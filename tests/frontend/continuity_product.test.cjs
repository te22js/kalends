'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {UsageClock,usageSessionId}=require('../../kalends/experience_os/static/product/app.js');

// The real shell runs against a controlled DOM/network/clock boundary. This is
// deterministic regression coverage, not a human playtest or native-browser QA.
const {shellHarness}=require('./helpers/product_harness.cjs');

test('active time expires after 30 seconds while foreground idle remains visible',()=>{
  const clock=new UsageClock(0);clock.activity(0);
  assert.deepEqual(clock.drain(45000),{visible_ms:45000,foreground_ms:45000,active_ms:30000,idle_ms:15000});
  assert.deepEqual(clock.drain(60000),{visible_ms:15000,foreground_ms:15000,active_ms:0,idle_ms:15000});
});

test('hidden and unfocused time cannot become active or be charged to a later interaction',()=>{
  const clock=new UsageClock(0);clock.activity(0);clock.boundary(10000,{focused:false});
  assert.deepEqual(clock.drain(20000),{visible_ms:20000,foreground_ms:10000,active_ms:10000,idle_ms:0});
  clock.boundary(20000,{visible:false});clock.activity(40000);clock.boundary(50000,{visible:true,focused:true});
  assert.deepEqual(clock.drain(60000),{visible_ms:10000,foreground_ms:10000,active_ms:0,idle_ms:10000});
});

test('session identifiers survive reload and blocked storage still permits an opaque session',()=>{
  const map=new Map(),storage={getItem:k=>map.get(k),setItem:(k,v)=>map.set(k,v)};
  assert.equal(usageSessionId(storage,()=> 'first_uuid'),'first_uuid');
  assert.equal(usageSessionId(storage,()=> 'second_uuid'),'first_uuid');
  assert.equal(usageSessionId({getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}},()=> 'fallback_uuid'),'fallback_uuid');
});

test('default-off life sends no usage events and creates no usage session state',async()=>{
  const h=await shellHarness();await h.activity();h.advanceClock(45000);await h.visible(false);await h.pagehide();
  assert.deepEqual(h.events(),[]);assert.equal([...h.stored.keys()].some(k=>k.startsWith('kalends:usage')),false);
  assert.equal([...h.timers.values()].some(t=>t.ms===15000),false);
});

test('opt-in begins timing at consent, uses foreground idle deltas and omits all input content',async()=>{
  const h=await shellHarness();h.advanceClock(120000);await h.consent(true);await h.frameActivity();h.advanceClock(45000);await h.heartbeat();
  const interval=h.events().at(-1);assert.equal(interval.event,'active_interval');assert.equal(interval.active_ms,30000);assert.equal(interval.idle_ms,15000);assert.equal(interval.visible_ms,45000);assert.equal(interval.elapsed_ms,45000);
  const serialized=JSON.stringify(h.events());assert.doesNotMatch(serialized,/PRIVATE|DRAFT|KEY|utterance|coordinates/);
  const allowed=new Set(['id','event','visible_ms','foreground_ms','active_ms','idle_ms','elapsed_ms','session_id','reason','accepted_revision','first_meaningful']);
  for(const row of h.events())for(const key of Object.keys(row))assert.ok(allowed.has(key),key);
});

test('visibility and focus flush the old interval without turning away time into activity',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});await h.activity();h.advanceClock(10000);await h.focus(false);h.advanceClock(10000);await h.heartbeat();
  assert.equal(h.events().at(-1).visible_ms,10000);assert.equal(h.events().at(-1).foreground_ms,0);assert.equal(h.events().at(-1).active_ms,0);
  await h.visible(false);h.advanceClock(10000);await h.visible(true);
  assert.equal(h.events().at(-1).visible_ms,0);assert.equal(h.events().at(-1).active_ms,0);
});

test('moves and duplicate reconciliation never become first meaningful accepted choices',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});
  h.life.life.revision=1;h.life.snapshot.command_count=1;await h.accepted('move');assert.equal(h.events().filter(e=>e.event==='meaningful_action').length,0);
  h.life.life.revision=2;h.life.snapshot.command_count=2;h.life.telemetry.meaningful_revision=2;await h.accepted();await h.accepted();
  h.life.life.revision=3;h.life.snapshot.command_count=3;h.life.telemetry.meaningful_revision=3;await h.accepted();
  const actions=h.events().filter(e=>e.event==='meaningful_action');assert.equal(actions.length,2);assert.deepEqual(actions.map(e=>e.first_meaningful),[true,false]);assert.deepEqual(actions.map(e=>e.accepted_revision),[2,3]);
});

test('reload retains the session and first-choice marker while never replaying an old action',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});h.life.life.revision=1;h.life.telemetry.meaningful_revision=1;await h.accepted();
  const reload=await shellHarness({initialLife:h.life,initialStored:h.stored});assert.equal(reload.events().filter(e=>e.event==='session_start').length,0);assert.equal(reload.events().find(e=>e.event==='return_resumed').reason,'reload');
  await reload.accepted();assert.equal(reload.events().filter(e=>e.event==='meaningful_action').length,0);
  reload.life.life.revision=2;reload.life.telemetry.meaningful_revision=2;await reload.accepted();assert.equal(reload.events().find(e=>e.event==='meaningful_action').first_meaningful,false);
  assert.equal(reload.events()[0].session_id,h.events()[0].session_id);
});

test('opting out suppresses later events even while the server write is pending',async()=>{
  let finish;const pending=new Promise(resolve=>finish=resolve);
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}},responder:async({url,body,life})=>{if(url==='/product/api/telemetry'&&body.opt_in===false){await pending;life.telemetry.opt_in=false;return {body:{opt_in:false,recorded:false}};}}});
  const before=h.events().length;await h.consent(false);await h.activity();h.advanceClock(45000);await h.visible(false);await h.pagehide();assert.equal(h.events().length,before);
  finish();await h.settle();assert.equal(h.node('#telemetry-opt-in').checked,false);
});

test('cancelled review records only a fixed decline category and acceptance does not decline',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}},responder:({url})=>url==='/product/api/propose'?{body:{proposal_id:'review_1',action:{action:'inspect'}}}:undefined});
  await h.clickData({action:'inspect'});h.node('#review-dialog').close();await h.settle();
  const declined=h.events().filter(e=>e.event==='choice_declined');assert.equal(declined.length,1);assert.equal(declined[0].reason,'cancelled');assert.equal('proposal_id' in declined[0],false);
});

test('consequence views require a displayed consequence, and later same-tab returns show new saved changes',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});await h.clickId('story-button');assert.equal(h.events().filter(e=>e.event==='consequence_viewed').length,0);await h.clickId('close-story');
  await h.navigate('/your-worlds');h.life.life.revision=1;h.life.history.chapters=[{title:'A result',kind:'consequence',beats:[{title:'Recorded delivery',kind:'consequence'}]}];h.life.return_summary={changes:[{kind:'consequence',text:'A saved delivery changed.'}]};await h.navigate('/lives/life_a');
  assert.match(h.node('#world-notice').innerHTML,/A saved delivery changed/);assert.equal(h.events().find(e=>e.event==='return_resumed').reason,'return');
  assert.ok(h.events().some(e=>e.event==='consequence_viewed'&&e.reason==='return'));await h.clickId('story-button');assert.ok(h.events().some(e=>e.event==='consequence_viewed'&&e.reason==='history'));
});

test('operator entry and categorized errors never send raw diagnostics',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0,operator_exposed:true}},responder:({url})=>url==='/product/api/propose'?{status:409,body:{error:'PRIVATE ECONOMIC DETAIL',code:'stale_proposal'}}:undefined});
  assert.equal(h.node('#operator-exposure').hidden,false);await h.clickData({action:'inspect'});assert.equal(h.events().find(e=>e.event==='error').reason,'stale');assert.doesNotMatch(JSON.stringify(h.events()),/PRIVATE ECONOMIC DETAIL/);
  await h.navigate('/lab/life_a');await h.enterLab();assert.ok(h.events().some(e=>e.event==='research_entered'));await h.navigate('/lives/life_a');assert.doesNotMatch(h.node('#main').innerHTML,/PRIVATE_OPERATOR_RECORD/);
});

test('fractional timing rounds to a consistent foreground partition',()=>{
  const clock=new UsageClock(0);clock.activity(0);const result=clock.drain(30000.5);assert.equal(result.foreground_ms,result.active_ms+result.idle_ms);assert.ok(result.active_ms<=result.foreground_ms&&result.foreground_ms<=result.visible_ms);
});

test('background rendering does not claim a consequence was viewed',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0},history:{chapters:[{title:'A delivery',kind:'consequence',beats:[]}]}}});
  await h.visible(false);await h.clickId('story-button');assert.equal(h.events().filter(e=>e.event==='consequence_viewed').length,0);
});

test('a local move cannot claim another tab’s intervening meaningful action',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});h.life.life.revision=2;h.life.telemetry.meaningful_revision=1;await h.accepted('move',2);
  assert.equal(h.events().filter(e=>e.event==='meaningful_action').length,0);
  h.life.life.revision=4;h.life.telemetry.meaningful_revision=4;await h.accepted('action',3);
  assert.equal(h.events().find(e=>e.event==='meaningful_action').accepted_revision,3);
});

test('typed scene rejection reports only an allowed category, never its message',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}}});
  await h.scene({kind:'kalends:rejected',reason:'network',error:'PRIVATE DIAGNOSTIC'});
  await h.scene({kind:'kalends:rejected',reason:'PRIVATE CATEGORY',error:'PRIVATE DIAGNOSTIC'});
  const errors=h.events().filter(e=>e.event==='error');assert.deepEqual(errors.map(e=>e.reason),['network','rejected']);assert.doesNotMatch(JSON.stringify(errors),/PRIVATE/);
});

test('failed opt-out remains locally paused across reload instead of trusting stale server consent',async()=>{
  const h=await shellHarness({initialLife:{telemetry:{opt_in:true,meaningful_revision:0}},responder:({url,body})=>url==='/product/api/telemetry'&&body.opt_in===false?{status:400,body:{error:'Preference write failed'}}:undefined});
  await h.consent(false);const reload=await shellHarness({initialLife:h.life,initialStored:h.stored});assert.deepEqual(reload.events(),[]);assert.equal(reload.node('#telemetry-opt-in').checked,false);
  await reload.consent(true);assert.ok(reload.events().some(e=>e.event==='life_entered'));
});

test('beginning a new Observatory life skips the return notice but a later return keeps it',async()=>{
  const h=await shellHarness({path:'/worlds/shared_observatory',initialLife:{life:{id:'life_a',template_id:'shared_observatory',revision:0},snapshot:{setting:'commons',command_count:0,minute:0}},responder:({url,life})=>url==='/product/api/start'?{body:life}:undefined});
  await h.clickData({start:'shared_observatory'});await h.settle();assert.equal(h.location.pathname,'/lives/life_a');assert.equal(h.node('#world-notice').hidden,true);assert.equal(h.node('#world-notice').innerHTML,'');
  await h.navigate('/your-worlds');await h.navigate('/lives/life_a');assert.equal(h.node('#world-notice').hidden,false);assert.match(h.node('#world-notice').innerHTML,/Your place is still here/);
});

test('opening an existing zero-choice life still offers its saved-place return notice',async()=>{
  const h=await shellHarness();assert.equal(h.life.life.revision,0);assert.equal(h.node('#world-notice').hidden,false);assert.match(h.node('#world-notice').innerHTML,/Your place is still here/);
});
