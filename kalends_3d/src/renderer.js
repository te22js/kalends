import * as pc from 'playcanvas';
import {toScene,toWorld,sameFloor,WORLD_SCALE,worldDistance} from '../bridge.js';
import {sceneActivity} from './scene_guide.js';
const setAt=(entity,point)=>{const p=toScene(point);entity.setPosition(p.x,p.y,p.z);};
const A='/immersion-assets/';
const lerpAngle=(a,b,t)=>a+(((b-a+540)%360)-180)*t;

export class DistrictRenderer {
  constructor(canvas,{trace,onProgress=()=>{},onTarget=()=>{},onFrame=()=>{},onPresented=()=>{},onError=()=>{}}={}){
    this.canvas=canvas;this.trace=trace;this.onProgress=onProgress;this.onTarget=onTarget;this.onFrame=onFrame;this.onPresented=onPresented;this.onError=onError;
    this.actors=new Map();this.assetCache=new Map();this.snapshot=null;this.currentScene='street';this.cameraYaw=24;this.cameraDistance=13.5;this.cameraFocus=new pc.Vec3(-3,0,0);this.follow=true;this.running=false;this.reduced=false;this.selected=null;this.marker=null;this.frameStarted=0;this.playerMoved=false;this.seenMove=null;
    this.app=new pc.Application(canvas,{graphicsDeviceOptions:{antialias:true,alpha:false,powerPreference:'high-performance'}});
    this.app.setCanvasFillMode(pc.FILLMODE_FILL_WINDOW);this.app.setCanvasResolution(pc.RESOLUTION_AUTO);
    this.app.graphicsDevice.maxPixelRatio=Math.min(devicePixelRatio,1.5);
    this.app.scene.ambientLight=new pc.Color(.55,.51,.44);this.app.scene.exposure=1.05;
    this.camera=new pc.Entity('District camera');this.camera.addComponent('camera',{clearColor:new pc.Color(.61,.66,.64),nearClip:.1,farClip:90,fov:45});this.app.root.addChild(this.camera);
    this.sun=new pc.Entity('Mediterranean sun');this.sun.addComponent('light',{type:'directional',color:new pc.Color(1,.89,.7),intensity:2.15,castShadows:true,shadowType:pc.SHADOW_PCF3,shadowResolution:2048,shadowDistance:50,normalOffsetBias:.04,shadowBias:.15,numCascades:2});this.sun.setEulerAngles(48,-28,0);this.app.root.addChild(this.sun);
    const fill=new pc.Entity('Sky fill');fill.addComponent('light',{type:'directional',color:new pc.Color(.65,.76,.85),intensity:.45,castShadows:false});fill.setEulerAngles(38,140,0);this.app.root.addChild(fill);
    this.frame=new pc.CameraFrame(this.app,this.camera.camera);this.frame.rendering.toneMapping=pc.TONEMAP_ACES;this.frame.rendering.samples=2;this.frame.ssao.type=pc.SSAOTYPE_NONE;this.frame.grading.enabled=true;this.frame.grading.tint.set(1,.98,.94);this.frame.grading.saturation=.94;this.frame.grading.contrast=1.025;this.frame.vignette.intensity=.2;this.frame.vignette.inner=.45;this.frame.vignette.outer=1.25;this.frame.bloom.intensity=.025;this.frame.bloom.threshold=1.4;
    this.app.on('update',dt=>{this.frameStarted=performance.now();this.update(Math.min(dt,.05));});
    this.app.on('frameend',()=>{const presenting=!document.hidden&&this.app.autoRender;if(presenting)this.onPresented();if(this.playerMoved&&presenting)this.trace?.changedDraw();this.trace?.frame(performance.now(),performance.now()-this.frameStarted,presenting);this.playerMoved=false;});
    this.resize=()=>this.app.resizeCanvas();window.addEventListener('resize',this.resize);this.app.start();this.setQuality('balanced');
  }
  async loadAsset(file){if(!this.assetCache.has(file)){this.assetCache.set(file,new Promise((resolve,reject)=>{const at=performance.now();this.app.assets.loadFromUrl(A+file,'container',(error,asset)=>{this.trace?.record('asset_load',{file,duration_ms:performance.now()-at,ok:!error});error?reject(new Error('Could not load '+file+': '+error)):resolve(asset);});}));}return this.assetCache.get(file);}
  async load(snapshot){
    this.onProgress(10,'Opening the district…');
    const manifestResponse=await fetch(A+'characters/characters.json');if(!manifestResponse.ok)throw Error('Character manifest is missing.');this.characterManifest=await manifestResponse.json();
    const environment=await this.loadAsset('environment/pompeii_district.glb');this.environment=environment.resource.instantiateRenderEntity({castShadows:true,receiveShadows:true});this.app.root.addChild(this.environment);
    this.onProgress(45,'Preparing the people of Pompeii…');
    this.roofs=new Map(['bakery','fullery','thermopolium','household'].map(id=>[id,this.environment.findByName(id+'_roof')]));
    this.walls=new Map(['bakery','fullery','thermopolium','household'].map(id=>[id,{full:this.environment.findByName(id+'_walls'),cutaway:this.environment.findByName(id+'_cutaway_walls')}]));for(const wall of this.walls.values())if(wall.cutaway)wall.cutaway.enabled=false;
    await Promise.all([snapshot.world.player,...snapshot.world.agents].map(a=>this.addActor(a)));
    this.apply(snapshot,true);this.createDoorLabels(snapshot.world.map.locations);this.createMarker();this.updateCamera(1);this.onProgress(95,'The district is ready.');
  }
  async addActor(data){
    const variant=this.characterManifest.variants[data.id];if(!variant)throw Error('No character asset for '+data.id);
    const asset=await this.loadAsset(variant.file),model=asset.resource.instantiateRenderEntity({castShadows:true,receiveShadows:true});model.setLocalScale(variant.scale,variant.scale,variant.scale);model.setLocalEulerAngles(0,variant.yaw||0,0);
    const entity=new pc.Entity(data.id);entity.addChild(model);this.app.root.addChild(entity);
    model.addComponent('anim',{activate:true});const clips=variant.clips||this.characterManifest.clips;
    const states=[{name:'START'},{name:'END'},...Object.keys(clips).map(name=>({name,speed:1,loop:true}))];
    model.anim.loadStateGraph({layers:[{name:'Base',weight:1,states,transitions:[{from:'START',to:'idle',time:0}]}],parameters:{}});
    const available={};for(const animation of asset.resource.animations||[]){available[animation.resource.name]=animation.resource;available[animation.name]=animation.resource;}
    for(const [role,name]of Object.entries(clips)){const animation=available[name]||Object.values(available).find(a=>a.name===name);if(!animation)throw Error('Animation '+name+' missing for '+data.id);model.anim.assignAnimation(role,animation);}
    const name=document.createElement(data.id==='Player'?'div':'button');name.className='nameplate';if(data.id!=='Player'){name.dataset.approach=data.id;name.setAttribute('aria-label','Approach '+data.id);}name.innerHTML='<span></span><small></small>';name.querySelector('span').textContent=data.id==='Player'?'Aelia · you':data.name||data.id;document.querySelector('#names').append(name);
    const actor={id:data.id,data,entity,model,position:{x:data.x,y:data.y},target:{x:data.x,y:data.y},path:[],location:data.location,scene:['street','water','forum_access'].includes(data.location)?'street':data.location,yaw:180,state:'idle',label:name,lastEvent:null,gestureUntil:0};this.actors.set(data.id,actor);setAt(entity,data);
    // Recolor only a modest material accent. The original mesh/skin/weights and
    // professional authored clips remain, with a local per-instance material.
    const tint=new pc.Color().fromString(variant.tint||'#b8a48a');for(const render of model.findComponents('render'))for(const mesh of render.meshInstances){const original=mesh.material,accent=original.name==='KALENDS_Skin'?variant.skinTint:original.name==='KALENDS_Cloth'?variant.clothTint:original.name==='KALENDS_Cloth_Trim'?variant.beltTint:null;if(accent||original.name?.match(/cloth|outfit|body/i)){const material=original.clone();if(accent)material.diffuse.fromString(accent);else material.diffuse.lerp(material.diffuse,tint,.3);material.update();mesh.material=material;}}
    this.trace?.record('actor_ready',{id:data.id,clips:Object.keys(clips),skin:true});
  }
  apply(snapshot,snap=false){
    const old=this.snapshot?.world;this.snapshot=snapshot;const w=snapshot.world;const jump=old&&Math.abs(w.minute-old.minute)>120;
    for(const data of [w.player,...w.agents]){const a=this.actors.get(data.id);if(!a)continue;const changed=a.target.x!==data.x||a.target.y!==data.y||a.location!==data.location;a.data=data;
      if(changed){const points=(data.path||[]).map(p=>Array.isArray(p)?{x:p[0],y:p[1]}:{x:p.x,y:p.y});a.path=points.filter(q=>worldDistance(q,a.position)>.05);if(!a.path.length||worldDistance(a.path.at(-1),data)>.05)a.path.push({x:data.x,y:data.y});a.target={x:data.x,y:data.y};a.location=data.location;}
      if(snap||jump){a.position={x:data.x,y:data.y};a.scene=['street','water','forum_access'].includes(data.location)?'street':data.location;a.path=[];setAt(a.entity,data);}
    }
    const cargo=this.environment?.findByName('market_cart_cargo');if(cargo)cargo.enabled=['unresolved','committed'].includes(w.story?.stage);
    const h=(8+Math.floor(w.minute/60))%24;const daylight=h>=6&&h<19;this.sun.light.intensity=daylight?2.15:.45;this.app.scene.ambientLight=daylight?new pc.Color(.55,.51,.44):new pc.Color(.2,.25,.32);this.frame.grading.tint.set(1,daylight?.98:.96,daylight?.94:1);
    if(jump)this.trace?.record('time_jump',{minutes:w.minute-old.minute});
  }
  get player(){return this.actors.get('Player');}
  remaining(){const a=this.player;if(!a)return 0;let total=0,from=a.position;for(const p of a.path){total+=worldDistance(from,p);from=p;}return total;}
  displayedNear(id){const a=this.actors.get(id),p=this.player;if(!a||!p)return false;return sameFloor(a.scene,p.scene)&&sameFloor(a.scene,this.currentScene)&&this.snapshot.world.nearby.includes(id)&&worldDistance(a.position,p.position)<=155;}
  visibleActor(id){const a=this.actors.get(id);if(!a||!this.player||!sameFloor(a.scene,this.currentScene)||worldDistance(a.position,this.player.position)>420)return false;const p=a.entity.getPosition(),q=this.camera.camera.worldToScreen(new pc.Vec3(p.x,1.2,p.z));return q.z>0&&q.x>=0&&q.y>=0&&q.x<=this.canvas.clientWidth&&q.y<=this.canvas.clientHeight;}
  setAnimation(a,state){if(a.state===state)return;try{a.model.anim.baseLayer.transition(state,this.reduced?.05:.17);a.state=state;}catch(error){this.onError(error);}}
  update(dt){
    if(!this.snapshot)return;const p=this.player;
    for(const a of this.actors.values()){
      let dx=0,dy=0;const before={...a.position};let remaining=dt*(a.id==='Player'?(this.running?185:115):100);
      while(a.path.length&&remaining>0){const q=a.path[0],distance=worldDistance(a.position,q);if(distance<=remaining){a.position={...q};a.path.shift();remaining-=distance;}else{a.position.x+=(q.x-a.position.x)/distance*remaining;a.position.y+=(q.y-a.position.y)/distance*remaining;remaining=0;}}
      dx=a.position.x-before.x;dy=a.position.y-before.y;const moving=Math.hypot(dx,dy)>1e-8;
      if(moving){a.yaw=lerpAngle(a.yaw,Math.atan2(dx,dy)*180/Math.PI,1-Math.exp(-dt*15));if(a.id==='Player')this.playerMoved=true;}
      else if(this.selected&&(a.id==='Player'||a.id===this.selected)){const other=a.id==='Player'?this.actors.get(this.selected):p;if(other)a.yaw=lerpAngle(a.yaw,Math.atan2(other.position.x-a.position.x,other.position.y-a.position.y)*180/Math.PI,1-Math.exp(-dt*10));}
      this.updateScene(a);setAt(a.entity,a.position);a.entity.setEulerAngles(0,a.yaw,0);
      const talking=this.selected===a.id||this.selected&&a.id==='Player';const working=a.id!=='Player'&&/working|baking|serving|keeping the bread|attending to household/.test(a.data.activity||'');
      const state=moving?(this.running&&a.id==='Player'?'run':'walk'):this.reduced?'idle':performance.now()<a.gestureUntil?'celebrate':talking?'talk':working?'work':'idle';this.setAnimation(a,state);
      a.model.anim.speed=moving?(state==='run'?1:.95):this.reduced?0:1;
    }
    // A room is shown only when the interpolated actor reaches its physical
    // threshold. The server may already have accepted the next short segment.
    if(p){this.currentScene=p.scene;const sign=this.environment?.findByName('bakery_frontage_sign');if(sign)sign.enabled=this.currentScene!=='bakery';for(const [id,roof]of this.roofs)if(roof)roof.enabled=id!==this.currentScene;for(const [id,wall]of this.walls||[]){if(wall.full)wall.full.enabled=id!==this.currentScene;if(wall.cutaway)wall.cutaway.enabled=id===this.currentScene;}this.updateCamera(dt);}
    for(const a of this.actors.values()){const q=this.camera.camera.worldToScreen(new pc.Vec3(a.entity.getPosition().x,1.95,a.entity.getPosition().z));const show=(a.id==='Player'||this.visibleActor(a.id)||this.selected===a.id)&&q.z>0&&q.x>-20&&q.x<this.canvas.clientWidth+20&&q.y>-20&&q.y<this.canvas.clientHeight+20;a.label.classList.toggle('hidden',!show);a.label.style.left=q.x+'px';a.label.style.top=q.y+'px';const near=this.displayedNear(a.id),activity=sceneActivity(a.data,{moving:a.path.length>0,talking:this.selected===a.id});a.label.querySelector('small').textContent=a.id==='Player'?'':activity+(near?' · E to talk':' · approach to speak');if(a.id!=='Player')a.label.setAttribute('aria-label',a.id+', '+activity+'. '+(near?'Talk':'Approach to speak'));}
    for(const door of this.doorLabels||[]){const active=this.currentScene===door.location.id||this.currentScene==='street',q=this.camera.camera.worldToScreen(new pc.Vec3(...Object.values(toScene(door.location.door,1.1)))),close=this.player&&worldDistance(this.player.position,door.location.door)<220;door.element.hidden=!active||!close||q.z<=0;door.element.style.left=q.x+'px';door.element.style.top=q.y+'px';door.element.dataset.visit=this.currentScene===door.location.id?'street':door.location.id;door.element.textContent=this.currentScene===door.location.id?'To the street ↗':door.location.kind==='bakery'?'Felix’s bakery ↗':door.location.name+' ↗';}
    const left=this.environment?.findByName('bakery_shutter_left'),right=this.environment?.findByName('bakery_shutter_right');if(left&&right&&this.player){const open=worldDistance(this.player.position,{x:810,y:310})<145;this.doorAngle=(this.doorAngle||0)+((open?15:0)-(this.doorAngle||0))*(this.reduced?1:1-Math.exp(-dt*4));left.setLocalEulerAngles(0,this.doorAngle,0);right.setLocalEulerAngles(0,-this.doorAngle,0);}
    if(this.marker){this.marker.enabled=performance.now()<this.markerUntil;this.marker.setLocalScale(1,1,1);}
    this.onFrame();
  }
  updateScene(actor){const rooms=this.snapshot.world.map.locations.filter(q=>q.interior),current=rooms.find(q=>q.id===actor.scene),target=rooms.find(q=>q.id===actor.location);if(current&&actor.location!==current.id&&(worldDistance(actor.position,current.door)<20||!actor.path.length))actor.scene='street';if(target&&actor.scene!==target.id&&actor.position.x>=target.x+12&&actor.position.x<=target.x+target.w-12&&actor.position.y>=target.y+12&&actor.position.y<=target.y+target.h-12)actor.scene=target.id;}
  updateCamera(dt){if(!this.player)return;const p=toScene(this.player.position),target=new pc.Vec3(p.x,.7,p.z);if(this.selected){const other=this.actors.get(this.selected);if(other){const q=other.entity.getPosition();target.x=(target.x+q.x)*.5;target.z=(target.z+q.z)*.5;}if(this.conversationCamera?.id!==this.selected)this.conversationCamera={id:this.selected,x:target.x,y:target.y,z:target.z};target.set(this.conversationCamera.x,this.conversationCamera.y,this.conversationCamera.z);}else this.conversationCamera=null;
    if(this.follow)this.cameraFocus.lerp(this.cameraFocus,target,this.reduced?1:1-Math.exp(-dt*5));
    const yaw=this.cameraYaw*Math.PI/180,desiredDistance=this.cameraDistance*(this.selected?.82:1);this.cameraEffectiveDistance??=this.cameraDistance;this.cameraEffectiveDistance+=(desiredDistance-this.cameraEffectiveDistance)*(this.reduced?1:1-Math.exp(-dt*4));const distance=this.cameraEffectiveDistance;this.camera.setPosition(this.cameraFocus.x+Math.sin(yaw)*distance*.65,this.cameraFocus.y+distance*.72,this.cameraFocus.z+Math.cos(yaw)*distance*.65);this.camera.lookAt(this.cameraFocus);}
  createDoorLabels(locations){this.doorLabels=locations.filter(q=>q.interior).map(location=>{const element=document.createElement('button');element.className='doorplate';element.setAttribute('aria-label','Walk to '+location.name);document.querySelector('#names').append(element);return{location,element};});}
  createMarker(){this.marker=new pc.Entity('Chosen destination');const mat=new pc.StandardMaterial();mat.diffuse=new pc.Color(1,.82,.42);mat.emissive=new pc.Color(.3,.16,.025);mat.opacity=.7;mat.blendType=pc.BLEND_NORMAL;mat.useLighting=false;mat.update();const segments=48,positions=[],indices=[];for(let i=0;i<segments;i++){const t=i/segments*Math.PI*2;for(const r of [.2,.25])positions.push(Math.cos(t)*r,.025,Math.sin(t)*r);const j=i*2,k=(i*2+2)%(segments*2);indices.push(j,k,j+1,j+1,k,k+1);}const mesh=new pc.Mesh(this.app.graphicsDevice);mesh.setPositions(positions);mesh.setIndices(indices);mesh.update(pc.PRIMITIVE_TRIANGLES);this.marker.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,mat,this.marker)]});this.app.root.addChild(this.marker);this.marker.enabled=false;}
  showTarget(q,duration=1600){const v=toScene(q);this.marker.setPosition(v.x,v.y,v.z);this.markerUntil=performance.now()+duration;}
  pick(x,y){const viewport=this.canvas.getBoundingClientRect();const sx=x-viewport.left,sy=y-viewport.top;let nearest=null,min=35;for(const a of this.actors.values()){if(a.id==='Player')continue;if(!sameFloor(a.scene,this.currentScene))continue;const pos=a.entity.getPosition(),q=this.camera.camera.worldToScreen(new pc.Vec3(pos.x,1,pos.z));if(q.z<=0)continue;const d=Math.hypot(q.x-sx,q.y-sy);if(d<min){min=d;nearest=a.id;}}
    if(nearest)return{kind:'person',id:nearest};
    const near=this.camera.camera.screenToWorld(sx,sy,this.camera.camera.nearClip),far=this.camera.camera.screenToWorld(sx,sy,this.camera.camera.farClip),dir=new pc.Vec3().sub2(far,near);if(Math.abs(dir.y)<1e-6)return null;const t=-near.y/dir.y;if(t<0)return null;const hit=new pc.Vec3().copy(near).add(dir.mulScalar(t));return{kind:'ground',...toWorld(hit)};
  }
  screenPoint(q,height=0){return this.camera.camera.worldToScreen(new pc.Vec3(...Object.values(toScene(q,height))));}
  setQuality(quality){this.quality=quality;const high=quality==='high',low=quality==='low';this.app.graphicsDevice.maxPixelRatio=low?1:Math.min(devicePixelRatio,1.5);this.frame.rendering.renderTargetScale=low?.75:1;this.frame.rendering.samples=low?1:2;this.frame.ssao.type=high?pc.SSAOTYPE_COMBINE:pc.SSAOTYPE_NONE;this.frame.ssao.radius=1.2;this.frame.ssao.samples=8;this.frame.ssao.intensity=.35;this.frame.ssao.power=1.6;this.sun.light.castShadows=!low;this.sun.light.shadowResolution=high?2048:1024;this.frame.update();this.app.resizeCanvas();}
  diagnostics(){const d=this.app.graphicsDevice,gl=d.gl,ext=gl?.getExtension('WEBGL_debug_renderer_info');return{gpu_renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'unavailable',engine:'PlayCanvas '+pc.version,device_type:d.deviceType,user_agent:navigator.userAgent,hardware_concurrency:navigator.hardwareConcurrency,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,render_width:this.canvas.width,render_height:this.canvas.height},quality:this.quality,scene_resolution_scale:this.frame.rendering.renderTargetScale,msaa_samples:this.frame.rendering.samples,actors:this.actors.size,draw_calls:this.app.stats.drawCalls.total,triangles:this.app.stats.frame.triangles,textures_bytes:this.app.stats.vram.tex,scope:'Browser-reported hardware and engine counters; not GPU elapsed time or physical-device qualification.'};}
}
