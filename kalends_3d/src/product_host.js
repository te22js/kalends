/* Local UI continuity only. The host cannot invoke any world action here. */
const clamp=(value,min,max,fallback)=>typeof value==='number'&&Number.isFinite(value)?Math.max(min,Math.min(max,value)):fallback;
const boundedText=(value,limit)=>typeof value==='string'?value.slice(0,limit):'';
export function sceneView(value={}) {
  return {
    cameraYaw:clamp(value.cameraYaw,-35,55,24),
    cameraDistance:clamp(value.cameraDistance,7,23,13.5),
    follow:typeof value.follow==='boolean'?value.follow:true,
    recipient:boundedText(value.recipient,80)||null,
    draftRecipient:boundedText(value.draftRecipient,80)||null,
    draft:boundedText(value.draft,600),
    tab:['story','people','places','bag'].includes(value.tab)?value.tab:'story',
    started:value.started===true,
    journalOpen:value.journalOpen===true,
    focus:['speech','world'].includes(value.focus)?value.focus:null,
  };
}

export function installProductHost({windowObject=globalThis.window,ready=()=>true,pending=()=>false,
  pause=()=>{},refresh=async()=>{},capture=()=>({}),restore=async()=>{}}={}) {
  const host=windowObject;
  if(!host||host.parent===host)return {notifyReady(){},notifyView(){},destroy(){}};
  const origin=host.location.origin;
  const lifeId=new URL(host.location.href).searchParams.get('experience')||'pompeii_life';
  let operation=false,viewTimer=null;
  const schedule=host.setTimeout?.bind(host)||globalThis.setTimeout;
  const unschedule=host.clearTimeout?.bind(host)||globalThis.clearTimeout;
  const send=(requestId,status,extra={})=>host.parent.postMessage({kind:'kalends:scene',life_id:lifeId,request_id:requestId,status,...extra},origin);
  const flushView=()=>{if(viewTimer!==null)unschedule(viewTimer);viewTimer=null;if(ready()&&!operation)send('view','ok',{view:sceneView(capture())});};
  function notifyView({immediate=false}={}){if(immediate){flushView();return;}if(viewTimer!==null)unschedule(viewTimer);viewTimer=schedule(flushView,150);}
  async function receive(event) {
    const data=event.data;
    if(event.origin!==origin||event.source!==host.parent||!data||Array.isArray(data)||data.kind!=='kalends:host'
      ||data.life_id!==lifeId||typeof data.request_id!=='string'||!data.request_id.length||data.request_id.length>120
      ||!['pause','refresh','capture','restore'].includes(data.action))return;
    const requestId=data.request_id;
    if(data.action==='pause') {
      pause();send(requestId,'ok',{view:sceneView(capture())});return;
    }
    if(data.action==='capture') {
      send(requestId,ready()?'ok':'pending',{view:sceneView(capture())});return;
    }
    if(!ready()||pending()||operation){send(requestId,'pending');return;}
    operation=true;
    try {
      if(data.action==='refresh')await refresh();
      else await restore(sceneView(data.view));
      send(requestId,'ok',{view:sceneView(capture())});
    } catch {
      send(requestId,'error',{error:'The scene could not refresh. Check the saved world and try again.'});
    } finally {operation=false;}
  }
  host.addEventListener('message',receive);
  host.addEventListener('pagehide',flushView);
  return {notifyReady:()=>send('ready','ready',{view:sceneView(capture())}),notifyView,
    destroy:()=>{host.removeEventListener('message',receive);host.removeEventListener('pagehide',flushView);if(viewTimer!==null)unschedule(viewTimer);}};
}
