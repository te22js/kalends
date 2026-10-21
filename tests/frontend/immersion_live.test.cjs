'use strict';
// Execute the shipped live scheduler with independent timer and save gates.
// This does not emulate the WebGL renderer or claim native timing accuracy.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
const begin=source.indexOf('function setLive('),end=source.indexOf('function applyPreferences(',begin);
if(begin<0||end<begin)throw Error('The shipped Live functions could not be isolated.');
const functions=source.slice(begin,end);
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};};

function harness(){
 let timerId=0,dialog=false,remaining=0,advance=()=>Promise.resolve();
 const timers=new Map(),requests=[],errors=[];
 const button={textContent:'',attributes:{},setAttribute(key,value){this.attributes[key]=value;}};
 const S={live:false,liveTimer:null,liveEpoch:0,started:true,nav:{active:false},selected:null,renderer:{remaining:()=>remaining}};
 const bridge={pending:false,advance:(...args)=>{requests.push(args);return advance(...args);}};
 const sandbox={S,bridge,$:()=>button,dialogOpen:()=>dialog,fail:error=>errors.push(error),setTimeout:(callback,delay)=>{const id=++timerId;timers.set(id,{callback,delay});return id;},clearTimeout:id=>timers.delete(id)};
 vm.createContext(sandbox);vm.runInContext(functions,sandbox,{filename:'main.js:live-scheduler'});
 return{S,bridge,timers,requests,errors,button,setLive:sandbox.setLive,
  setAdvance:fn=>advance=fn,setDialog:value=>dialog=value,setRemaining:value=>remaining=value,
  run(id=S.liveTimer){const timer=timers.get(id);if(!timer)throw Error('No timer '+id);timers.delete(id);return timer.callback();},
 };
}

test('Live advances exactly one explicit minute and schedules after the save resolves',async()=>{
 const h=harness(),gate=deferred();h.setAdvance(()=>gate.promise);h.setLive(true);
 assert.equal(h.timers.size,1);assert.equal(h.timers.get(h.S.liveTimer).delay,1800);
 const running=h.run();assert.deepEqual(h.requests,[[1,'live']]);assert.equal(h.timers.size,0,'a pending save must not queue another tick');
 gate.resolve();await running;assert.equal(h.timers.size,1);assert.equal(h.S.live,true);
 assert.equal(h.button.textContent,'Pause');assert.equal(h.button.attributes['aria-pressed'],'true');
});

test('Pause then Live during a save cannot revive the previous timer chain',async()=>{
 const h=harness(),gate=deferred();h.setAdvance(()=>gate.promise);h.setLive(true);
 const old=h.run();h.setLive(false);h.setLive(true);const currentTimer=h.S.liveTimer;
 assert.equal(h.timers.size,1);gate.resolve();await old;
 assert.equal(h.timers.size,1,'the old save response must not schedule a second chain');
 assert.equal(h.S.liveTimer,currentTimer,'the fresh Live session owns its timer');
 assert.deepEqual(h.requests,[[1,'live']]);
});

test('pausing a pending tick permits that accepted minute but schedules no future one',async()=>{
 const h=harness(),gate=deferred();h.setAdvance(()=>gate.promise);h.setLive(true);const running=h.run();
 h.setLive(false);gate.resolve();await running;
 assert.deepEqual(h.requests,[[1,'live']]);assert.equal(h.timers.size,0);assert.equal(h.S.live,false);
 assert.equal(h.button.textContent,'Live');assert.equal(h.button.attributes['aria-pressed'],'false');
});

test('an already queued callback from an old Live session cannot disturb the new one',async()=>{
 const h=harness();h.setLive(true);const oldCallback=h.timers.get(h.S.liveTimer).callback;
 h.setLive(false);h.setLive(true);const currentTimer=h.S.liveTimer;await oldCallback();
 assert.equal(h.requests.length,0);assert.equal(h.timers.size,1);assert.equal(h.S.liveTimer,currentTimer);
});

test('repeated Live toggles retain one timer and never advance time immediately',()=>{
 const h=harness();for(let i=0;i<10;i++){h.setLive(true);h.setLive(false);}h.setLive(true);h.setLive(true);
 assert.equal(h.timers.size,1);assert.equal(h.requests.length,0);
});

for(const reason of ['not started','API pending','navigation active','conversation','dialog','visual tail']){
 test('Live waits without a consequential call while '+reason,async()=>{
  const h=harness();
  if(reason==='not started')h.S.started=false;
  if(reason==='API pending')h.bridge.pending=true;
  if(reason==='navigation active')h.S.nav.active=true;
  if(reason==='conversation')h.S.selected='Felix';
  if(reason==='dialog')h.setDialog(true);
  if(reason==='visual tail')h.setRemaining(2);
  h.setLive(true);await h.run();assert.equal(h.requests.length,0);assert.equal(h.timers.size,1);
 });
}

test('a failed save stops Live and reports once without automatic POST retry',async()=>{
 const h=harness(),failure=Error('Save failed');h.setAdvance(()=>Promise.reject(failure));h.setLive(true);await h.run();
 assert.equal(h.S.live,false);assert.equal(h.timers.size,0);assert.deepEqual(h.requests,[[1,'live']]);assert.deepEqual(h.errors,[failure]);
});
