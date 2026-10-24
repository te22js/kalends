'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/product_host.js'),'utf8');
const modulePromise=import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve};};
async function harness(options={}){
 const {installProductHost}=await modulePromise,events=new Map(),messages=[],calls=[];
 const parent={postMessage(payload,origin){assert.equal(this,parent);messages.push({payload,origin});}};
 const timers=new Map();let serial=0;
 const host={parent,location:{href:'http://127.0.0.1:8801/immersion/?experience=life_a',origin:'http://127.0.0.1:8801'},
 setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),
 addEventListener:(type,fn)=>events.set(type,fn),removeEventListener:(type,fn)=>{if(events.get(type)===fn)events.delete(type);}};
 const view={cameraYaw:41,cameraDistance:18,follow:false,recipient:'Felix',draftRecipient:'Felix',draft:'An unsent question',tab:'people',started:true,journalOpen:false};
 const controller=installProductHost({windowObject:host,capture:()=>view,pause:()=>calls.push('pause'),refresh:async()=>calls.push('refresh'),restore:async value=>calls.push(['restore',value]),...options});
 const request=(action,extra={},event={})=>events.get('message')?.({origin:host.location.origin,source:parent,data:{kind:'kalends:host',life_id:'life_a',request_id:'request-1',action,...extra},...event});
 return{host,parent,messages,calls,view,controller,request,events,timers};
}
test('same-origin parent captures local camera and draft without a world call',async()=>{
 const h=await harness();await h.request('capture');assert.deepEqual(h.calls,[]);
 assert.equal(h.messages[0].payload.view.draft,'An unsent question');assert.equal(h.messages[0].payload.view.cameraYaw,41);
 assert.equal(h.messages[0].payload.life_id,'life_a');assert.equal(h.messages[0].origin,h.host.location.origin);
});
test('wrong origin, source, life, unknown action and invalid IDs never reach callbacks',async()=>{
 const h=await harness();await h.request('pause',{}, {origin:'https://untrusted.example'});await h.request('pause',{}, {source:{}});
 await h.request('pause',{life_id:'life_b'});await h.request('act');await h.request('pause',{request_id:''});
 assert.deepEqual(h.calls,[]);assert.deepEqual(h.messages,[]);
});
test('pause preserves unsent speech and acknowledges with captured local view',async()=>{
 const h=await harness();await h.request('pause');assert.deepEqual(h.calls,['pause']);
 assert.equal(h.messages[0].payload.status,'ok');assert.equal(h.messages[0].payload.view.recipient,'Felix');
 assert.equal(h.messages[0].payload.view.draft,'An unsent question');
});
test('refresh returns pending during an accepted write and never initiates a second operation',async()=>{
 const h=await harness({pending:()=>true});await h.request('refresh');await h.request('restore',{view:{}});
 assert.deepEqual(h.calls,[]);assert.ok(h.messages.every(m=>m.payload.status==='pending'));
});
test('concurrent host refreshes serialize and do not replay a mutation',async()=>{
 const gate=deferred();let reads=0;const h=await harness({refresh:async()=>{reads++;await gate.promise;}});
 const first=h.request('refresh');await h.request('refresh',{request_id:'second'});assert.equal(reads,1);
 assert.equal(h.messages[0].payload.status,'pending');gate.resolve();await first;
 assert.equal(h.messages[1].payload.status,'ok');
});
test('restore clamps camera and whitelists local fields; action proposals are discarded',async()=>{
 const h=await harness();await h.request('restore',{view:{cameraYaw:999,cameraDistance:-1,follow:false,recipient:'Felix',draft:'x'.repeat(1000),tab:'operator',started:true,action:'buy',proposal_id:'secret'}});
 const restored=h.calls[0][1];assert.equal(restored.cameraYaw,55);assert.equal(restored.cameraDistance,7);
 assert.equal(restored.draft.length,600);assert.equal(restored.tab,'story');assert.equal(restored.started,true);
 assert.equal('proposal_id' in restored,false);assert.equal('action' in restored,false);
});
test('boot readiness is life scoped and transient errors do not expose details',async()=>{
 const h=await harness({refresh:async()=>{throw Error('PRIVATE REPORT: fragile');}});h.controller.notifyReady();
 assert.equal(h.messages[0].payload.status,'ready');assert.equal(h.messages[0].payload.life_id,'life_a');
 await h.request('refresh');assert.equal(h.messages[1].payload.status,'error');assert.doesNotMatch(h.messages[1].payload.error,/PRIVATE|fragile/);
 h.controller.destroy();assert.equal(h.events.has('message'),false);
});
test('top-level 3D client installs no host bridge and keeps its ordinary behavior',async()=>{
 const {installProductHost}=await modulePromise;let installed=0;const host={addEventListener:()=>installed++};host.parent=host;
 const bridge=installProductHost({windowObject:host});bridge.notifyReady();bridge.destroy();assert.equal(installed,0);
});

function appHarness(){
 const vm=require('node:vm'),main=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=main.indexOf('function sceneVisibility('),end=main.indexOf('async function boot(',begin);
 const elements={'#speech':{value:'Keep this draft',focus(){}},'#journal':{open:false},'#loading':{hidden:true}};
 const calls=[],S={ready:true,hostPaused:false,started:true,selected:'Felix',speechRecipient:'Felix',tab:'people',conversationEpoch:1,
  renderer:{cameraYaw:41,cameraDistance:18,follow:false,app:{autoRender:true},displayedNear:id=>id==='Felix'}};
 const bridge={pending:false,state:async()=>calls.push('state'),context:async id=>{calls.push(['context',id]);return{speaker:id};}};
 const sandbox={S,bridge,document:{activeElement:{id:'speech'},addEventListener(){}},$:key=>elements[key],canvas:{focus:()=>calls.push('focus')},
  setLive:value=>calls.push(['live',value]),cancelWalk:reason=>calls.push(['cancel',reason]),renderContext:()=>{},renderConversation:()=>calls.push('renderConversation'),
  closeConversation:()=>{calls.push('close');S.selected=null;},person:id=>['Felix','Sabina'].includes(id)?{id}:null,
  openConversation:async id=>{calls.push(['open',id]);S.selected=id;},openDialog:id=>calls.push(['dialog',id]),installProductHost:callbacks=>({...callbacks,notifyView(){}})};
 vm.createContext(sandbox);vm.runInContext(main.slice(begin,end)+'\nglobalThis.callbacks=productHost;',sandbox);
 return{callbacks:sandbox.callbacks,S,elements,calls};
}
test('actual scene glue pauses rendering while preserving the conversation, camera and unsent draft',()=>{
 const h=appHarness();h.callbacks.pause();assert.equal(h.S.hostPaused,true);assert.equal(h.S.renderer.app.autoRender,false);
 assert.equal(h.S.selected,'Felix');assert.equal(h.elements['#speech'].value,'Keep this draft');assert.equal(h.S.renderer.cameraYaw,41);
 assert.equal(h.calls.some(call=>call==='close'||call==='state'),false);
});
test('actual scene glue reconciles only reads and keeps camera, selected person and draft',async()=>{
 const h=appHarness();h.callbacks.pause();await h.callbacks.refresh();assert.equal(h.S.renderer.app.autoRender,true);
 assert.equal(h.S.selected,'Felix');assert.equal(h.elements['#speech'].value,'Keep this draft');assert.equal(h.S.renderer.cameraYaw,41);
 assert.ok(h.calls.includes('state'));assert.ok(h.calls.some(call=>Array.isArray(call)&&call[0]==='context'&&call[1]==='Felix'));
 assert.equal(h.calls.includes('close'),false);
});
test('actual reload restore reopens only a supported nearby person and restores the draft',async()=>{
 const {sceneView}=await modulePromise,h=appHarness();h.S.selected=null;
 await h.callbacks.restore(sceneView({started:true,recipient:'Sabina',draftRecipient:'Sabina',draft:'For Sabina',cameraYaw:40}));
 assert.equal(h.S.selected,null,'a currently distant recipient is never approached automatically');
 assert.equal(h.elements['#speech'].value,'For Sabina');assert.equal(h.S.speechRecipient,'Sabina');
 await h.callbacks.restore(sceneView({started:true,recipient:'Felix',draftRecipient:'Felix',draft:'For Felix',cameraYaw:50}));
 assert.equal(h.S.selected,'Felix');assert.equal(h.elements['#speech'].value,'For Felix');assert.equal(h.S.renderer.cameraYaw,50);
 assert.equal(h.calls.includes('state'),false,'local restore has no world operation');
});
test('an immediate draft update notifies only the parent with a bounded local view',async()=>{
 const h=await harness();h.view.draft='The latest unsent words';h.controller.notifyView({immediate:true});
 assert.equal(h.messages[0].payload.request_id,'view');assert.equal(h.messages[0].payload.status,'ok');
 assert.equal(h.messages[0].payload.view.draft,'The latest unsent words');assert.deepEqual(h.calls,[]);
 assert.equal(h.messages[0].origin,h.host.location.origin);
});
test('camera notifications debounce and pagehide flushes the latest captured view',async()=>{
 const h=await harness();for(let i=0;i<10;i++){h.view.cameraYaw=i;h.controller.notifyView();}
 assert.equal(h.timers.size,1);assert.equal(h.messages.length,0);
 h.view.cameraYaw=53;h.events.get('pagehide')();
 assert.equal(h.timers.size,0);assert.equal(h.messages[0].payload.view.cameraYaw,53);
 h.controller.notifyView();h.controller.destroy();assert.equal(h.timers.size,0);assert.equal(h.events.has('pagehide'),false);
});
test('boot and a partial restore cannot overwrite a saved parent view with intermediate state',async()=>{
 let ready=false;const gate=deferred(),h=await harness({ready:()=>ready,restore:async()=>gate.promise});
 h.controller.notifyView({immediate:true});assert.equal(h.messages.length,0);ready=true;
 const restoring=h.request('restore',{view:{started:true,draft:'saved'}});h.view.draft='intermediate';h.controller.notifyView({immediate:true});
 assert.equal(h.messages.length,0);h.view.draft='saved';gate.resolve();await restoring;
 assert.equal(h.messages.length,1);assert.equal(h.messages[0].payload.view.draft,'saved');
});
