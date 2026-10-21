'use strict';
// Execute shipped renderer methods with independently controlled authoritative
// location and displayed scene/position. No GPU, native input or pixel claim.
const test=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const modulePromise=import(pathToFileURL(path.resolve(__dirname,'../../kalends_3d/src/renderer.js')).href);

async function proximity({playerLocation='street',playerScene='street',playerPosition={x:810,y:350},npcLocation='street',npcScene='bakery',npcPosition={x:810,y:229.5},nearby=['Felix']}={}){
  const {DistrictRenderer}=await modulePromise;
  const renderer=Object.create(DistrictRenderer.prototype);
  renderer.currentScene=playerScene;
  renderer.snapshot={world:{nearby,map:{locations:[{id:'bakery',x:650,y:80,w:320,h:230,door:{x:810,y:350},interior:true}]}}};
  renderer.actors=new Map([
    ['Player',{id:'Player',location:playerLocation,scene:playerScene,position:playerPosition}],
    ['Felix',{id:'Felix',location:npcLocation,scene:npcScene,position:npcPosition}],
  ]);
  return renderer;
}

test('an NPC future street endpoint cannot authorize talk while its displayed body remains inside',async()=>{
  const r=await proximity();
  assert.equal(r.displayedNear('Felix'),false,
    'authority says street, but the baker is still visibly inside the bakery');
});

test('an NPC future room endpoint cannot authorize talk from the displayed street side',async()=>{
  const r=await proximity({playerLocation:'bakery',playerScene:'bakery',playerPosition:{x:810,y:275.5},npcLocation:'bakery',npcScene:'street',npcPosition:{x:810,y:340}});
  assert.equal(r.displayedNear('Felix'),false,
    'a near authoritative endpoint cannot replace crossing the rendered portal');
});

test('matching displayed room, authoritative floor and real proximity allow interaction',async()=>{
  const r=await proximity({playerLocation:'bakery',playerScene:'bakery',playerPosition:{x:810,y:275.5},npcLocation:'bakery',npcScene:'bakery'});
  assert.equal(r.displayedNear('Felix'),true);
});

test('displayed proximity still cannot bypass the server nearby authorization',async()=>{
  const r=await proximity({playerLocation:'bakery',playerScene:'bakery',playerPosition:{x:810,y:275.5},npcLocation:'bakery',npcScene:'bakery',nearby:[]});
  assert.equal(r.displayedNear('Felix'),false);
});

test('public landmark aliases share one displayed street floor without granting cross-room access',async()=>{
  const r=await proximity({playerLocation:'water',playerPosition:{x:510,y:415},npcLocation:'forum_access',npcScene:'street',npcPosition:{x:550,y:415}});
  assert.equal(r.displayedNear('Felix'),true);
});

test('rendered exit waits for the outgoing actor to reach the public doorway',async()=>{
  const r=await proximity(),a=r.actors.get('Felix');a.path=[{x:810,y:350}];
  r.updateScene(a);assert.equal(a.scene,'bakery');
  a.position={x:810,y:315};r.updateScene(a);assert.equal(a.scene,'bakery','a room threshold is not yet the public doorway');
  a.position={x:810,y:331};r.updateScene(a);assert.equal(a.scene,'street');
});

test('rendered entrance waits for the incoming actor to cross into the room floor',async()=>{
  const r=await proximity({npcLocation:'bakery',npcScene:'street',npcPosition:{x:810,y:330}}),a=r.actors.get('Felix');a.path=[{x:810,y:275.5}];
  r.updateScene(a);assert.equal(a.scene,'street');
  a.position={x:810,y:294};r.updateScene(a);assert.equal(a.scene,'bakery');
});

test('room-to-room authority still renders the intervening street, rather than jumping scene',async()=>{
  const r=await proximity();r.snapshot.world.map.locations.push({id:'fullery',x:220,y:500,w:330,h:240,door:{x:385,y:480},interior:true});
  const a=r.actors.get('Felix');Object.assign(a,{scene:'fullery',location:'bakery',position:{x:385,y:656},path:[{x:385,y:480},{x:810,y:350},{x:810,y:275.5}]});
  r.updateScene(a);assert.equal(a.scene,'fullery');
  a.position={x:385,y:480};r.updateScene(a);assert.equal(a.scene,'street');
  a.position={x:810,y:294};r.updateScene(a);assert.equal(a.scene,'bakery');
});

test('screen picking cannot select an NPC behind its former room while authority is already on the street',async()=>{
  const r=await proximity();r.canvas={getBoundingClientRect:()=>({left:0,top:0})};
  r.camera={camera:{nearClip:.1,farClip:90,worldToScreen:()=>({x:100,y:100,z:1}),screenToWorld:(x,y,depth)=>({x:0,y:depth<1?3:-3,z:1})}};
  r.actors.get('Felix').entity={getPosition:()=>({x:.2,y:0,z:-3.71})};
  assert.equal(r.pick(100,100).kind,'ground');
  r.actors.get('Felix').scene='street';assert.deepEqual(r.pick(100,100),{kind:'person',id:'Felix'});
});

async function cameraHarness(){
  const r=await proximity({playerPosition:{x:800,y:415},npcScene:'street',npcPosition:{x:800,y:415}});
  r.cameraYaw=24;r.cameraDistance=13.5;r.cameraFocus={x:0,y:.7,z:0};r.follow=false;r.reduced=false;r.selected=null;
  r.camera={setPosition:(x,y,z)=>{r.lastCamera={x,y,z};},lookAt:()=>{}};
  r.actors.get('Felix').entity={getPosition:()=>({x:0,y:0,z:0})};
  return r;
}

test('conversation camera zoom blends over frames instead of an immediate eighteen-percent jump',async()=>{
  const r=await cameraHarness();r.updateCamera(1/60);assert.equal(r.cameraEffectiveDistance,13.5);
  r.selected='Felix';r.updateCamera(1/60);
  assert.ok(r.cameraEffectiveDistance>13.2&&r.cameraEffectiveDistance<13.5,'first frame must move only partway toward 11.07m');
  for(let i=0;i<60;i++)r.updateCamera(1/60);
  assert.ok(Math.abs(r.cameraEffectiveDistance-13.5*.82)<.05);
  const previous=r.cameraEffectiveDistance;r.selected=null;r.updateCamera(1/60);
  assert.ok(r.cameraEffectiveDistance>previous&&r.cameraEffectiveDistance-previous<.3,'leaving conversation must also blend');
});

test('reduced motion may select the conversation camera distance immediately',async()=>{
  const r=await cameraHarness();r.reduced=true;r.selected='Felix';r.updateCamera(1/60);
  assert.equal(r.cameraEffectiveDistance,13.5*.82);
});
