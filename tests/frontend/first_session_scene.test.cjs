'use strict';
// Shipped guide and renderer behavior. These are protocol/state checks, not
// browser interaction, visual QA, human comprehension or assistive-tech tests.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const modulePromise=import(pathToFileURL(path.resolve(__dirname,'../../kalends_3d/src/scene_guide.js')).href);
const world={minute:20,nearby:['Sabina'],agents:[{id:'Sabina',x:750,y:435},{id:'Dama',x:710,y:936}],
  map:{locations:[{id:'street',name:'Street'},{id:'thermopolium',name:'Food counter',door:{x:1225,y:480}}]},
  player:{commitments:[{id:'delivery',title:'Deliver flour',status:'open',deadline:40},{id:'old',status:'fulfilled',deadline:25}]},
  story:{stage:'committed',deadline:360}};

async function hostHarness(){const {installSceneGuideHost}=await modulePromise,events=new Map(),received=[],messages=[],actions=[];
 const parent={postMessage:(data,origin)=>messages.push({data,origin})};
 const host={parent,location:{origin:'http://localhost:8817',href:'http://localhost:8817/immersion/?experience=first_life'},
  addEventListener:(type,fn)=>events.set(type,fn),removeEventListener:type=>events.delete(type)};
 const guide=installSceneGuideHost({windowObject:host,onGuide:value=>received.push(value),onAction:value=>actions.push(value)});
 const receive=(data={},override={})=>events.get('message')({origin:host.location.origin,source:parent,
  data:{kind:'kalends:guide',life_id:'first_life',guide:{enabled:true,step:{id:'p1',body:'Find Sabina.'}},...data},...override});
 return {guide,host,events,messages,received,actions,receive};}

test('guide comes only from the same-origin parent for this exact life',async()=>{const h=await hostHarness();
 h.receive({}, {origin:'https://other.example'});h.receive({}, {source:{}});h.receive({life_id:'second_life'});h.receive({kind:'kalends:host'});
 assert.equal(h.received.length,0);h.receive();assert.equal(h.received[0].step.body,'Find Sabina.');h.guide.destroy();assert.equal(h.events.size,0);
});
test('only a same-origin parent primary intent can invoke the guide action; updates never invoke it',async()=>{const h=await hostHarness();
 h.receive();assert.deepEqual(h.actions,[]);
 h.receive({kind:'kalends:guide-action',action:'primary'},{origin:'https://other.example'});
 h.receive({kind:'kalends:guide-action',action:'primary'},{source:{}});
 h.receive({kind:'kalends:guide-action',action:'primary',life_id:'second_life'});
 h.receive({kind:'kalends:guide-action',action:'pay'});assert.deepEqual(h.actions,[]);
 h.receive({kind:'kalends:guide-action',action:'primary',payload:{action:'pay',recipient:'private_actor'}});assert.deepEqual(h.actions,['primary']);assert.equal(h.received.length,1);
});
test('the Help scene button closes Help and sends display state before its one explicit primary intent',async()=>{
 const {shellHarness}=require('./helpers/product_harness.cjs');
 const guide={version:'first-session-v1',enabled:true,step:{id:'p5',title:'Seek another account.',body:'Use a known meeting place.',action:{kind:'scene',label:'Seek another account'}},hint:{target:{type:'location',id:'household'}},known:{},chapters:[]};
 const h=await shellHarness({initialLife:{guide}});await h.clickId('help-button');const frame=h.frame();assert.equal(h.node('#help-dialog').open,true);
 assert.equal(h.messages.some(m=>m.data.kind==='kalends:guide-action'),false);await h.clickData({guideAction:'scene'});
 assert.equal(h.node('#help-dialog').open,false);assert.equal(h.frame(),frame);
 const relevant=h.messages.filter(m=>['kalends:guide','kalends:guide-action'].includes(m.data.kind));assert.equal(relevant.at(-2).data.kind,'kalends:guide');assert.equal(relevant.at(-1).data.kind,'kalends:guide-action');assert.deepEqual(JSON.parse(JSON.stringify(relevant.at(-1).data)),{kind:'kalends:guide-action',life_id:'life_a',action:'primary'});
 await h.scene({status:'ready'});assert.equal(h.messages.filter(m=>m.data.kind==='kalends:guide-action').length,1,'a later guide update cannot walk again');assert.equal(h.requests.some(r=>r.method==='POST'&&/\/(confirm|advance|act|move)$/.test(r.url)),false);
});
test('an explicit parent action reconciles a paused scene once, then honors pending-save protection',async()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8'),begin=source.indexOf('async function hostGuidePrimary('),end=source.indexOf('function prepareGuideNavigation(',begin),calls=[];
 let release;const read=new Promise(resolve=>release=resolve),S={hostPaused:true,transition:false};
 const bridge={pending:false,state:async()=>{calls.push('read current state');await read;}};
 const sandbox={S,bridge,toast:text=>calls.push(text),sceneVisibility:()=>{S.hostPaused=false;calls.push('resume presentation');},guideAction:async()=>calls.push('safe primary')};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);const intent=sandbox.hostGuidePrimary();assert.equal(S.transition,true);assert.deepEqual(calls,['resume presentation','read current state']);
 await sandbox.hostGuidePrimary();assert.match(calls.at(-1),/still being saved/);release();await intent;assert.equal(S.transition,false);assert.equal(calls.filter(c=>c==='safe primary').length,1);
 bridge.pending=true;await sandbox.hostGuidePrimary();assert.equal(calls.filter(c=>c==='safe primary').length,1);assert.match(calls.at(-1),/still being saved/);
});
test('guide presentation drops private fields and oversized strings',async()=>{const {guideView}=await modulePromise;
 const projected=guideView({enabled:true,private:'secret',step:{title:'x'.repeat(300),body:'Read the account.',action:{kind:'scene',action:'pay',cash:999}},hint:{target:{type:'person',id:'Sabina',private:'secret'}}});
 assert.equal(projected.step.title.length,180);assert.equal(JSON.stringify(projected).includes('secret'),false);assert.equal('cash' in projected.step.action,false);
});
test('help requests are metadata messages, never action, payment or proposal commands',async()=>{const h=await hostHarness();
 for(const action of ['help','history','toggle','resume','begin','hint'])assert.equal(h.guide.request(action,{card_id:'H1',location:'thermopolium',cash:0,proposal_id:'untrusted'}),true);
 assert.equal(h.guide.request('confirm'),false);assert.equal(h.messages.length,6);
 assert.ok(h.messages.every(m=>m.data.life_id==='first_life'&&m.data.kind==='kalends:guide-request'&&m.origin==='http://localhost:8817'));
 assert.equal(JSON.stringify(h.messages).includes('proposal'),false);
});
test('a nearby authoritative endpoint still needs rendered interaction range',async()=>{const {knownGuideTarget}=await modulePromise,guide={hint:{target:{type:'person',id:'Sabina'}}};
 assert.equal(knownGuideTarget(guide,world,()=>false),null);assert.deepEqual(knownGuideTarget(guide,world,()=>true),{type:'person',id:'Sabina'});
 assert.equal(knownGuideTarget({hint:{target:{type:'person',id:'Dama'}}},world,()=>true),null);
});
test('a stale contact hint preserves the admitted meeting point instead of tracking their latest coordinates',async()=>{const {guideView,knownGuideTarget}=await modulePromise;
 const guide=guideView({hint:{target:{type:'location',id:'street',x:850,y:430,at:0,person:'Dama'}}}),target=knownGuideTarget(guide,world);
 assert.deepEqual(target,{type:'location',id:'street',x:850,y:430,at:0,person:'Dama'});
 assert.notEqual(target.x,world.agents[1].x);assert.equal(knownGuideTarget({hint:{target:{type:'location',id:'private-room'}}},world),null);
});
test('the canonical street floor admits a public meeting point even though map.locations lists only named places',async()=>{
 const {guideView,knownGuideTarget}=await modulePromise,sample={...world,map:{locations:world.map.locations.filter(p=>p.id!=='street'),streets:[{x:0,y:350,w:1600,h:130,name:'Via dell’Abbondanza'}]}};
 const guide=guideView({hint:{target:{type:'location',id:'street',x:850,y:430,person:'Dama',basis:'public opening cart meeting point'}}});
 assert.deepEqual(knownGuideTarget(guide,sample),{type:'location',id:'street',x:850,y:430,person:'Dama',basis:'public opening cart meeting point'});
 assert.equal('at' in knownGuideTarget(guide,sample),false);assert.notEqual(knownGuideTarget(guide,sample).x,sample.agents[1].x);
 assert.equal(knownGuideTarget({hint:{target:{type:'location',id:'street',x:850,y:800}}},sample),null,'an arbitrary point outside the declared street is not admitted');
 assert.equal(knownGuideTarget({hint:{target:{type:'location',id:'private-room',x:850,y:430}}},sample),null);
});
test('an undated public street point never renders as a last sighting or an undefined timestamp',async()=>{
 const {guideView,knownGuideTarget}=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8'),begin=source.indexOf('function guidePlace('),end=source.indexOf('const sceneGuide=',begin),node={};
 const sample={...world,map:{locations:world.map.locations.filter(p=>p.id!=='street'),streets:[{x:0,y:350,w:1600,h:130}]}};
 const S={guide:guideView({enabled:true,step:{action:{kind:'scene',label:'Seek another account'}},hint:{target:{type:'location',id:'street',x:850,y:430,person:'Dama',basis:'public opening cart meeting point'}}}),renderer:{currentScene:'thermopolium',player:{position:{x:1225,y:656}}}};
 const sandbox={S,$:()=>node,place:id=>sample.map.locations.find(p=>p.id===id),guideTarget:()=>knownGuideTarget(S.guide,sample),worldDistance:(a,b)=>Math.hypot(a.x-b.x,a.y-b.y)};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.renderGuideRange();assert.match(node.textContent,/Public meeting point for Dama/);assert.match(sandbox.guideActionText(),/Walk to the public street meeting point/);assert.doesNotMatch(node.textContent,/last.seen|undefined|world minute/i);
 S.renderer.player.position={x:850,y:430};sandbox.renderGuideRange();assert.match(node.textContent,/You reached the public meeting point/);assert.doesNotMatch(node.textContent,/undefined|world minute/);
 S.guide.hint.target.at=0;sandbox.renderGuideRange();assert.match(node.textContent,/last-seen point/);assert.match(node.textContent,/world minute 0/);
});
test('activity describes accepted movement and public work without inventing deliveries',async()=>{const {sceneActivity}=await modulePromise;
 assert.equal(sceneActivity({activity:'working at the food counter'}),'Working at the food counter');
 assert.equal(sceneActivity({activity:'carrying household instructions'},{moving:true}),'Walking · recorded movement');
 assert.equal(sceneActivity({activity:'secret report'},{talking:true}),'In conversation');assert.equal(sceneActivity({}),'At this place');
});
test('an owner-held order cannot be read as a topic before a legitimate copy is received',async()=>{const {admittedTopics}=await modulePromise;
 const context={topics:[{id:'role',text:'I run the counter.'},{id:'market_receipt',text:'Private order: two units.'},{id:'household_tablet',text:'Private household order.'}]};
 assert.deepEqual(admittedTopics(context,{player:{documents:[]}}).map(t=>t.id),['role']);
 assert.deepEqual(admittedTopics(context,{player:{documents:[{id:'market_receipt'}]}}).map(t=>t.id),['role','market_receipt']);
});
test('time review includes actual open commitments and a crossed public dispute deadline',async()=>{const {timeReview}=await modulePromise;
 assert.deepEqual(timeReview(world,30),{from:20,to:50,minutes:30,known:[{at:40,title:'Deliver flour'}]});
 assert.deepEqual(timeReview(world,400).known.map(q=>q.at),[40,360]);assert.equal(timeReview(world,10).known.length,0);
 assert.equal(world.minute,20,'review is a read and cannot advance time');
});
test('guided introduction prevents Live even if a former timer tries to resume',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function setLive('),end=source.indexOf('function applyPreferences(',begin),button={setAttribute(){}};
 const sandbox={S:{guide:{enabled:true},liveEpoch:0},$:()=>button,setTimeout(){throw Error('Guide must not schedule automatic time');},clearTimeout(){}};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.setLive(true);assert.equal(sandbox.S.live,false);assert.equal(button.textContent,'Live');
});
test('the actual scene action walks only to an admitted point and sends history to the participant notebook',async()=>{
 const {knownGuideTarget}=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function prepareGuideNavigation('),end=source.indexOf('function renderContext(',begin),walks=[],requests=[],messages=[];
 const S={guide:{enabled:true,step:{action:{kind:'scene'}},hint:{target:{type:'location',id:'street',x:850,y:430,at:0,person:'Dama'}}},renderer:{currentScene:'street'}};
 const sandbox={S,bridge:{pending:false},w:()=>world,guideTarget:()=>knownGuideTarget(S.guide,world,()=>false),closeDialog(){},
  go:body=>walks.push(body),openDialog:id=>messages.push(id),toast:text=>messages.push(text),approach:()=>assert.fail('Unseen actor must not be approached'),
  sceneGuide:{request:(...args)=>requests.push(args)}};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);await sandbox.guideAction();
 assert.deepEqual(JSON.parse(JSON.stringify(walks)),[{location:'street',x:850,y:430}]);
 S.guide.hint.target={type:'person',id:'Dama'};await sandbox.guideAction();assert.equal(walks.length,1);assert.match(messages.at(-1),/not close enough/);
 S.guide.step.action={kind:'history',card_id:'food_counter'};await sandbox.guideAction();assert.deepEqual(JSON.parse(JSON.stringify(requests)),[['history',{card_id:'food_counter',location:'street'}]]);
 S.guide.step.action={kind:'ack'};await sandbox.guideAction();assert.equal(requests.at(-1)[0],'begin');assert.equal(walks.length,1);
});
test('explicit guide walking leaves the conversation safely and preserves the unsent draft',async()=>{
 const {knownGuideTarget}=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function prepareGuideNavigation('),end=source.indexOf('function renderContext(',begin),closeBegin=source.indexOf('function closeConversation('),closeEnd=source.indexOf('function renderConversation(',closeBegin),calls=[],elements=new Map();
 const $=id=>{if(!elements.has(id))elements.set(id,{value:'Unsent question for Sabina',focus(){}});return elements.get(id);};
 const S={selected:'Sabina',speechRecipient:'Sabina',conversationEpoch:3,proposal:{proposal_id:'unconfirmed'},renderer:{selected:'Sabina',currentScene:'street'},guide:{enabled:true,step:{action:{kind:'history',card_id:'food_counter'}},hint:{target:{type:'location',id:'thermopolium'}}}};
 const bridge={pending:false,cancelConversation:()=>calls.push('cancel review')};
 const sandbox={S,bridge,$,w:()=>world,guideTarget:()=>knownGuideTarget(S.guide,world,()=>false),closeDialog(){},
  go:body=>calls.push(['walk',body]),toast:text=>calls.push(text),renderContext(){},document:{body:{classList:{remove(){}}}},productHost:{notifyView:()=>calls.push('draft view saved')},sceneGuide:{request:()=>assert.fail('Walking must not confirm or save history')}};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end)+source.slice(closeBegin,closeEnd),sandbox);await sandbox.guideAction();
 assert.equal(S.selected,null);assert.equal(S.proposal,null);assert.equal(S.speechRecipient,'Sabina');assert.equal($('#speech').value,'Unsent question for Sabina');assert.equal(S.conversationEpoch,4);
 assert.deepEqual(JSON.parse(JSON.stringify(calls.find(c=>Array.isArray(c)))),['walk',{location:'thermopolium'}]);assert.ok(calls.includes('cancel review'));assert.ok(calls.includes('draft view saved'));
});
test('a pending save blocks guide navigation and keeps its conversation and review intact',async()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8'),begin=source.indexOf('function prepareGuideNavigation('),end=source.indexOf('function renderContext(',begin),messages=[];
 const S={selected:'Sabina',proposal:{proposal_id:'saving'},renderer:{currentScene:'street'},guide:{enabled:true,step:{action:{kind:'history'}},hint:{target:{type:'location',id:'thermopolium'}}}};
 const sandbox={S,bridge:{pending:true},guideTarget:()=>S.guide.hint.target,toast:text=>messages.push(text),closeConversation:()=>assert.fail('Do not close during a save'),closeDialog:()=>assert.fail('Do not close during a save'),go:()=>assert.fail('Do not walk during a save'),sceneGuide:{request:()=>assert.fail('Do not send a hint during a save')}};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);await sandbox.guideAction();sandbox.showGuideWay();
 assert.equal(S.selected,'Sabina');assert.equal(S.proposal.proposal_id,'saving');assert.ok(messages.every(message=>/still being saved/.test(message)));
});
test('the marker hint closes only the local interaction and never walks or advances time',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8'),begin=source.indexOf('function prepareGuideNavigation('),end=source.indexOf('function renderContext(',begin),calls=[];
 const S={selected:'Sabina',renderer:{showTarget:(point,duration)=>calls.push(['marker',point,duration])}};
 const sandbox={S,bridge:{pending:false},guideTarget:()=>({type:'location',id:'thermopolium'}),guidePlace:()=>({name:'Food counter',door:{x:1225,y:480}}),closeConversation:()=>{S.selected=null;calls.push('close conversation');},closeDialog(){},sceneGuide:{request:action=>calls.push(action)},toast:text=>calls.push(text),go:()=>assert.fail('A marker hint cannot walk')};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.showGuideWay();assert.equal(S.selected,null);assert.ok(calls.some(c=>Array.isArray(c)&&c[0]==='marker'));assert.ok(calls.some(c=>typeof c==='string'&&c.includes('does not walk or advance time')));
});
test('the shipped conversation renders readable opening, topic questions and an explicit acceptance verb',async()=>{
 const helpers=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function renderConversation('),end=source.indexOf('async function propose(',begin),elements=new Map();
 const $=id=>{if(!elements.has(id))elements.set(id,{style:{}});return elements.get(id);};
 const S={selected:'Sabina',line:null,topic:null,context:{greeting:{text:'Six sacks, two buyers, and somehow my bowls are the ones left empty. I paid Marcus. Ask him what changed.'},topics:[{id:'role',label:'Your life here',text:'I run the counter.'}],choices:[{id:'support_market',enabled:true,label:'Help the market arrangement',description:'Pay the carrying charge and direct four flour units to Sabina and two to Felix.',cost:'3 coins · 20 minutes'},{id:'duplicate',enabled:true,label:'A repeated cost fixture',description:'1 coin',cost:'1 coin'}]},proposal:null};
 const sandbox={S,$,all:()=>[],person:()=>({role:'food seller'}),w:()=>world,bridge:{pending:false},textOf:value=>typeof value==='string'?value:value?.text||value?.title||'',escapeHTML:value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;'),...helpers};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.renderConversation();
 assert.equal($('#dialogue-line').textContent,'I paid Marcus for flour for my food counter. The household also has a claim on the cart. Hear our accounts before deciding whether to help.');
 assert.match($('#topics').innerHTML,/What is your work here\?/);
 assert.match($('#choices').innerHTML,/Pay the carrying charge and direct four flour units to Sabina and two to Felix\./);assert.match($('#choices').innerHTML,/Cost: 3 coins · 20 minutes\./);assert.equal(($('#choices').innerHTML.match(/1 coin/g)||[]).length,1,'an exact duplicate cost is rendered once');
 S.proposal={reply:null,interpretations:[{id:'zero',label:'Review the arrangement',action:{action:'support_market'},cost:'0 coins',consequence:'No delivery has been recorded yet.'}]};sandbox.renderConversation();
 assert.match($('#interpretations').innerHTML,/0 coins/);assert.match($('#interpretations').innerHTML,/Confirm arrangement/);assert.match($('#interpretations').innerHTML,/No delivery has been recorded yet/);
});
test('the shipped journal keeps zero delivery, singular quantities and missing optional values readable',async()=>{
 const helpers=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function renderJournal('),end=source.indexOf('function reviewAdvance(',begin),content={};
 const sample={...world,player:{cash:1,inventory:1,reputation:0,commitments:[{status:'open',quantity:0}]},counter_market:{contracts:[{buyer:'A very long buyer name',status:'open',quantity:1,delivered:0}]}};
 const sandbox={S:{tab:'bag'},$:()=>content,all:()=>[],w:()=>sample,escapeHTML:value=>String(value??''),textOf:value=>typeof value==='string'?value:value?.text||value?.title||'',...helpers};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.renderJournal();
 assert.match(content.innerHTML,/1 coin/);assert.doesNotMatch(content.innerHTML,/1 coins/);assert.match(content.innerHTML,/1 flour unit/);assert.doesNotMatch(content.innerHTML,/1 flour units/);
 assert.match(content.innerHTML,/0 of 1 flour unit delivered\./);assert.match(content.innerHTML,/Promised quantity: 0\./);assert.doesNotMatch(content.innerHTML,/undefined|\[object Object\]|\{"status"/);
});
test('arrival owns the guidance layer until the participant enters the scene',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function renderHUD('),end=source.indexOf('function guideTarget(',begin),lead={hidden:false},S={started:false};
 const sandbox={S,$:()=>lead,w:()=>null};vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);
 sandbox.renderHUD();assert.equal(lead.hidden,true);S.started=true;sandbox.renderHUD();assert.equal(lead.hidden,false);
 const html=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/index.html'),'utf8');assert.match(html,/<aside id="lead"[^>]* hidden>/);
});
test('the objective primary and Help remain before long copy in keyboard and reading order',()=>{
 const html=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/index.html'),'utf8'),css=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/style.css'),'utf8');
 assert.ok(html.indexOf('id="lead-action"')<html.indexOf('id="lead-copy"'));assert.ok(html.indexOf('id="guide-help"')<html.indexOf('id="lead-copy"'));
 assert.match(css,/#lead-actions\{position:sticky;top:0;[^}]*background:#243b2d/);
});
test('crowded scene labels retain every target while reserving the primary guide marker',async()=>{
 const {layoutSceneLabels}=await modulePromise,labels=[
  {id:'Sabina',x:754,y:342,width:190,height:60,priority:200},
  {id:'Dama',x:895,y:380,width:65,height:27,priority:50},
  {id:'Marcus',x:1028,y:405,width:68,height:27,priority:50},
  {id:'bakery',x:850,y:373,width:113,height:33,priority:10},
 ];
 const positions=layoutSceneLabels(labels,1280,643);assert.equal(positions.size,4);assert.deepEqual(positions.get('Sabina'),{x:754,y:342});
 const boxes=labels.map(label=>{const q=positions.get(label.id);return {left:q.x-label.width/2,right:q.x+label.width/2,top:q.y-label.height,bottom:q.y};});
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];assert.equal(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top,false,'all four labels remain separate');}
 assert.ok([...positions.values()].every(q=>q.x>=8&&q.x<=1272&&q.y>=8&&q.y<=635));
 const css=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/style.css'),'utf8');assert.match(css,/\.nameplate small\{display:none\}/);assert.match(css,/\.nameplate:focus-visible small\{display:block\}/);
});
