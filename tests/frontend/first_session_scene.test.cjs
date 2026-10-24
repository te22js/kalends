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

async function hostHarness(){const {installSceneGuideHost}=await modulePromise,events=new Map(),received=[],messages=[];
 const parent={postMessage:(data,origin)=>messages.push({data,origin})};
 const host={parent,location:{origin:'http://localhost:8817',href:'http://localhost:8817/immersion/?experience=first_life'},
  addEventListener:(type,fn)=>events.set(type,fn),removeEventListener:type=>events.delete(type)};
 const guide=installSceneGuideHost({windowObject:host,onGuide:value=>received.push(value)});
 const receive=(data={},override={})=>events.get('message')({origin:host.location.origin,source:parent,
  data:{kind:'kalends:guide',life_id:'first_life',guide:{enabled:true,step:{id:'p1',body:'Find Sabina.'}},...data},...override});
 return {guide,host,events,messages,received,receive};}

test('guide comes only from the same-origin parent for this exact life',async()=>{const h=await hostHarness();
 h.receive({}, {origin:'https://other.example'});h.receive({}, {source:{}});h.receive({life_id:'second_life'});h.receive({kind:'kalends:host'});
 assert.equal(h.received.length,0);h.receive();assert.equal(h.received[0].step.body,'Find Sabina.');h.guide.destroy();assert.equal(h.events.size,0);
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
 const begin=source.indexOf('async function guideAction('),end=source.indexOf('function renderContext(',begin),walks=[],requests=[],messages=[];
 const S={guide:{enabled:true,step:{action:{kind:'scene'}},hint:{target:{type:'location',id:'street',x:850,y:430,at:0,person:'Dama'}}},renderer:{currentScene:'street'}};
 const sandbox={S,w:()=>world,guideTarget:()=>knownGuideTarget(S.guide,world,()=>false),closeDialog(){},
  go:body=>walks.push(body),openDialog:id=>messages.push(id),toast:text=>messages.push(text),approach:()=>assert.fail('Unseen actor must not be approached'),
  sceneGuide:{request:(...args)=>requests.push(args)}};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);await sandbox.guideAction();
 assert.deepEqual(JSON.parse(JSON.stringify(walks)),[{location:'street',x:850,y:430}]);
 S.guide.hint.target={type:'person',id:'Dama'};await sandbox.guideAction();assert.equal(walks.length,1);assert.match(messages.at(-1),/not close enough/);
 S.guide.step.action={kind:'history',card_id:'food_counter'};await sandbox.guideAction();assert.deepEqual(JSON.parse(JSON.stringify(requests)),[['history',{card_id:'food_counter',location:'street'}]]);
 S.guide.step.action={kind:'ack'};await sandbox.guideAction();assert.equal(requests.at(-1)[0],'begin');assert.equal(walks.length,1);
});
test('the shipped conversation renders readable opening, topic questions and an explicit acceptance verb',async()=>{
 const helpers=await modulePromise,vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const begin=source.indexOf('function renderConversation('),end=source.indexOf('async function propose(',begin),elements=new Map();
 const $=id=>{if(!elements.has(id))elements.set(id,{style:{}});return elements.get(id);};
 const S={selected:'Sabina',line:null,topic:null,context:{greeting:{text:'Six sacks, two buyers, and somehow my bowls are the ones left empty. I paid Marcus. Ask him what changed.'},topics:[{id:'role',label:'Your life here',text:'I run the counter.'}],choices:[]},proposal:null};
 const sandbox={S,$,all:()=>[],person:()=>({role:'food seller'}),w:()=>world,bridge:{pending:false},textOf:value=>typeof value==='string'?value:value?.text||value?.title||'',escapeHTML:value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;'),...helpers};
 vm.createContext(sandbox);vm.runInContext(source.slice(begin,end),sandbox);sandbox.renderConversation();
 assert.equal($('#dialogue-line').textContent,'I paid Marcus for flour for my food counter. The household also has a claim on the cart. Hear our accounts before deciding whether to help.');
 assert.match($('#topics').innerHTML,/What is your work here\?/);
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
