'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {capacityFromReport,allocationTotal}=require('../../kalends/experience_os/static/product/app.js');
const {shellHarness}=require('./helpers/product_harness.cjs');
const steps={
 role:{id:'o0',title:'You coordinate one shared instrument.',body:'Read what the teams request before deciding.',action:{kind:'ack',label:'Begin the guided round',ack:'role_arrival'}},
 request:{id:'o1',title:'Read a real request.',body:'Amir requests four units. A request creates no promise.',action:{kind:'ack',label:'I understand this request',ack:'request_read'}},
 report:{id:'o2',title:'Ask Mira for her dated report.',body:'Current condition not yet known. Rated capacity is twelve.',action:{kind:'report',label:'Ask Mira for the report'}},
 allocation:{id:'o3',title:'Choose an allocation.',body:'Use the evidence you actually received.',action:{kind:'allocation',label:'Review your allocation'}},
 promise:{id:'o4',title:'A promise is optional and separate.',body:'Changing allocation does not make a promise.',action:{kind:'promise',label:'Review an optional promise',ack:'promise_explained'}},
 finish:{id:'o5',title:'Finish this round deliberately.',body:'Review the target time before advancing.',action:{kind:'finish_round',label:'Review and finish this round'}},
 results:{id:'o6',title:'Read what actually happened.',body:'Compare your allocation and delivery.',action:{kind:'results',label:'Review the actual result',ack:'reflection_done'}},
 complete:{id:'o7',title:'Continue with less guidance.',body:'Help remains available.',action:{kind:'complete',label:'Continue exploring'}}
};
const freshGuide=(step=steps.role,patch={})=>({version:'first-session-v1',enabled:true,learn:false,practice:false,step,completed:[],chapters:[{id:step.id,title:step.title,status:'current'}],known:{summary:['Requests are not promises.'],evidence:[],project_requirements:[{text:'Amir needs four units in a settled batch.'}]},result:null,history_cards:[],...patch});
const commons=(guide=freshGuide())=>({life:{id:'life_a',template_id:'shared_observatory',revision:0,minute:0,state_hash:'a'.repeat(64)},snapshot:{setting:'commons',minute:0,command_count:0,state_hash:'a'.repeat(64),allocation:null,promises:{},requests:{team_a:4,team_b:4,team_c:4},credits:12,own_reports:[]},guide,time:{known_stops:[{kind:'public_round_deadline',at:1439,title:'The round settles'}]}});
const posts=h=>h.requests.filter(r=>r.method==='POST');

test('homepage and world details explain the role, real actions, guidance and fiction plainly',async()=>{
 const h=await shellHarness({path:'/',initialCatalog:{templates:[{id:'pompeii_life'},{id:'shared_observatory'}]}});
 const home=h.node('#main').innerHTML;assert.match(home,/<h1>A morning<br>in Pompeii\.<\/h1>/);assert.match(home,/You are Aelia\. A flour cart has arrived, but two buyers claim it/);assert.match(home,/Enter Shared Observatory/);assert.match(home,/Aelia and the dispute are fictional/);assert.match(home,/Continue this life/);assert.equal(posts(h).filter(r=>/\/(start|observe|confirm|advance)$/.test(r.url)).length,0);
 await h.navigate('/worlds/shared_observatory');const markup=h.node('#main').innerHTML;for(const label of ['Your role','The starting situation','Three things you can do','What you can learn','What is simplified'])assert.ok(markup.includes(label),label);assert.ok(markup.indexOf('Your role')<markup.indexOf('What is simplified'));assert.match(markup,/data-guided="false"/);
});

test('guided and unguided starts send an explicit preference without confirming a game action',async()=>{
 for(const guided of ['true','false']){const h=await shellHarness({path:'/worlds',responder:({url,life})=>url==='/product/api/start'?{body:life}:undefined});await h.clickData({start:'pompeii_life',guided});assert.equal(posts(h).find(r=>r.url==='/product/api/start').body.guided,guided==='true');assert.equal(posts(h).some(r=>r.url.endsWith('/confirm')||r.url.endsWith('/advance')),false);}
});

test('guide acknowledgements and on/off/resume remain metadata-only and render server progress',async()=>{
 const h=await shellHarness({initialLife:commons(),responder:({url,body,life})=>{if(url==='/product/api/guide'&&body.ack==='role_arrival'){life.guide.step=steps.request;return {body:life};}}});
 assert.match(h.node('#guide-panel').innerHTML,/Begin the guided round/);await h.clickData({guideAction:'ack'});assert.equal(posts(h).find(r=>r.url==='/product/api/guide').body.ack,'role_arrival');assert.match(h.node('#guide-panel').innerHTML,/Read a real request/);
 await h.clickData({guideEnabled:'false'});assert.equal(h.node('#guide-panel').hidden,true);await h.clickId('help-button');assert.match(h.node('#help-content').innerHTML,/Resume guidance/);await h.clickData({guideEnabled:'true'});assert.equal(h.node('#guide-panel').hidden,false);
 assert.equal(posts(h).filter(r=>/\/(confirm|advance|propose)$/.test(r.url)).length,0);
});

test('an explicit free question admits one observation without pre-click disclosure or a review',async()=>{
 const h=await shellHarness({initialLife:commons(freshGuide(steps.report)),responder:({url,body,life})=>{
  if(url==='/product/api/observe'){
   assert.deepEqual(body,{id:'life_a',action:{action:'share',recipient:'team_b'},expected_revision:0,expected_state_hash:'a'.repeat(64)});
   life.life.revision=1;life.life.state_hash='b'.repeat(64);life.snapshot.command_count=1;
   life.snapshot.own_reports=[{tick:0,payload:{value:'fragile',as_of:0,origin_observer:'team_b'}}];
   return {body:{...life,outcome:'accepted',accepted_revision:1,receipt:{event_id:9}}};
  }
 }});
 assert.match(h.node('#observatory-stage').innerHTML,/Current condition unknown/);
 assert.doesNotMatch(h.node('#observatory-stage').innerHTML,/8 reported usable|Mira’s report · observed/);
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,0);
 await h.clickData({guideAction:'report'});
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,1);
 assert.equal(posts(h).filter(r=>/\/(propose|confirm|advance)$/.test(r.url)).length,0);
 assert.equal(h.node('#review-dialog').open,false);assert.equal(h.life.life.revision,1);
 assert.match(h.node('#observatory-stage').innerHTML,/8 reported usable units/);
 assert.match(h.node('#observatory-stage').innerHTML,/Mira’s report · observed Day 1 · 00:00/);
 assert.equal(h.life.snapshot.minute,0);assert.equal(h.life.snapshot.credits,12);assert.deepEqual(h.life.snapshot.promises,{});
});

test('a delayed free answer prevents a second observation and keeps undisclosed state private',async()=>{
 let release;const delay=new Promise(resolve=>{release=resolve;});
 const h=await shellHarness({initialLife:commons(freshGuide(steps.report)),responder:async({url,life})=>{
  if(url==='/product/api/observe'){await delay;life.life.revision=1;life.snapshot.command_count=1;life.snapshot.own_reports=[{tick:0,payload:{value:'fragile',as_of:0,origin_observer:'team_b'}}];return {body:{...life,outcome:'accepted',accepted_revision:1}};}
 }});
 await h.clickData({action:'report'});await h.clickData({guideAction:'report'});
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,1);
 assert.equal(h.life.life.revision,0);assert.doesNotMatch(h.node('#observatory-stage').innerHTML,/8 reported usable/);
 release();await h.settle();assert.equal(h.life.life.revision,1);
 assert.equal(posts(h).filter(r=>/\/(propose|confirm|advance)$/.test(r.url)).length,0);
});

test('allocation totals use admitted dated evidence and keep no-promise distinct from explicit zero',async()=>{
 const initial=commons(freshGuide(steps.allocation));initial.snapshot.promises={team_a:0};initial.snapshot.own_reports=[{tick:0,payload:{value:'fragile',as_of:0,origin_observer:'team_b'}}];initial.snapshot.minute=60;
 const h=await shellHarness({initialLife:initial});await h.inputAllocation({team_a:4,team_b:4,team_c:4});assert.match(h.node('#allocation-total').innerHTML,/Total: 12 of 12/);assert.match(h.node('#allocation-total').innerHTML,/exceeds the 8 usable units in your last dated report/);assert.match(h.node('#observatory-stage').innerHTML,/0 units promised/);assert.match(h.node('#observatory-stage').innerHTML,/No promise/);assert.match(h.node('#observatory-stage').innerHTML,/earlier observation; conditions can change/);
 assert.equal(capacityFromReport({payload:{value:'PRIVATE_OTHER'}}),null);assert.equal(allocationTotal({team_a:4,team_b:4,team_c:0}),8);assert.equal(posts(h).some(r=>r.url.endsWith('/confirm')),false);
});

test('finish-round review explains the exact target, saved allocation, evidence and obligations before advancing',async()=>{
 const initial=commons(freshGuide(steps.finish));initial.snapshot.allocation={team_a:4,team_b:4,team_c:0};initial.known_commitments=[{text:'You promised four units to Amir.'}];
 const h=await shellHarness({initialLife:initial});await h.clickData({guideAction:'finish_round'});assert.equal(h.node('#time-dialog').open,true);assert.match(h.node('#known-deadlines').innerHTML,/Day 1 · 00:00 to Day 1 · 23:59: the rest of this day/);assert.match(h.node('#known-deadlines').innerHTML,/Amir 4, Mira 4, Lin 0/);assert.match(h.node('#known-deadlines').innerHTML,/You promised four units to Amir/);assert.match(h.node('#known-deadlines').innerHTML,/data-advance="1439" data-mode="compress" data-protect="false">Run with these saved choices/);assert.equal(posts(h).some(r=>r.url.endsWith('/advance')),false);
});

test('actual result shows all four quantities and never invents an unmade promise or a retry outcome',async()=>{
 const result={at:1439,requests:{team_a:4,team_b:4,team_c:4},promises:{team_c:4},allocation:{team_a:4,team_b:4,team_c:4},executed:{team_a:4,team_b:4,team_c:0},actual_capacity:8,explanation:['Eight units were available. Lin received none, so the recorded promise was missed.']};
 const initial=commons(freshGuide(steps.results,{result}));initial.snapshot.round_closed=true;const h=await shellHarness({initialLife:initial});const markup=h.node('#observatory-stage').innerHTML;for(const label of ['Requested','Promised','Allocated','Delivered','Eight units were available','None','Skip reflection'])assert.ok(markup.includes(label),label);assert.match(markup,/>Lin<\/th><td>4<\/td><td>4<\/td><td>4<\/td><td>0<\/td>/);assert.equal(posts(h).some(r=>r.url.endsWith('/fork')),false);
});

test('a later open round keeps the previous result but does not invite skipping the active round',async()=>{
 const result={at:1439,requests:{},promises:{},allocation:{},executed:{},explanation:['No allocation was recorded.']};const h=await shellHarness({initialLife:commons(freshGuide(steps.complete,{result}))});assert.match(h.node('#observatory-stage').innerHTML,/<summary>Last round’s result<\/summary>/);assert.match(h.node('#observatory-stage').innerHTML,/data-guide-action="finish_round"/);assert.doesNotMatch(h.node('#observatory-stage').innerHTML,/data-guide-action="next_round"/);
});

test('history cards use specific evidence labels, safe sources and an explicit metadata save',async()=>{
 const card={id:'H1',title:'A food counter',available:true,read:false,encounter:'A represented counter.',claim:'Counters sold food and drink.',evidence:'A source-supported counter has jars.',limits:'This scene is simplified.',game_changed:'Sabina and her prices are fictional.',labels:['Historical evidence','Reconstruction','Fictional gameplay'],sources:[{title:'Park source',url:'https://pompeiisites.org/en/pompeii-map/'},{title:'Unsafe',url:'javascript:alert(1)'}]};
 const h=await shellHarness({initialLife:{guide:freshGuide(steps.role,{learn:true,history_cards:[card]})}});await h.clickData({openNotebook:''});assert.equal(h.node('#notebook-dialog').open,true);h.node('#notebook-dialog').close();await h.clickId('help-button');await h.clickData({guideAction:'history'});await h.clickData({historyCard:'H1'});
 const markup=h.node('#notebook-content').innerHTML;for(const label of ['Place & history','Counters sold food and drink.','How do we know?','A source-supported counter has jars.','This scene is simplified.','What we invented','Sabina and her prices are fictional'])assert.ok(markup.includes(label),label);assert.doesNotMatch(markup,/javascript:|href="Unsafe/);assert.ok(markup.indexOf('Counters sold food and drink.')<markup.indexOf('How do we know?'));assert.match(markup,/<details><summary>How do we know\?<\/summary>/);assert.ok(posts(h).some(r=>r.url==='/product/api/guide'&&r.body.card==='H1'));assert.equal(posts(h).some(r=>/\/(confirm|advance|act)$/.test(r.url)),false);
});

test('unavailable history cards cannot be saved by forged UI requests',async()=>{
 const h=await shellHarness({initialLife:{guide:freshGuide(steps.role,{history_cards:[{id:'H2',title:'A workshop',available:false}]})}});await h.clickData({historyCard:'H2'});assert.equal(posts(h).some(r=>r.url==='/product/api/guide'),false);
});

test('Help and notebook pause the scene and close without remounting it',async()=>{
 const h=await shellHarness({initialLife:{guide:freshGuide()}}),frame=h.frame();await h.clickId('help-button');assert.ok(h.messages.some(m=>m.data.kind==='kalends:host'&&m.data.action==='pause'));assert.equal(h.node('#help-dialog').open,true);h.node('#help-dialog').close();await h.settle();assert.equal(h.frame(),frame);assert.ok(h.messages.some(m=>m.data.kind==='kalends:host'&&m.data.action==='refresh'));await h.scene({status:'ready'});assert.ok(h.messages.some(m=>m.data.kind==='kalends:guide'&&m.data.guide.version==='first-session-v1'));
});

test('optional learning preference changes only guide metadata',async()=>{
 const h=await shellHarness({initialLife:{guide:freshGuide()}});await h.change('learn-as-explore',{checked:true});assert.ok(posts(h).some(r=>r.url==='/product/api/guide'&&r.body.learn===true));assert.equal(posts(h).some(r=>r.url.endsWith('/confirm')),false);
});

test('help and invalid-action telemetry stay optional and carry fixed categories only',async()=>{
 const h=await shellHarness({initialLife:{...commons(),telemetry:{opt_in:true,meaningful_revision:0}},responder:({url})=>url==='/product/api/propose'?{status:400,body:{error:'Not enough credits: PRIVATE DETAIL'}}:undefined});await h.clickId('help-button');await h.clickData({action:'inspect'});assert.ok(h.events().some(e=>e.event==='guide_help'&&e.reason==='guide'));assert.ok(h.events().some(e=>e.event==='invalid_action'&&e.reason==='affordability'));assert.doesNotMatch(JSON.stringify(h.events()),/PRIVATE DETAIL|step_id|card_id/);
 const off=await shellHarness({initialLife:commons()});await off.clickId('help-button');assert.deepEqual(off.events(),[]);
});

test('a practice request creates a separate life through the dedicated endpoint without replaying the original',async()=>{
 const h=await shellHarness({initialLife:commons(),responder:({url,life})=>url==='/product/api/practice'?{body:{...life,life:{...life.life,id:'practice_b'}}}:undefined});await h.clickData({practice:''});assert.equal(posts(h).filter(r=>r.url==='/product/api/practice').length,1);assert.equal(h.location.pathname,'/lives/practice_b');assert.equal(h.life.life.id,'life_a');assert.equal(posts(h).some(r=>/\/(confirm|advance|act)$/.test(r.url)),false);
});

test('one guided Observatory round uses real action handlers and never auto-promises or advances',async()=>{
 let proposed=null;
 const h=await shellHarness({initialLife:commons(),responder:({url,body,life})=>{
  if(url==='/product/api/guide'){
   if(body.ack==='role_arrival')life.guide.step=steps.request;
   if(body.ack==='request_read')life.guide.step=steps.report;
   if(body.ack==='promise_explained')life.guide.step=steps.finish;
   if(body.ack==='reflection_done')life.guide.step=steps.complete;
   if('enabled' in body)life.guide.enabled=body.enabled;
   return {body:life};
  }
  if(url==='/product/api/propose'){proposed=body.action;return {body:{proposal_id:'review_'+(life.life.revision+1),action:proposed}};}
  if(url==='/product/api/observe'){
   assert.deepEqual(body.action,{action:'share',recipient:'team_b'});assert.equal(body.expected_revision,0);assert.equal(body.expected_state_hash,'a'.repeat(64));
   life.life.revision++;life.snapshot.command_count=life.life.revision;life.snapshot.own_reports=[{tick:0,payload:{value:'fragile',as_of:0,origin_observer:'team_b'}}];life.guide.step=steps.allocation;return {body:{...life,outcome:'accepted',accepted_revision:1}};
  }
  if(url==='/product/api/confirm'){
   life.life.revision++;life.snapshot.command_count=life.life.revision;
   if(proposed.action==='allocate'){life.snapshot.allocation=proposed.allocation;life.guide.step=steps.promise;}
   return {body:life};
  }
  if(url==='/product/api/advance'){
   life.life.revision++;life.snapshot.command_count=life.life.revision;life.snapshot.minute=1439;life.snapshot.round_closed=true;
   life.guide.result={at:1439,requests:life.snapshot.requests,promises:{},allocation:life.snapshot.allocation,executed:{team_a:4,team_b:4,team_c:0},explanation:['Eight units were available. Amir received four and Mira received four.']};life.guide.step=steps.results;return {body:life};
  }
 }});
 await h.clickData({guideAction:'ack'});await h.clickData({guideAction:'ack'});await h.clickData({guideAction:'report'});assert.equal(h.life.life.revision,1);assert.equal(h.node('#review-dialog').open,false);
 await h.inputAllocation({team_a:4,team_b:4,team_c:0});h.node('#allocation-form').elements={team_a:{value:'4'},team_b:{value:'4'},team_c:{value:'0'}};await h.submitId('allocation-form');assert.equal(h.life.life.revision,1);await h.clickId('confirm-choice');assert.equal(h.life.life.revision,2);
 await h.clickData({guideAck:'promise_explained'});assert.equal(h.life.life.revision,2);assert.deepEqual(h.life.snapshot.promises,{});await h.clickData({guideAction:'finish_round'});assert.equal(posts(h).some(r=>r.url.endsWith('/advance')),false);
 await h.clickData({advance:'1439',mode:'compress',protect:'false'});assert.equal(h.life.life.revision,3);assert.match(h.node('#observatory-stage').innerHTML,/Eight units were available/);assert.equal(h.life.snapshot.credits,12);
 await h.clickData({guideAck:'reflection_done'});await h.clickData({guideAction:'complete'});assert.equal(h.node('#guide-panel').hidden,true);assert.equal(posts(h).filter(r=>r.url.endsWith('/confirm')).length,1);assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,1);assert.equal(posts(h).filter(r=>r.url.endsWith('/advance')).length,1);assert.equal(posts(h).filter(r=>r.url.endsWith('/propose')).some(r=>r.body.action.action==='commit'),false);
});

test('unavailable historical learning remains optional and learn-off accepts the server’s next step',async()=>{
 const step={id:'p4',title:'Learn one historical idea.',body:'Visit a public food counter or skip this optional lesson.',action:{kind:'history',card:'food_counter',label:'What is this place?'}};
 const h=await shellHarness({initialLife:{guide:freshGuide(step,{learn:true,history_cards:[{id:'food_counter',title:'The food counter',available:false}]})},responder:({url,body,life})=>{if(url==='/product/api/guide'&&(body.learn===false||body.ack==='skip_history')){life.guide.learn=body.learn??life.guide.learn;life.guide.step={id:'p5',title:'Compare the accounts.',body:'Choose another supported route.',action:{kind:'scene',label:'Seek another account'}};return {body:life};}}});
 await h.clickId('help-button');assert.match(h.node('#help-content').innerHTML,/Skip this history lesson/);await h.change('learn-as-explore',{checked:false});assert.match(h.node('#help-content').innerHTML,/Compare the accounts/);assert.equal(posts(h).some(r=>r.body?.card),false);
 await h.scene({kind:'kalends:guide-request',action:'skip-history'});assert.ok(posts(h).some(r=>r.body?.ack==='skip_history'));assert.equal(posts(h).some(r=>/\/(confirm|advance|act)$/.test(r.url)),false);
});

test('unsupported language records a fixed invalid-loop category without storing the utterance',async()=>{
 const h=await shellHarness({initialLife:{...commons(),telemetry:{opt_in:true,meaningful_revision:0}},responder:({url})=>url==='/product/api/intent'?{body:{clarification:'Try asking for a report or use a suggested choice.'}}:undefined});h.node('#common-speech-input').value='MY PRIVATE UNSUPPORTED REQUEST';await h.submitId('common-speech');assert.ok(h.events().some(e=>e.event==='invalid_action'&&e.reason==='control_help'));assert.doesNotMatch(JSON.stringify(h.events()),/MY PRIVATE/);assert.equal(posts(h).some(r=>r.url.endsWith('/confirm')),false);
});

test('direct inspection and copied testimony retain their actual evidence type and practice stays labelled',async()=>{
 const initial=commons(freshGuide(steps.allocation,{practice:true,enabled:false,known:{report:{kind:'direct observation'},evidence:[{title:'An account',text:'One person described an expectation.',source:'Mira',kind:'Testimony'},{title:'Copied order',text:'Its holder recorded a claim.',source:'Sabina',kind:'Copied fictional document; its contents are a claim'}]}}));initial.snapshot.own_reports=[{etype:'observe',tick:0,payload:{category:'condition',value:'fragile'}}];
 const h=await shellHarness({initialLife:initial});assert.match(h.node('#observatory-stage').innerHTML,/Your inspection · observed Day 1 · 00:00/);assert.doesNotMatch(h.node('#observatory-stage').innerHTML,/Mira’s report · observed/);assert.match(h.node('#world-participant').textContent,/Practice copy/);await h.clickId('help-button');assert.match(h.node('#help-content').innerHTML,/Dated testimony/);assert.match(h.node('#help-content').innerHTML,/Copied fictional document; its contents are a claim/);
});

test('quantity and old return sentences preserve zero, singular, plural and punctuation',()=>{
  const core=require('../../kalends/experience_os/static/product/app.js');
  assert.equal(core.unitQuantity(0),'0 units');
  assert.equal(core.unitQuantity(1),'1 unit');
  assert.equal(core.unitQuantity(12),'12 units');
  assert.equal(core.unitQuantity(1,'credit'),'1 credit');
  assert.equal(core.readableSentence('World time advances by 1 minutes'),'World time advances by 1 minute.');
  assert.equal(core.readableSentence('World time advances by 11 minutes.'),'World time advances by 11 minutes.');
  assert.equal(core.describeAction({action:'commit',quantity:1,recipient:'team_a'}),'Promise 1 unit to Amir');
});

test('missing requests and allocations are not displayed as explicit zero records',async()=>{
 const initial=commons(freshGuide(steps.allocation));initial.snapshot.requests={team_a:0};
 const h=await shellHarness({initialLife:initial});const markup=h.node('#observatory-stage').innerHTML;
 assert.match(markup,/0 units requested/);assert.match(markup,/No request received/);assert.match(markup,/Your decision/);assert.match(markup,/Saving this allocation does not make a promise or deliver it/);assert.doesNotMatch(markup,/Your saved allocation|Allocation saved/);assert.equal(h.life.snapshot.allocation,null);
});

test('report age is explicit without describing a current observation as old',async()=>{
 for(const [asOf,isOld] of [[60,false],[0,true]]){
  const initial=commons(freshGuide(steps.allocation));initial.snapshot.minute=60;
  initial.snapshot.own_reports=[{tick:asOf,payload:{value:'fragile',as_of:asOf,origin_observer:'team_b'}}];
  const h=await shellHarness({initialLife:initial}),markup=h.node('#observatory-stage').innerHTML;
  assert.match(markup,/8 reported usable units/);assert.match(markup,isOld?/observed Day 1 · 00:00/:/observed Day 1 · 01:00/);
  assert.equal(markup.includes('This is an earlier observation; conditions can change.'),isOld);
  assert.equal(posts(h).filter(r=>/\/(observe|propose|confirm|advance)$/.test(r.url)).length,0);
 }
});

test('accepted allocation quantities override stale tab drafts in every saved summary',async()=>{
 const h=await shellHarness({initialLife:commons(freshGuide(steps.allocation))});
 await h.inputAllocation({team_a:4,team_b:4,team_c:4});assert.match(h.node('#allocation-total').innerHTML,/Total: 12 of 12/);
 h.life.life.revision=1;h.life.snapshot.command_count=1;h.life.snapshot.allocation={team_a:4,team_b:4,team_c:0};
 await h.clickData({reconcile:''});
 assert.match(h.node('#observatory-stage').innerHTML,/Your saved allocation/);
 assert.match(h.node('#observatory-stage').innerHTML,/name="team_c"[^>]*value="0" disabled/);
 assert.match(h.node('#allocation-total').innerHTML,/Total: 8 of 12/);
 assert.doesNotMatch(h.node('#allocation-total').innerHTML,/Total: 12 of 12/);
 await h.clickData({guideAction:'finish_round'});assert.match(h.node('#known-deadlines').innerHTML,/Amir 4, Mira 4, Lin 0/);
 assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance)$/.test(r.url)).length,0);
});

test('an incomplete historical result preserves missing quantities instead of manufacturing zero',async()=>{
 const result={at:1439,requests:{team_a:0},promises:{team_a:0},allocation:{team_a:0},executed:{team_a:0},explanation:['Only part of this older result is available.']};
 const initial=commons(freshGuide(steps.complete,{result}));initial.snapshot.round_closed=true;
 const h=await shellHarness({initialLife:initial}),markup=h.node('#observatory-stage').innerHTML;
 assert.doesNotMatch(markup,/NaN|undefined units|Delivered: Amir 0 · Mira 0 · Lin 0/);
 assert.match(markup,/>Amir<\/th><td>0<\/td><td>0<\/td><td>0<\/td><td>0<\/td>/);
 assert.doesNotMatch(markup,/>Mira<\/th><td>Unknown<\/td><td>None<\/td><td>0<\/td><td>0<\/td>/);
 assert.match(markup,/Only part of this older result is available/);
 assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance)$/.test(r.url)).length,0);
});

test('a stale free question is rejected without installing an answer or retrying automatically',async()=>{
 const h=await shellHarness({initialLife:commons(freshGuide(steps.report)),responder:({url})=>url==='/product/api/observe'?{status:409,body:{code:'observation_stale',error:'The situation changed. Reopen the conversation before asking again.'}}:undefined});
 await h.clickData({action:'report'});
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,1);assert.equal(h.life.life.revision,0);
 assert.match(h.node('#global-status').textContent,/situation changed/);
 assert.doesNotMatch(h.node('#observatory-stage').innerHTML,/8 reported usable|Mira’s report · observed/);
 assert.equal(h.node('#review-dialog').open,false);assert.deepEqual(h.life.snapshot.own_reports,[]);
});

test('a paid inspection still reviews the actual fee and cancellation admits no report',async()=>{
 const h=await shellHarness({initialLife:commons(freshGuide(steps.report)),responder:({url})=>url==='/product/api/propose'?{body:{proposal_id:'paid_inspection',action:{action:'inspect'}}}:undefined});
 await h.clickData({action:'inspect'});assert.equal(h.node('#review-dialog').open,true);
 assert.match(h.node('#review-content').innerHTML,/1 of your credits/);assert.match(h.node('#review-content').innerHTML,/only after this interaction is accepted and saved/);
 h.node('#review-dialog').close();await h.settle();
 assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance)$/.test(r.url)).length,0);
 assert.equal(h.life.life.revision,0);assert.equal(h.life.snapshot.credits,12);assert.deepEqual(h.life.snapshot.own_reports,[]);
});

test('repeated speech submission while interpretation is pending cannot admit the same question twice',async()=>{
 const interpretations=[];
 const h=await shellHarness({initialLife:commons(freshGuide(steps.report)),responder:async({url,body,life})=>{
  if(url==='/product/api/intent')return await new Promise(resolve=>interpretations.push(()=>resolve({body:{action:{action:'share',recipient:'team_b'}}})));
  if(url==='/product/api/observe'){
   assert.equal(body.expected_revision,life.life.revision);
   life.life.revision++;life.snapshot.command_count=life.life.revision;life.snapshot.state_hash='b'.repeat(64);
   life.snapshot.own_reports=[{tick:0,payload:{value:'fragile',as_of:0,origin_observer:'team_b'}}];
   return {body:{...life,outcome:'accepted',accepted_revision:life.life.revision}};
  }
 }});
 h.node('#common-speech-input').value='Ask for the report';
 await h.submitId('common-speech');await h.submitId('common-speech');
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,0);
 // Deliver responses separately: a late duplicate must not use a newer revision
 // after the first observation completed. Do not rely on simultaneous responses.
 interpretations[0]();await h.settle();
 for(const release of interpretations.slice(1)){release();await h.settle();}
 assert.equal(posts(h).filter(r=>r.url.endsWith('/observe')).length,1);
 assert.equal(h.life.life.revision,1);
 assert.equal(posts(h).filter(r=>/\/(confirm|advance)$/.test(r.url)).length,0);
});

test('notebook comparison does not turn a spoken account into a copied document',async()=>{
 const evidence=[{title:'The household steward’s account',text:'I expected six sacks.',source:'Lucius',at:5,kind:'Testimony; not a verified delivery record'},
  {title:'The market account',text:'A copied order for flour.',source:'Sabina',at:2,kind:'Copied fictional document; its contents are a claim'}];
 const h=await shellHarness({initialLife:{guide:freshGuide(steps.role,{known:{evidence},history_cards:[]})}});
 await h.clickData({openNotebook:''});const markup=h.node('#notebook-content').innerHTML;
 assert.match(markup,/The accounts you received/);
 const spoken=markup.match(/<article class="account-card"><h4>The household steward’s account<\/h4>([\s\S]*?)<\/article>/)?.[1];
 const copied=markup.match(/<article class="account-card"><h4>The market account<\/h4>([\s\S]*?)<\/article>/)?.[1];
 assert.ok(spoken);assert.ok(copied);assert.match(spoken,/Spoken account/);assert.match(spoken,/claim/);
 assert.doesNotMatch(spoken,/A fictional document|Copied fictional document/);
 assert.match(copied,/Copied fictional document/);assert.match(copied,/claim/);
 assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance)$/.test(r.url)).length,0);
});

test('each team exposes its public project threshold before an allocation without inventing a request',async()=>{
 const guide=freshGuide(steps.allocation,{known:{project_requirements:[{actor:'team_b',quantity:4,deadline:1440,status:'open',text:'Mira needs four units.'}]}});
 const initial=commons(guide);initial.snapshot.requests={};const h=await shellHarness({initialLife:initial});
 const markup=h.node('#observatory-stage').innerHTML;assert.match(markup,/Public project requirement/);assert.match(markup,/4 units in one delivery/);assert.match(markup,/No request submitted yet/);
 await h.clickData({action:'project-need'});assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance|propose)$/.test(r.url)).length,0);
});


test('a valid public project question stays readable and is not counted as an invalid action',async()=>{
 const answer='The public project register: Mira needs four units in one delivery.';
 const h=await shellHarness({initialLife:{...commons(),telemetry:{opt_in:true,meaningful_revision:0}},responder:({url})=>url==='/product/api/intent'?{body:{kind:'public_record',reply:answer}}:undefined});
 h.node('#common-speech-input').value='What does your project need?';await h.submitId('common-speech');
 assert.equal(h.node('#common-answer').textContent,answer);assert.equal(h.node('#common-answer').hidden,false);
 assert.equal(h.events().some(e=>e.event==='invalid_action'),false);
 assert.equal(posts(h).filter(r=>/\/(observe|confirm|advance|propose)$/.test(r.url)).length,0);
});


test('reviewing the previous result opens its disclosure after the next day begins',async()=>{
 const result={at:1439,actual_capacity:8,allocation:{team_a:4,team_b:4,team_c:4},executed:{team_a:4,team_b:4,team_c:0},promises:{team_c:4}};
 const h=await shellHarness({initialLife:commons(freshGuide(steps.results,{result}))});
 assert.match(h.node('#observatory-stage').innerHTML,/id="last-round-result"/);
 h.node('#last-round-result').open=false;await h.clickData({guideAction:'results'});
 assert.equal(h.node('#last-round-result').open,true);
 assert.equal(posts(h).filter(r=>/\/(confirm|advance|observe)$/.test(r.url)).length,0);
});
