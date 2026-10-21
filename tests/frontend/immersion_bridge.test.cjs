'use strict';
// Actual shipped ES module. Network gates are independent of action acceptance.
// Browser rendering, real WebGL and native input are verified separately.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/bridge.js'),'utf8');
const modulePromise=import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const copy=v=>JSON.parse(JSON.stringify(v));
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};};
const flush=()=>new Promise(setImmediate);
const snapshot=(cash=6)=>({mode:'game',save_version:4,capabilities:{navigation_revision:2},world:{minute:0,day:1,clock:'08:00',player:{id:'Player',name:'Aelia',x:800,y:415,cash,inventory:0,location:'street',path:[]},agents:[{id:'Felix',name:'Felix',role:'baker',x:810,y:250,location:'bakery',activity:'keeping the bread counter',private:{beliefs:'secret'}}],map:{width:1600,height:1100,locations:[]},nearby:[],objective:{title:'Six sacks'},story:{stage:'unresolved'},journal:[],operator:{facts:'secret'},counter_market:{active:true,operator:{minds:'secret'}}},branch:{operator:'secret'},removable_actions:['secret']});
const context=()=>({speaker:'Felix',greeting:{text:'I need flour.'},topics:[],choices:[],relationship:{reliability:.6},private:'secret'});
const proposal=()=>({proposal_id:'p0-1',interpretations:[{id:'0',label:'Buy two',action:{recipient:'Marcus',action:'buy',quantity:2}}],ai_receipt:'secret'});
async function harness() {
 const {KalendsBridge}=await modulePromise;
 const requests=[],states=[],status=[],timings=[],handlers=new Map();
 const fetchImpl=async(url,options)=>{const request={url,body:options.body?JSON.parse(options.body):undefined,options};requests.push(request);const value=await(handlers.get(url)?.(request)??snapshot());return {ok:true,status:200,json:async()=>copy(value)};};
 const bridge=new KalendsBridge({fetchImpl,onState:s=>states.push(s),onStatus:s=>status.push(s),onTiming:s=>timings.push(s)});
 return{bridge,requests,states,status,timings,handlers};
}

test('world/scene mapping preserves scale, axes and exact round trips',async()=>{
 const {toScene,toWorld,WORLD_SCALE,WORLD_ORIGIN,sameFloor}=await modulePromise;
 assert.equal(WORLD_SCALE,.02);assert.deepEqual(WORLD_ORIGIN,{x:800,y:415});
 assert.deepEqual(toScene({x:800,y:415}),{x:0,y:0,z:0});
 assert.deepEqual(toScene({x:850,y:465},.1),{x:1,y:.1,z:1});
 assert.deepEqual(toWorld(toScene({x:725,y:622})),{x:725,y:622});
 assert.equal(sameFloor('water','forum_access'),true);assert.equal(sameFloor('bakery','street'),false);
 assert.throws(()=>toScene({x:Infinity,y:2}),/finite/);
});

test('public entity projection never forwards operator or NPC private cognition',async()=>{
 const {projectSnapshot}=await modulePromise,payload=snapshot();
 const projected=projectSnapshot(payload);
 assert.equal(projected.world.player.cash,6);assert.equal(projected.world.agents[0].activity,'keeping the bread counter');
 assert.equal(JSON.stringify(projected).includes('secret'),false);
 projected.world.player.cash=999;assert.equal(payload.world.player.cash,6,'the rendering projection must be a separate object');
});

test('operator snapshots cannot enter the ordinary 3D entity graph',async()=>{
 const {projectSnapshot}=await modulePromise;
 assert.throws(()=>projectSnapshot({...snapshot(),mode:'lab'}),/public game snapshot/);
});

test('initial load returns a saved Lab session to public game mode before projection',async()=>{
 const h=await harness();h.handlers.set('/api/state',()=>({...snapshot(),mode:'lab'}));
 const result=await h.bridge.state();assert.equal(result.mode,'game');
 assert.deepEqual(h.requests.map(r=>r.url),['/api/state','/api/mode']);
 assert.deepEqual(h.requests[1].body,{mode:'game'});assert.equal(h.states.length,1);
});

test('duplicate in-flight confirmation submits exactly one economic action',async()=>{
 const h=await harness(),gate=deferred();h.handlers.set('/api/propose',proposal);h.handlers.set('/api/act',()=>gate.promise);
 await h.bridge.propose('Marcus',{choice_id:'buy'});
 const a=h.bridge.confirm('p0-1'),b=h.bridge.confirm('p0-1');assert.equal(a,b);
 await flush();assert.equal(h.requests.filter(r=>r.url==='/api/act').length,1);
 gate.resolve({...snapshot(2),receipt:{event_id:80,title:'Bought flour',private:'secret'},conversation:context()});
 const result=await a;assert.equal(result.world.player.cash,2);assert.equal(h.bridge.world.player.cash,2);
 assert.equal(JSON.stringify(result.receipt).includes('secret'),false);
 await assert.rejects(h.bridge.confirm('p0-1'),/situation changed/);
 assert.equal(h.requests.filter(r=>r.url==='/api/act').length,1);
});

test('confirmation sends only server-issued identifiers and never client resource values',async()=>{
 const h=await harness();h.handlers.set('/api/propose',proposal);
 await h.bridge.propose('Marcus',{text:'Buy 2 flour units'});await h.bridge.confirm('p0-1');
 assert.deepEqual(h.requests.find(r=>r.url==='/api/act').body,{proposal_id:'p0-1',interpretation_id:'0'});
 assert.equal(h.requests.find(r=>r.url==='/api/propose').body.text,'Buy 2 flour units');
});

test('a second world mutation is rejected rather than queued behind a stale intent',async()=>{
 const h=await harness(),gate=deferred();h.handlers.set('/api/move',()=>gate.promise);
 const first=h.bridge.move({x:826,y:415});await flush();
 await assert.rejects(h.bridge.advance(30),/previous action/);
 assert.equal(h.requests.length,1);assert.equal(h.bridge.pending,true);
 gate.resolve(snapshot());await first;assert.equal(h.bridge.pending,false);
 assert.equal(h.requests.filter(r=>r.url==='/api/advance').length,0);
});

test('a rejected move preserves the last accepted resources and releases busy state',async()=>{
 const h=await harness();await h.bridge.state();
 h.handlers.set('/api/move',()=>({error:'Choose a walkable point'}));
 await assert.rejects(h.bridge.move({x:10,y:10}),/walkable point/);
 assert.equal(h.bridge.world.player.cash,6);assert.equal(h.bridge.pending,false);
 h.handlers.set('/api/move',()=>snapshot(5));await h.bridge.move({x:826,y:415});
 assert.equal(h.bridge.world.player.cash,5);
});

test('a late context cannot reopen a conversation after moving',async()=>{
 const h=await harness(),gate=deferred();h.handlers.set('/api/context?recipient=Felix',()=>gate.promise);
 const reading=h.bridge.context('Felix');await h.bridge.move({x:826,y:415});gate.resolve(context());
 await assert.rejects(reading,/situation changed/);
});

test('a late state GET cannot overwrite a subsequently accepted transaction',async()=>{
 const h=await harness(),gate=deferred();h.handlers.set('/api/state',()=>gate.promise);h.handlers.set('/api/move',()=>snapshot(3));
 const reading=h.bridge.state();await h.bridge.move({x:826,y:415});gate.resolve(snapshot(6));
 await assert.rejects(reading,/situation changed/);assert.equal(h.bridge.world.player.cash,3);assert.equal(h.states.length,1);
});

test('closing a pending proposal makes the delayed response unusable',async()=>{
 const h=await harness(),gate=deferred();h.handlers.set('/api/propose',()=>gate.promise);
 const reading=h.bridge.propose('Felix',{choice_id:'inspect'});await flush();h.bridge.cancelConversation();gate.resolve(proposal());
 await assert.rejects(reading,/situation changed/);assert.equal(h.bridge.proposal,null);
 await assert.rejects(h.bridge.confirm('p0-1'),/situation changed/);assert.equal(h.requests.filter(r=>r.url==='/api/act').length,0);
});

test('movement body is a position intent, not client authority over resources',async()=>{
 const h=await harness();await h.bridge.move({x:826,y:415,cash:999,inventory:999});
 assert.deepEqual(h.requests[0].body,{x:826,y:415});assert.equal(h.bridge.world.player.cash,6);
});

test('route preview validates usable nodes and never changes accepted world state',async()=>{
 const h=await harness();await h.bridge.state();h.handlers.set('/api/route',()=>({points:[{x:800,y:415,location:'street'},{x:826,y:415,location:'street'}],destination:{x:826,y:415,location:'street'},private:'secret'}));
 const route=await h.bridge.route({x:826,y:415});assert.equal(route.points.length,2);assert.equal(h.states.length,1);assert.equal(route.private,undefined);
 h.handlers.set('/api/route',()=>({points:[{x:'bad',y:415,location:'street'}]}));await assert.rejects(h.bridge.route({x:826,y:415}),/finite/);
});

test('time advances only by an explicit bounded API call, never by rendering',async()=>{
 const h=await harness();for(const minutes of [0,-1,1.5,Infinity])await assert.rejects(h.bridge.advance(minutes),/positive whole/);
 assert.equal(h.requests.length,0);await h.bridge.advance(30);
 assert.deepEqual(h.requests[0].body,{minutes:30,mode:'compress'});
});

test('provider parser payloads stay scoped and failures are never automatically retried',async()=>{
 const h=await harness();h.handlers.set('/api/propose',()=>({error:'The provider timed out; use a choice'}));
 await assert.rejects(h.bridge.propose('Felix',{text:'What do you know?'}),/timed out/);
 assert.equal(h.requests.length,1);assert.equal(h.bridge.proposal,null);assert.equal(h.bridge.pending,false);
 assert.equal(h.timings.length,1);assert.equal(h.timings[0].ok,false);
});


test('default browser fetch retains its required global receiver',async()=>{
 const {KalendsBridge}=await modulePromise,original=globalThis.fetch;
 let called=0;
 globalThis.fetch=function(){assert.equal(this,globalThis,'Window.fetch cannot be invoked with the bridge as receiver');called++;return Promise.resolve({ok:true,status:200,json:async()=>snapshot()});};
 try {const bridge=new KalendsBridge();await bridge.state();assert.equal(called,1);assert.equal(bridge.world.player.cash,6);}
 finally {globalThis.fetch=original;}
});


test('a legacy World Lab view cannot leak through a later accepted 3D mutation',async()=>{
 const h=await harness();await h.bridge.state();
 h.handlers.set('/api/move',()=>({...snapshot(4),mode:'lab'}));
 h.handlers.set('/api/mode',()=>snapshot(4));
 const result=await h.bridge.move({x:826,y:415});
 assert.equal(result.mode,'game');assert.equal(result.world.player.cash,4);
 assert.equal(h.requests.filter(r=>r.url==='/api/move').length,1);
 assert.deepEqual(h.requests.at(-1).body,{mode:'game'});
 assert.equal(h.states.length,2);assert.equal(JSON.stringify(h.states).includes('secret'),false);
});
