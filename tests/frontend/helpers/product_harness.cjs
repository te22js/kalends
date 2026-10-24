'use strict';
const assert=require('node:assert/strict');
async function shellHarness({path='/lives/life_a',storedView=null,initialLife=null,initialCatalog=null,responder=null,initialStored=[]}={}) {
  const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(require('node:path').resolve(__dirname,'../../../kalends/experience_os/static/product/app.js'),'utf8');
  const nodes=new Map(),created=[],windowEvents=new Map(),documentEvents=new Map(),requests=[],messages=[],timers=new Map(),stored=new Map(initialStored);
  let serial=0,now=0,isFocused=true;
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
  const node=selector=>{if(!nodes.has(selector)){const id=selector.startsWith('#')?selector.slice(1):'',tag=['review-dialog','evidence-dialog','time-dialog','world-menu','help-dialog','notebook-dialog'].includes(id)?'dialog':['story-button','close-story','confirm-choice'].includes(id)?'button':'div';nodes.set(selector,new Element(tag,id));}return nodes.get(selector);};
  const document={hidden:false,hasFocus:()=>isFocused,title:'',activeElement:null,body:new Element('body'),
    querySelector(selector){if(selector==='dialog[open]')return [...nodes.values()].find(n=>n.tagName==='DIALOG'&&n.open)||null;return node(selector);},
    querySelectorAll(selector){if(selector==='dialog[open]')return [...nodes.values()].filter(n=>n.tagName==='DIALOG'&&n.open);if(selector==='#observatory-stage input[name],#observatory-stage select[name]')return [...nodes.values()].filter(n=>n.name);return [];},
    createElement(tag){const element=new Element(tag);if(tag==='iframe'){element.contentWindow={postMessage:(data,origin)=>messages.push({frame:element,data:JSON.parse(JSON.stringify(data)),origin})};element.contentDocument={events:new Map(),addEventListener(type,fn){if(!this.events.has(type))this.events.set(type,[]);this.events.get(type).push(fn);}};}created.push(element);return element;},
    getElementById:id=>node('#'+id),addEventListener(type,fn){if(!documentEvents.has(type))documentEvents.set(type,[]);documentEvents.get(type).push(fn);}};
  for(const id of ['story-drawer','story-backdrop','life-shell','life-loading','world-notice'])node('#'+id).hidden=true;
  const location={};function setLocation(next){const url=new URL(next,'http://127.0.0.1:8810');Object.assign(location,{href:url.href,origin:url.origin,pathname:url.pathname,search:url.search,hash:url.hash});}setLocation(path);
  const life={life:{id:'life_a',title:'A personal Pompeii life',template_id:'pompeii_life',participant:'Aelia',minute:0,revision:0,save_status:'saved'},
    snapshot:{experience:'life_a',setting:'pompeii',minute:0,command_count:0,terminated:false},people:[],history:{revision:0,chapters:[],beats:[],people:[],known_commitments:[]},
    time:{known_stops:[]},telemetry:{opt_in:false,meaningful_revision:0},return_summary:{changes:[],text:'Paused at a saved moment.'}};
  if(initialLife)Object.assign(life,initialLife);
  const catalog={templates:[{id:'pompeii_life',title:'Pompeii'}],lives:[life.life],examples:[],failures:[]};
  if(initialCatalog)Object.assign(catalog,initialCatalog);
  if(storedView)stored.set('kalends:scene:life_a',JSON.stringify(storedView));
  const window={location,addEventListener(type,fn){if(!windowEvents.has(type))windowEvents.set(type,[]);windowEvents.get(type).push(fn);}};
  const sandbox={window,document,location,URL,AbortController,crypto:{randomUUID:()=> 'local_session'},performance:{now:()=>now},Date:class extends Date{static now(){return 1700000000000+now;}},
    sessionStorage:{getItem:key=>stored.get(key)??null,setItem:(key,value)=>stored.set(key,String(value))},
    history:{pushState:(_state,_title,url)=>setLocation(url),replaceState:(_state,_title,url)=>setLocation(url)},
    setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),requestAnimationFrame:()=>++serial,scrollTo(){},
    fetch:async(url,options={})=>{const body=options.body?JSON.parse(options.body):null;requests.push({url,method:options.method||'GET',body});let result;
      const override=responder?await responder({url,body,options,life,catalog}):undefined;
      if(override!==undefined){const status=override.status||200;return {ok:status>=200&&status<300,status,json:async()=>JSON.parse(JSON.stringify(override.body))};}
      if(url==='/product/api/catalog')result=catalog;
      else if(url.startsWith('/product/api/life?'))result=life;
      else if(url==='/product/api/resume'||url==='/product/api/seen')result=life;
      else if(url==='/product/api/guide'){life.guide={...life.guide,...Object.fromEntries(['enabled','learn'].filter(key=>key in body).map(key=>[key,body[key]]))};if(body.card){const card=life.guide.history_cards?.find(card=>card.id===body.card);if(card)card.read=true;}result=life;}
      else if(url==='/product/api/telemetry'){if(typeof body.opt_in==='boolean')life.telemetry.opt_in=body.opt_in;result={recorded:!!body.event,opt_in:life.telemetry.opt_in};}
      else if(url==='/product/api/lab')result={life:life.life,snapshot:{lab:{truth:{secret:'PRIVATE_OPERATOR_RECORD'},minds:{},commands:[]}},operator_exposed:true};
      else throw Error('Unexpected fetch in shell harness: '+url);
      return {ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(result))};}};
  vm.createContext(sandbox);vm.runInContext(source,sandbox,{filename:'product/app.js'});
  async function settle(){for(let i=0;i<30;i++)await Promise.resolve();}
  async function click(element){const event={target:element,button:0,preventDefault(){}};for(const fn of documentEvents.get('click')||[])fn(event);await settle();}
  await settle();
  return {node,document,life,catalog,created,requests,messages,timers,stored,location,settle,
    advanceClock(ms){now+=ms;},
    events:()=>requests.filter(r=>r.url==='/product/api/telemetry'&&r.body.event).map(r=>r.body),
    async activity(type='input'){for(const fn of documentEvents.get(type)||[])fn({target:{value:'PRIVATE DRAFT',key:'PRIVATE KEY',closest(){return null;}},isTrusted:true});await settle();},
    async focus(value){isFocused=value;for(const fn of windowEvents.get(value?'focus':'blur')||[])fn({});await settle();},
    async change(id,values){const target=node('#'+id);Object.assign(target,values);for(const fn of documentEvents.get('change')||[])fn({target});await settle();},
    async inputAllocation(values){for(const [id,value] of Object.entries(values)){const input=node('#allocate-'+id);Object.assign(input,{name:id,value:String(value)});input.closest=selector=>selector==='#observatory-stage'?node('#observatory-stage'):null;}for(const fn of documentEvents.get('input')||[])fn({target:node('#allocate-team_a'),isTrusted:true});await settle();},
    async consent(value){const target=node('#telemetry-opt-in');target.checked=value;for(const fn of documentEvents.get('change')||[])fn({target});await settle();},
    async heartbeat(){const entry=[...timers].find(([,timer])=>timer.ms===15000);assert.ok(entry,'usage heartbeat exists');timers.delete(entry[0]);entry[1].fn();await settle();},
    async pagehide(){for(const fn of windowEvents.get('pagehide')||[])fn({});await settle();},
    async frameActivity(){const frame=created.find(n=>n.tagName==='IFRAME');for(const fn of frame.events.get('load')||[])fn({});for(const fn of frame.contentDocument.events.get('input')||[])fn({isTrusted:true,target:{value:'PRIVATE SCENE DRAFT'}});await settle();},
    frame:()=>created.find(n=>n.tagName==='IFRAME'),
    async scene(data){const frame=created.find(n=>n.tagName==='IFRAME');for(const fn of windowEvents.get('message')||[])fn({origin:location.origin,source:frame.contentWindow,data:{kind:'kalends:scene',life_id:'life_a',...data}});await settle();},
    async accepted(operation='action',accepted_revision=life.life.revision){const frame=created.find(n=>n.tagName==='IFRAME');for(const fn of windowEvents.get('message')||[])fn({origin:location.origin,source:frame.contentWindow,data:{kind:'kalends:accepted',experience:'life_a',operation,accepted_revision}});await settle();},
    async visible(value){document.hidden=!value;for(const fn of documentEvents.get('visibilitychange')||[])fn({});await settle();},
    async clickId(id){const element=node('#'+id);element.tagName='BUTTON';await click(element);},
    async clickData(data){const element=new Element('button');Object.assign(element.dataset,data);for(const [key,value] of Object.entries(data))element.setAttribute('data-'+key.replace(/[A-Z]/g,c=>'-'+c.toLowerCase()),value);await click(element);},
    async submitId(id){const element=node('#'+id),event={target:element,preventDefault(){}};for(const fn of documentEvents.get('submit')||[])fn(event);await settle();},
    async navigate(url){const a=new Element('a');const parsed=new URL(url,location.origin);Object.assign(a,{href:parsed.href,origin:parsed.origin,pathname:parsed.pathname,search:parsed.search,hash:parsed.hash,download:'',target:''});await click(a);},
    async enterLab(){const b=new Element('button');b.dataset.enterLab='life_a';await click(b);},
    async runRetry(){const entry=[...timers].find(([,timer])=>timer.ms>=100&&timer.ms<=1200);assert.ok(entry,'a bounded read-only retry is scheduled');timers.delete(entry[0]);entry[1].fn();await settle();},
  };
}



module.exports={shellHarness};
