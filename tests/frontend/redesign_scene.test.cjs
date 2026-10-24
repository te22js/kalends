'use strict';
// Actual shipped presentation and bridge; native WebGL/UI reviewed separately.
const test=require('node:test'),assert=require('node:assert/strict');
const path=require('node:path'),{pathToFileURL}=require('node:url');
const load=relative=>import(pathToFileURL(path.resolve(__dirname,'../../kalends_3d/'+relative)).href);
const snap=()=>({mode:'game',world:{minute:0,player:{id:'Player',x:800,y:415,location:'street',cash:6},agents:[],map:{locations:[]},journal:[]}});
const choice={id:'account',enabled:true,interaction:'observation',action:{action:'hear_dispute',recipient:'Sabina'}};
const context={speaker:'Sabina',revision:7,state_hash:'original-hash',choices:[choice],topics:[]};
test('conversation exposes only three contextual choices and keeps every other permitted choice in More',async()=>{
 const {conversationChoices}=await load('src/conversation_presenter.js');
 const choices=['talk','work','examine_receipt','support_market','hear_dispute','decline_dispute'].map(action=>({id:action,enabled:true,action:{action}}));
 const result=conversationChoices({choices},{player:{documents:[]}},'Sabina');
 assert.deepEqual(result.primary.map(q=>q.id),['hear_dispute','examine_receipt','support_market']);
 assert.equal(new Set([...result.primary,...result.more].map(q=>q.id)).size,choices.length);
 assert.equal(result.primary[0],choices[4]);
});
test('document card cannot reveal an unreceived account',async()=>{
 const {receivedDocuments}=await load('src/conversation_presenter.js');
 assert.deepEqual(receivedDocuments({player:{documents:[]}},'Sabina'),[]);
 const sabina={id:'market_receipt',text:'Her account'},dama={id:'household_tablet',text:'Their account'};
 assert.deepEqual(receivedDocuments({player:{documents:[sabina,dama]}},'Sabina'),[sabina]);
});
test('Pompeii time uses 08:00 origin and crosses midnight honestly',async()=>{
 const {pompeiiTime}=await load('src/conversation_presenter.js');
 assert.equal(pompeiiTime(0),'Day 1 · 08:00');assert.equal(pompeiiTime(960),'Day 2 · 00:00');assert.equal(pompeiiTime(1440),'Day 2 · 08:00');
});
test('direct observation refuses an unmarked or disabled choice without issuing a request',async()=>{
 const {KalendsBridge}=await load('bridge.js');let requests=0;
 const bridge=new KalendsBridge({fetchImpl:async()=>{requests++;}});
 await assert.rejects(bridge.observe(context,{...choice,interaction:'review'}),/available question/);
 await assert.rejects(bridge.observe(context,{...choice,enabled:false}),/available question/);
 await assert.rejects(bridge.observe({...context,revision:undefined},choice),/situation changed/);
 assert.equal(requests,0);
});
test('duplicate observation clicks share one request and accepted receipt',async()=>{
 const {KalendsBridge}=await load('bridge.js');let release;const gate=new Promise(resolve=>release=resolve),requests=[];
 const bridge=new KalendsBridge({fetchImpl:async(url,options)=>{requests.push({url,body:JSON.parse(options.body)});await gate;return{ok:true,status:200,json:async()=>({...snap(),outcome:'accepted',receipt:{event_id:1,text:'Sabina told you her account.'},conversation:context})};}});
 const a=bridge.observe(context,choice),b=bridge.observe(context,choice);assert.equal(a,b);await new Promise(setImmediate);assert.equal(requests.length,1);
 release();const result=await a;assert.equal(result.receipt.event_id,1);assert.deepEqual(requests[0].body,{action:choice.action,expected_revision:7,expected_state_hash:'original-hash'});
});
test('lost observation response retries the original revision and hash, not a fresh question',async()=>{
 const {KalendsBridge}=await load('bridge.js');const requests=[];
 const bridge=new KalendsBridge({fetchImpl:async(url,options)=>{requests.push(JSON.parse(options.body));if(requests.length===1)throw new TypeError('Network lost');return{ok:true,status:200,json:async()=>({...snap(),outcome:'already_accepted',receipt:{event_id:9,text:'Existing account'}})};}});
 await assert.rejects(bridge.observe(context,choice),/Network lost/);assert.equal(bridge.observationUncertain,true);
 await assert.rejects(bridge.observe({...context,revision:8},choice),/previous question/);assert.equal(requests.length,1);
 const result=await bridge.retryObservation();assert.equal(result.outcome,'already_accepted');assert.deepEqual(requests[0],requests[1]);assert.equal(bridge.observationUncertain,false);
});
test('stale observation rejection releases uncertain state without a second request',async()=>{
 const {KalendsBridge}=await load('bridge.js');let requests=0;
 const bridge=new KalendsBridge({fetchImpl:async()=>{requests++;return{ok:false,status:409,json:async()=>({error:'The offer changed.',code:'observation_stale'})};}});
 await assert.rejects(bridge.observe(context,choice),error=>error.code==='observation_stale');
 assert.equal(requests,1);assert.equal(bridge.observationUncertain,false);await assert.rejects(bridge.retryObservation(),/no question/);
});
test('continuing opportunities use available nearby offers and known places without promising work',async()=>{
 const {continuingOptions}=await load('src/conversation_presenter.js');
 const world={story:{stage:'resolved'},player:{location:'street',commitments:[]},map:{locations:[{id:'fullery',name:'Fullonica of Stephanus'},{id:'thermopolium',name:'Food counter'}]},opportunities:[{enabled:false,title:'Unavailable work',action:{recipient:'Sabina'}},{enabled:true,title:'Discuss a replacement delivery',action:{recipient:'Lucius'}}]};
 assert.deepEqual(continuingOptions(world).map(q=>q.kind),['person','location']);assert.equal(continuingOptions(world)[0].recipient,'Lucius');assert.equal(continuingOptions(world)[1].location,'fullery');
 world.player.commitments=[{status:'open',title:'Two hours of service'}];assert.equal(continuingOptions(world)[0].kind,'journal');world.story.stage='unresolved';assert.deepEqual(continuingOptions(world),[]);
});
test('receipt projection keeps category needed to avoid duplicate document receipts while excluding private payload',async()=>{
 const {projectReceipt}=await load('bridge.js');
 assert.deepEqual(projectReceipt({event_id:9,tick:0,title:'You copied an order',payload:{category:'rb_evidence',private:'secret'}}),{event_id:9,title:'You copied an order',category:'rb_evidence',minute:0});
});
test('newly received document opens with its quantities/source and suppresses duplicate receipt text',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../kalends_3d/src/main.js'),'utf8');
 const helpers={...await load('src/conversation_presenter.js'),...await load('src/scene_guide.js')},nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{style:{}});return nodes.get(id);};
 const S={selected:'Sabina',line:'Here is the account you asked for.',newDocumentId:'market_receipt',receipt:{category:'rb_evidence',title:'You copied an account'},context:{greeting:'Hello',topics:[],choices:[]}};
 const world={player:{documents:[{id:'market_receipt',title:'Sabina’s order',text:'Two sacks ordered. Four coins advanced.',as_of:0}]}};
 const sandbox={S,$,all:()=>[],person:()=>({role:'Food seller'}),w:()=>world,bridge:{},textOf:v=>v?.text||v?.title||'',escapeHTML:v=>String(v??''),...helpers};vm.createContext(sandbox);
 vm.runInContext(source.slice(source.indexOf('function renderConversation('),source.indexOf('async function propose(')),sandbox);sandbox.renderConversation();
 assert.equal($('#conversation-receipt').hidden,true);assert.match($('#conversation-evidence').innerHTML,/<details open>/);assert.match($('#conversation-evidence').innerHTML,/Two sacks ordered\. Four coins advanced\./);assert.match($('#conversation-evidence').innerHTML,/Received from Sabina/);assert.match($('#conversation-evidence').innerHTML,/Account dated Day 1 · 08:00/);
 S.newDocumentId=null;sandbox.renderConversation();assert.doesNotMatch($('#conversation-evidence').innerHTML,/<details open>/);
});
test('an interrupted paid confirmation reconciles the same identity and blocks every new mutation',async()=>{
 const {KalendsBridge}=await load('bridge.js');let attempt=0;const requests=[],states=[];
 const bridge=new KalendsBridge({onState:s=>states.push(s),fetchImpl:async(url,options)=>{const body=JSON.parse(options.body);requests.push({url,body});if(url==='/api/propose')return{ok:true,json:async()=>({proposal_id:'paid-original',interpretations:[{id:'0'}]})};if(++attempt===1)throw new TypeError('Lost response');return{ok:true,json:async()=>({...snap(),world:{...snap().world,player:{...snap().world.player,cash:3}},outcome:'already_accepted',receipt:{event_id:11,text:'Existing delivery'}})};}});
 await bridge.propose('Sabina',{choice_id:'market'});await assert.rejects(bridge.confirm('paid-original'),/Lost response/);assert.equal(bridge.confirmationUncertain,true);
 await assert.rejects(bridge.move({x:900,y:415}),/previous/);await assert.rejects(bridge.propose('Sabina',{choice_id:'market'}),/previous/);await assert.rejects(bridge.observe(context,choice),/previous/);assert.equal(requests.length,2);
 const result=await bridge.retryConfirmation();assert.equal(result.outcome,'already_accepted');assert.deepEqual(requests[1],requests[2]);assert.equal(states.at(-1).world.player.cash,3);assert.equal(bridge.confirmationUncertain,false);
});
test('unknown confirmation after a restart stays uncertain and never creates a replacement proposal',async()=>{
 const {KalendsBridge}=await load('bridge.js');const requests=[];
 const bridge=new KalendsBridge({fetchImpl:async(url,options)=>{requests.push(url);return url==='/api/propose'?{ok:true,json:async()=>({proposal_id:'old',interpretations:[{id:'0'}]})}:{ok:false,status:409,json:async()=>({code:'outcome_unknown',error:'Check saved choices.'})};}});
 await bridge.propose('Sabina',{choice_id:'market'});await assert.rejects(bridge.confirm('old'),/Check saved/);assert.equal(bridge.confirmationUncertain,true);await assert.rejects(bridge.advance(1),/previous/);await assert.rejects(bridge.retryConfirmation(),/Check saved/);assert.deepEqual(requests,['/api/propose','/api/act','/api/act']);
});
