'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {LifeRequestGate,StaleRequest,acceptsSceneMessage,describeAction,escapeHTML} = require('../../kalends/experience_os/static/product/app.js');

function deferred() { let resolve, reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject}; }

test('a late life response cannot populate a different selected life',async()=>{
  const gate=new LifeRequestGate(),request=deferred();gate.select('life_a');let signal;
  const result=gate.run(s=>{signal=s;return request.promise;});gate.select('life_b');
  assert.equal(signal.aborted,true);request.resolve({id:'life_a',cash:7});
  await assert.rejects(result,StaleRequest);
  assert.equal(gate.id,'life_b');
});

test('leaving and returning to the same identity still invalidates the old request',async()=>{
  const gate=new LifeRequestGate(),request=deferred();gate.select('life_a');
  const result=gate.run(()=>request.promise);gate.select(null);gate.select('life_a');request.resolve('old revision');
  await assert.rejects(result,StaleRequest);
});

test('ordinary reconciliation of one life keeps active requests admitted',async()=>{
  const gate=new LifeRequestGate(),request=deferred();gate.select('life_a');let signal;
  const result=gate.run(s=>{signal=s;return request.promise;});gate.select('life_a');
  assert.equal(signal.aborted,false);request.resolve('current revision');assert.equal(await result,'current revision');
  assert.equal(gate.controllers.size,0);
});

test('an abort-ignoring failed request is still stale after a life change',async()=>{
  const gate=new LifeRequestGate(),request=deferred();gate.select('life_a');
  const result=gate.run(()=>request.promise);gate.select('life_b');request.reject(new Error('old failed network'));
  await assert.rejects(result,StaleRequest);
  assert.equal(gate.controllers.size,0);
});

test('scene messages require matching origin, frame window and explicit life',()=>{
  const source={},other={},frame={contentWindow:source},origin='http://127.0.0.1:8810';
  const event={origin,source,data:{kind:'kalends:scene',life_id:'life_a',status:'ready'}};
  assert.equal(acceptsSceneMessage(event,frame,origin,'life_a'),true);
  assert.equal(acceptsSceneMessage({...event,origin:'https://other.example'},frame,origin,'life_a'),false);
  assert.equal(acceptsSceneMessage({...event,source:other},frame,origin,'life_a'),false);
  assert.equal(acceptsSceneMessage(event,frame,origin,'life_b'),false);
  assert.equal(acceptsSceneMessage(event,null,origin,'life_a'),false);
  assert.equal(acceptsSceneMessage({...event,data:{experience:'life_a',kind:'kalends:accepted'}},frame,origin,'life_a'),true);
});

test('consequential choices are labelled without turning requested allocation into delivery',()=>{
  assert.equal(describeAction({action:'allocate',allocation:{team_a:4}}),'Commit the proposed allocation');
  assert.equal(describeAction({action:'commit',recipient:'team_c',quantity:3}),'Promise 3 units to Lin');
  assert.equal(describeAction({action:'share',recipient:'team_b'}),'Ask Mira to share a dated report');
});

test('world-provided text is escaped before insertion into shell markup',()=>{
  assert.equal(escapeHTML('<img src=x onerror="bad()">&'), '&lt;img src=x onerror=&quot;bad()&quot;&gt;&amp;');
  assert.equal(escapeHTML(undefined),'');
});

test('the life revision gate rejects late committed state and keeps identities separate',()=>{
  const {LifeRevisionGate}=require('../../kalends/experience_os/static/product/app.js'),gate=new LifeRevisionGate();
  assert.equal(gate.admit('a',{life:{revision:3}}),true);
  assert.equal(gate.admit('a',{life:{revision:2}}),false);
  assert.equal(gate.admit('b',{snapshot:{command_count:0}}),true);
  assert.equal(gate.admit('a',{life:{revision:true}}),false);
  assert.equal(gate.admit('a',{life:{revision:3}}),true);
});

/* Run the actual shell against a deliberately small DOM/fetch boundary. This
 * checks routing, node identity and message handling; it does not emulate CSS,
 * native browser focus behavior or WebGL performance. */
async function shellHarness({path='/lives/life_a',storedView=null,initialLife=null,initialCatalog=null,responder=null}={}) {
  const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(require('node:path').resolve(__dirname,'../../kalends/experience_os/static/product/app.js'),'utf8');
  const nodes=new Map(),created=[],windowEvents=new Map(),documentEvents=new Map(),requests=[],messages=[],timers=new Map(),stored=new Map();
  let serial=0;
  class Element {
    constructor(tag='div',id=''){this.tagName=tag.toUpperCase();this.id=id;this.dataset={};this.hidden=false;this.open=false;this.children=[];this.attributes={};this.innerHTML='';this.textContent='';this.disabled=false;this.isConnected=true;this.events=new Map();this.classList={add(){},remove(){},toggle(){}};}
    addEventListener(type,fn){if(!this.events.has(type))this.events.set(type,[]);this.events.get(type).push(fn);}
    setAttribute(name,value){this.attributes[name]=String(value);}
    getAttribute(name){return this.attributes[name]??null;}
    hasAttribute(name){return name in this.attributes;}
    append(...children){for(const child of children){child.parentElement=this;this.children.push(child);}}
    replaceChildren(...children){this.children=[];this.innerHTML='';this.append(...children);}
    focus(){document.activeElement=this;}
    closest(selector){if(selector==='button')return this.tagName==='BUTTON'?this:null;if(selector==='a[href]')return this.tagName==='A'?this:null;if(selector==='dialog')return this.tagName==='DIALOG'?this:this.parentElement?.closest(selector);return null;}
    querySelector(){return null;}
    querySelectorAll(){return [];}
    showModal(){this.open=true;}
    close(){if(!this.open)return;this.open=false;for(const fn of this.events.get('close')||[])fn({target:this});}
    getClientRects(){return this.hidden?[]:[{}];}
    scrollIntoView(){}
  }
  const node=selector=>{if(!nodes.has(selector)){const id=selector.startsWith('#')?selector.slice(1):'',tag=['review-dialog','evidence-dialog','time-dialog','world-menu'].includes(id)?'dialog':['story-button','close-story','confirm-choice'].includes(id)?'button':'div';nodes.set(selector,new Element(tag,id));}return nodes.get(selector);};
  const document={hidden:false,title:'',activeElement:null,body:new Element('body'),
    querySelector(selector){if(selector==='dialog[open]')return [...nodes.values()].find(n=>n.tagName==='DIALOG'&&n.open)||null;return node(selector);},
    querySelectorAll(selector){if(selector==='dialog[open]')return [...nodes.values()].filter(n=>n.tagName==='DIALOG'&&n.open);return [];},
    createElement(tag){const element=new Element(tag);if(tag==='iframe')element.contentWindow={postMessage:(data,origin)=>messages.push({frame:element,data:JSON.parse(JSON.stringify(data)),origin})};created.push(element);return element;},
    getElementById:id=>node('#'+id),addEventListener(type,fn){if(!documentEvents.has(type))documentEvents.set(type,[]);documentEvents.get(type).push(fn);}};
  for(const id of ['story-drawer','story-backdrop','life-shell','life-loading','world-notice'])node('#'+id).hidden=true;
  const location={};function setLocation(next){const url=new URL(next,'http://127.0.0.1:8810');Object.assign(location,{href:url.href,origin:url.origin,pathname:url.pathname,search:url.search,hash:url.hash});}setLocation(path);
  const life={life:{id:'life_a',title:'A personal Pompeii life',template_id:'pompeii_life',participant:'Aelia',minute:0,revision:0,save_status:'saved'},
    snapshot:{experience:'life_a',setting:'pompeii',minute:0,command_count:0,terminated:false},people:[],history:{revision:0,chapters:[],beats:[],people:[],known_commitments:[]},
    time:{known_stops:[]},telemetry:{opt_in:false},return_summary:{changes:[],text:'Paused at a saved moment.'}};
  if(initialLife)Object.assign(life,initialLife);
  const catalog={templates:[{id:'pompeii_life',title:'Pompeii'}],lives:[life.life],examples:[],failures:[]};
  if(initialCatalog)Object.assign(catalog,initialCatalog);
  if(storedView)stored.set('kalends:scene:life_a',JSON.stringify(storedView));
  const window={location,addEventListener(type,fn){if(!windowEvents.has(type))windowEvents.set(type,[]);windowEvents.get(type).push(fn);}};
  const sandbox={window,document,location,URL,AbortController,crypto:{randomUUID:()=> 'local_session'},performance:{now:()=>1},
    sessionStorage:{getItem:key=>stored.get(key)??null,setItem:(key,value)=>stored.set(key,String(value))},
    history:{pushState:(_state,_title,url)=>setLocation(url),replaceState:(_state,_title,url)=>setLocation(url)},
    setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),requestAnimationFrame:()=>++serial,scrollTo(){},
    fetch:async(url,options={})=>{const body=options.body?JSON.parse(options.body):null;requests.push({url,method:options.method||'GET',body});let result;
      const override=responder?await responder({url,body,options,life,catalog}):undefined;
      if(override!==undefined){const status=override.status||200;return {ok:status>=200&&status<300,status,json:async()=>JSON.parse(JSON.stringify(override.body))};}
      if(url==='/product/api/catalog')result=catalog;
      else if(url.startsWith('/product/api/life?'))result=life;
      else if(url==='/product/api/resume'||url==='/product/api/seen')result=life;
      else if(url==='/product/api/lab')result={life:life.life,snapshot:{lab:{truth:{secret:'PRIVATE_OPERATOR_RECORD'},minds:{},commands:[]}},operator_exposed:true};
      else throw Error('Unexpected fetch in shell harness: '+url);
      return {ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(result))};}};
  vm.createContext(sandbox);vm.runInContext(source,sandbox,{filename:'product/app.js'});
  async function settle(){for(let i=0;i<30;i++)await Promise.resolve();}
  async function click(element){const event={target:element,button:0,preventDefault(){}};for(const fn of documentEvents.get('click')||[])fn(event);await settle();}
  await settle();
  return {node,document,life,catalog,created,requests,messages,timers,stored,location,settle,
    frame:()=>created.find(n=>n.tagName==='IFRAME'),
    async scene(data){const frame=created.find(n=>n.tagName==='IFRAME');for(const fn of windowEvents.get('message')||[])fn({origin:location.origin,source:frame.contentWindow,data:{kind:'kalends:scene',life_id:'life_a',...data}});await settle();},
    async accepted(){const frame=created.find(n=>n.tagName==='IFRAME');for(const fn of windowEvents.get('message')||[])fn({origin:location.origin,source:frame.contentWindow,data:{kind:'kalends:accepted',experience:'life_a'}});await settle();},
    async visible(value){document.hidden=!value;for(const fn of documentEvents.get('visibilitychange')||[])fn({});await settle();},
    async clickId(id){const element=node('#'+id);element.tagName='BUTTON';await click(element);},
    async clickData(data){const element=new Element('button');Object.assign(element.dataset,data);await click(element);},
    async submitId(id){const element=node('#'+id),event={target:element,preventDefault(){}};for(const fn of documentEvents.get('submit')||[])fn(event);await settle();},
    async navigate(url){const a=new Element('a');const parsed=new URL(url,location.origin);Object.assign(a,{href:parsed.href,origin:parsed.origin,pathname:parsed.pathname,search:parsed.search,hash:parsed.hash,download:'',target:''});await click(a);},
    async enterLab(){const b=new Element('button');b.dataset.enterLab='life_a';await click(b);},
    async runRetry(){const entry=[...timers].find(([,timer])=>timer.ms>=100&&timer.ms<=1200);assert.ok(entry,'a bounded read-only retry is scheduled');timers.delete(entry[0]);entry[1].fn();await settle();},
  };
}

test('actual shell keeps the same iframe through accepted reconciliation and a history return',async()=>{
  const h=await shellHarness(),frame=h.frame();assert.ok(frame);const source=frame.src;
  await h.scene({status:'ready',request_id:'ready',view:{started:false,draft:''}});
  h.life.life.revision=1;h.life.snapshot.command_count=1;await h.accepted();
  await h.clickId('story-button');assert.equal(h.node('#story-drawer').hidden,false);
  assert.equal(h.node('.world-header').inert,true);await h.clickId('close-story');
  assert.equal(h.node('#story-drawer').hidden,true);assert.equal(h.node('.world-header').inert,false);
  assert.equal(h.created.filter(n=>n.tagName==='IFRAME').length,1);assert.equal(h.frame(),frame);assert.equal(frame.src,source);
  assert.ok(h.messages.some(m=>m.data.action==='pause'));assert.ok(h.messages.some(m=>m.data.action==='refresh'));
});

test('actual visibility handler unhides the active frame after returning to the tab',async()=>{
  const h=await shellHarness();await h.scene({status:'ready',request_id:'ready',view:{started:false}});
  const wrapper=h.frame().parentElement;await h.visible(false);assert.equal(wrapper.hidden,true);
  await h.visible(true);assert.equal(wrapper.hidden,false);assert.equal(h.messages.at(-1).data.action,'refresh');
});

test('actual ready handler restores the cached draft instead of overwriting it with boot defaults',async()=>{
  const saved={started:true,recipient:'Sabina',draft:'Keep my latest draft',cameraYaw:41,cameraDistance:18,follow:false};
  const h=await shellHarness({storedView:saved});await h.scene({status:'ready',request_id:'ready',view:{started:false,draft:'',cameraYaw:24}});
  const request=h.messages.at(-1).data;assert.equal(request.action,'restore');assert.equal(request.view.draft,saved.draft);
  assert.equal(request.view.cameraYaw,41);assert.equal(JSON.parse(h.stored.get('kalends:scene:life_a')).draft,saved.draft);
});

test('actual pending scene handler retries only the requested read and never a world mutation',async()=>{
  const h=await shellHarness();await h.scene({status:'ready',request_id:'ready',view:{started:false}});
  const first=h.messages.at(-1).data,fetches=h.requests.length;
  await h.scene({status:'pending',request_id:first.request_id});await h.runRetry();
  const retried=h.messages.at(-1).data;assert.equal(retried.action,'refresh');assert.notEqual(retried.request_id,first.request_id);
  assert.equal(h.requests.length,fetches);assert.equal(h.requests.some(r=>/confirm|advance|propose/.test(r.url)),false);
});

test('actual route removes the operator JSON DOM when returning to a participant life',async()=>{
  const h=await shellHarness({path:'/lab/life_a'});await h.enterLab();
  assert.match(h.node('#main').innerHTML,/PRIVATE_OPERATOR_RECORD/);
  await h.navigate('/lives/life_a');assert.equal(h.node('#main').innerHTML,'');
  assert.equal(h.node('#public-shell').hidden,true);assert.equal(h.node('#life-shell').hidden,false);
});


test('actual saved-world cards preserve incompatible journals without inventing a participant or clock',async()=>{
  const h=await shellHarness({path:'/your-worlds',initialCatalog:{lives:[],examples:[],failures:[{id:'pompeii_unreadable',title:'Old local journal',save_status:'incompatible_version',error:'Unsupported journal version 999; original preserved.'}]}});
  const markup=h.node('#main').innerHTML;
  assert.match(markup,/Preserved local journal/);assert.doesNotMatch(markup,/Day 1|00:00|Aelia|Consortium coordinator/);
  await h.clickData({saveDiagnostic:'pompeii_unreadable'});
  assert.equal(h.node('#global-status').textContent,'Unsupported journal version 999; original preserved.');
});

test('actual failed journal-write handler reports a rejected choice and preserved accepted history',async()=>{
  const h=await shellHarness({responder:({url})=>url==='/product/api/advance'?{status:400,body:{error:'[Errno 30] Read-only file system: private_path',save_failed:true}}:undefined});
  await h.clickData({advance:'1',mode:'compress'});
  assert.equal(h.node('#global-status').dataset.errorCode,'journal_save_failed');
  assert.match(h.node('#global-status').textContent,/journal could not be saved/);
  assert.match(h.node('#global-status').textContent,/choice was not accepted; your previously accepted history is preserved/);
  assert.doesNotMatch(h.node('#global-status').textContent,/private_path|Errno/);
  assert.equal(h.node('#world-saving').textContent,'Save error · Previous accepted history preserved');
  assert.doesNotMatch(h.node('#world-notice').innerHTML,/response was interrupted|server may have accepted/);
  assert.equal(h.requests.filter(r=>r.url==='/product/api/advance').length,1);
});

test('actual accepted-action handlers keep metadata warnings after successful callbacks and reconciliation',async()=>{
  const warning='World choice saved; display metadata could not be updated.';
  const h=await shellHarness({responder:({url,life})=>{
    if(url==='/product/api/propose')return {body:{proposal_id:'review_1',action:{action:'inspect'}}};
    if(url==='/product/api/confirm'){life.life.revision=1;life.life.metadata_warning=warning;life.snapshot.command_count=1;return {body:{...life,metadata_warning:warning,receipt:{accepted:true}}};}
  }});
  await h.clickData({action:'inspect'});assert.equal(h.node('#review-dialog').open,true);
  await h.clickId('confirm-choice');
  assert.equal(h.node('#review-dialog').open,false);
  assert.match(h.node('#global-status').textContent,/World choice saved; display metadata could not be updated/);
  assert.equal(h.node('#world-saving').textContent,'World saved · Display metadata needs attention');
  assert.equal(h.requests.filter(r=>r.url==='/product/api/confirm').length,1);
});

test('actual scene reconciliation exposes metadata failure without repeating the accepted world action',async()=>{
  const h=await shellHarness();h.life.life.metadata_warning='World choice saved; display metadata could not be updated.';
  h.life.life.revision=1;h.life.snapshot.command_count=1;await h.accepted();
  assert.match(h.node('#global-status').textContent,/display metadata could not be updated/);
  assert.equal(h.node('#world-saving').textContent,'World saved · Display metadata needs attention');
  assert.equal(h.requests.filter(r=>r.method==='POST'&&!r.url.endsWith('/resume')).length,0);
});

test('actual new-life handler carries the saved-journal metadata warning into the life route',async()=>{
  const warning='New life journal saved; display metadata could not be updated.';
  const h=await shellHarness({path:'/worlds/pompeii_life',responder:({url,life})=>{
    if(url==='/product/api/start'){life.life.metadata_warning=warning;return {body:{...life,metadata_warning:warning}};}
  }});
  await h.clickData({start:'pompeii_life'});await h.settle();
  assert.equal(h.location.pathname,'/lives/life_a');
  assert.match(h.node('#global-status').textContent,/New life journal saved; display metadata could not be updated/);
  assert.equal(h.node('#world-saving').textContent,'World saved · Display metadata needs attention');
  assert.equal(h.requests.filter(r=>r.url==='/product/api/start').length,1);
});

test('actual Studio uses backend-supported ranges and carries compile metadata warnings into the new life',async()=>{
  const warning='New life journal saved; display metadata could not be updated.';
  const h=await shellHarness({path:'/studio',responder:({url,life})=>{
    if(url==='/product/api/studio/compile'){life.life.metadata_warning=warning;return {body:{...life,metadata_warning:warning}};}
  }});
  await h.clickId('open-studio');
  const markup=h.node('#main').innerHTML;
  assert.match(markup,/maxlength="90"/);assert.match(markup,/name="seed"[^>]*max="1000000"/);assert.match(markup,/name="horizon_days"[^>]*max="90"/);
  const form=h.node('#studio-form');form.reportValidity=()=>true;form.elements={template_id:{value:'pompeii_life'},title:{value:'Authored life'},seed:{value:'17'},horizon_days:{value:'30'}};
  await h.submitId('studio-form');await h.settle();
  assert.equal(h.location.pathname,'/lives/life_a');
  assert.match(h.node('#global-status').textContent,/New life journal saved; display metadata could not be updated/);
  assert.equal(h.node('#world-saving').textContent,'World saved · Display metadata needs attention');
  assert.equal(h.requests.filter(r=>r.url==='/product/api/studio/compile').length,1);
});
