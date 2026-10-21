/* Isolated renderer fixture. Never reads /api/state or commits a game action. */
(() => {
  'use strict';
  const WIDTH=1280,HEIGHT=720,WARMUP=30,OBSERVATIONS=180,CASE_TIMEOUT=30000;
  const ORDERS=[['empty','canvas','phaser'],['canvas','phaser','empty'],['phaser','empty','canvas']];
  const PROTOCOL_VERSION='renderer-poc-1';
  const VENDOR={name:'Phaser',version:'4.2.1',bytes:1375976,sha256:'66348b1b5141e49b7d5ebbe688cddcb502eab1cb00f21c538686a5b2c5abe4de'};
  const $=selector=>document.querySelector(selector),stage=$('#stage');
  let assets=null,active=null,comparison=false,cancelled=false,lastReport=null;
  const now=()=>performance.now();
  const finite=value=>Number.isFinite(value)?value:null;
  const errorText=error=>String(error?.message||error).slice(0,1200);
  const status=text=>$('#status').textContent=text;
  function quantile(values,q){if(!values.length)return null;const sorted=[...values].sort((a,b)=>a-b);return sorted[Math.max(0,Math.ceil(q*sorted.length)-1)];}
  function statistics(values){return values.length?{n:values.length,mean:values.reduce((a,b)=>a+b,0)/values.length,p50:quantile(values,.5),p95:quantile(values,.95),p99:quantile(values,.99),max:Math.max(...values)}:{n:0,mean:null,p50:null,p95:null,p99:null,max:null};}
  function environment(){const r=stage.getBoundingClientRect();return{user_agent:navigator.userAgent,platform:navigator.platform,device_pixel_ratio:devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},backing:{width:WIDTH,height:HEIGHT,resolution:1},stage_css:{width:r.width,height:r.height,x:r.x,y:r.y},visibility:document.visibilityState,document_has_focus:document.hasFocus(),time_origin:performance.timeOrigin,phaser_runtime_version:window.Phaser?.VERSION||null,memory_api:performance.memory?{used_js_heap_size:performance.memory.usedJSHeapSize,total_js_heap_size:performance.memory.totalJSHeapSize,limit:performance.memory.jsHeapSizeLimit,scope:'Browser-reported JS heap, not process/GPU memory'}:null};}
  function summarize(record){const intervals=record.samples.map(s=>s.interval_ms),interval=statistics(intervals);return{mode:record.mode,repetition:record.repetition,status:record.status,observations:record.samples.length,interval_ms:interval,callback_rate_hz:interval.mean?1000/interval.mean:null,render_submit_cpu_ms:statistics(record.samples.map(s=>s.render_submit_cpu_ms)),update_cpu_ms:statistics(record.samples.map(s=>s.update_cpu_ms)),whole_step_cpu_ms:statistics(record.samples.map(s=>s.whole_step_cpu_ms)),intervals_above_16_7ms:intervals.filter(v=>v>16.7).length,estimated_60hz_unfilled_slots_not_hardware_drops:intervals.reduce((n,v)=>n+Math.max(0,Math.round(v/(1000/60))-1),0),error:record.error||null};}
  function publish(){if(!lastReport)return;lastReport.updated_utc=new Date().toISOString();$('#report').textContent=JSON.stringify(lastReport,null,2);$('#summary').textContent=JSON.stringify({status:lastReport.status,overall_valid:lastReport.overall_valid??null,completed_cases:lastReport.cases.filter(c=>c.status==='complete').length,planned_cases:9,cases:lastReport.cases.map(c=>c.summary)},null,2);$('#export').disabled=false;}
  function toolbar(){ $('#run').disabled=!assets||comparison;for(const b of document.querySelectorAll('[data-preview]'))b.disabled=!assets||comparison;$('#stop').disabled=!active&&!comparison;}
  function loadImage(src){return new Promise((resolve,reject)=>{const img=new Image();img.onload=async()=>{try{if(img.decode)await img.decode();resolve(img);}catch(error){reject(error);}};img.onerror=()=>reject(Error('Could not load local fixture image '+src));img.src=src;});}

  // Shared paths, sprite frames and delta integration are identical in both renderers.
  const fixture=Array.from({length:7},(_,i)=>({frame:i,x:260+i*115,y:330+(i%2)*45,speed:65+i*3,offset:i*17}));
  function positions(elapsed,manual,delta){const points=fixture.map(a=>{let d=(elapsed/1000*a.speed+a.offset)%130,x=a.x,y=a.y;if(d<40)x+=d;else if(d<65){x+=40;y+=d-40;}else if(d<105){x+=105-d;y+=25;}else y+=130-d;return{frame:a.frame,x,y};});if(manual?.target){const d=Math.hypot(manual.target.x-manual.x,manual.target.y-manual.y),step=Math.max(0,delta)*.32;if(d<=step){manual.x=manual.target.x;manual.y=manual.target.y;}else if(d){manual.x+=(manual.target.x-manual.x)/d*step;manual.y+=(manual.target.y-manual.y)/d*step;}points[0]={frame:0,x:manual.x,y:manual.y};}return points.sort((a,b)=>a.y-b.y);}
  function canvasDraw(ctx,points,manual){ctx.drawImage(assets.street,0,0,WIDTH,HEIGHT);for(const a of points)ctx.drawImage(assets.sprites,(a.frame%4)*384,Math.floor(a.frame/4)*512,384,512,a.x-36,a.y-96,72,96);if(manual?.target){ctx.strokeStyle='#fff5a6';ctx.lineWidth=2;ctx.beginPath();ctx.arc(manual.target.x,manual.target.y,9,0,Math.PI*2);ctx.stroke();}}
  function blankCanvas(){stage.replaceChildren();const canvas=document.createElement('canvas');canvas.width=WIDTH;canvas.height=HEIGHT;stage.append(canvas);return canvas;}
  function showStatic(){if(!assets)return;const canvas=blankCanvas(),ctx=canvas.getContext('2d',{alpha:false});canvasDraw(ctx,positions(0,null,0),null);}
  async function stopActive(reason){if(active)await active.stop(reason);}

  function runCase(mode,repetition,manualMode=false){return new Promise(resolve=>{
    const record={mode,repetition,manual:manualMode,status:'starting',started_utc:new Date().toISOString(),environment_before:environment(),warmup_frames:WARMUP,planned_observations:OBSERVATIONS,samples:[],input_samples:[],events:[],capabilities:{},error:null};
    let game=null,raf=0,timeout=0,frames=0,lastClock=null,elapsed=0,finished=false,finishing=null,stepStart=0,renderStart=0,updateCpu=0,frameClock=0;
    const manual=manualMode?{x:fixture[0].x,y:fixture[0].y,target:null,pendingInput:null}:null;
    const owner={mode,manual,record,stop:finish};active=owner;toolbar();
    async function finish(reason,error){if(finishing)return finishing;if(finished)return;finished=true;finishing=(async()=>{
      cancelAnimationFrame(raf);clearTimeout(timeout);record.status=reason;record.error=error?errorText(error):null;
      if(game){const dispose=game;game=null;await new Promise(done=>{let settled=false;const end=()=>{if(!settled){settled=true;done();}};dispose.events.once(Phaser.Core.Events.DESTROY,end);try{dispose.destroy(true);}catch(problem){record.events.push({event:'destroy_error',text:errorText(problem)});end();}setTimeout(end,500);});}
      if(active===owner)active=null;record.ended_utc=new Date().toISOString();record.environment_after=environment();record.summary=summarize(record);toolbar();resolve(record);
    })();return finishing;}
    function feedback(){if(manual?.pendingInput){const sample={...manual.pendingInput,input_to_render_submit_ms:now()-manual.pendingInput.at_ms,mode,scope:'Local presentation fixture, not authoritative game input'};record.input_samples.push(sample);record.input_samples=record.input_samples.slice(-50);$('#input-status').textContent=`${mode} local click → render submission: ${sample.input_to_render_submit_ms.toFixed(2)} ms. This is not game-controller latency.`;manual.pendingInput=null;}}
    function observe(clock,renderCpu,wholeCpu){if(finished)return;const delta=lastClock===null?null:clock-lastClock;lastClock=clock;frames++;feedback();if(!manualMode&&frames>WARMUP&&delta!==null&&delta>=0){record.samples.push({index:record.samples.length,interval_ms:delta,render_submit_cpu_ms:finite(renderCpu),update_cpu_ms:finite(updateCpu),whole_step_cpu_ms:finite(wholeCpu)});if(record.samples.length===OBSERVATIONS)finish('complete');}}
    timeout=setTimeout(()=>finish('timeout',Error('Case exceeded30 seconds; partial samples retained.')),CASE_TIMEOUT);
    if(manualMode)clearTimeout(timeout);
    if(mode==='empty'||mode==='canvas'){
      const canvas=blankCanvas(),ctx=mode==='canvas'?canvas.getContext('2d',{alpha:false,desynchronized:false}):null;
      if(mode==='canvas'&&!ctx){finish('unavailable',Error('Canvas2D context unavailable.'));return;}
      record.capabilities={renderer:mode==='empty'?'empty_requestAnimationFrame':'CanvasRenderingContext2D',canvas_backing:{width:canvas.width,height:canvas.height},context_attributes:ctx?.getContextAttributes?.()||null};
      function frame(){if(finished)return;const clock=now(),begin=clock,delta=lastClock===null?0:clock-lastClock;elapsed+=delta;let points=null;const updateStart=now();if(mode==='canvas')points=positions(elapsed,manual,delta);updateCpu=now()-updateStart;const drawStart=now();if(ctx)canvasDraw(ctx,points,manual);const renderCpu=now()-drawStart;observe(clock,renderCpu,now()-begin);if(!finished)raf=requestAnimationFrame(frame);}
      record.status='running';raf=requestAnimationFrame(frame);return;
    }
    if(!window.Phaser||Phaser.VERSION!==VENDOR.version){finish('unavailable',Error('Expected vendored Phaser4.2.1 is unavailable.'));return;}
    stage.replaceChildren();
    try{
      class ProbeScene extends Phaser.Scene{
        create(){
          if(finished){this.game.destroy(true);return;}
          if(this.game.renderer.type!==Phaser.WEBGL){finish('unavailable',Error('Phaser did not create the requested WebGL renderer.'));return;}
          this.textures.addImage('probe-street',assets.street);this.textures.addSpriteSheet('probe-actors',assets.sprites,{frameWidth:384,frameHeight:512,endFrame:7});
          this.add.image(0,0,'probe-street').setOrigin(0,0).setDisplaySize(WIDTH,HEIGHT);
          this.actors=fixture.map(a=>this.add.image(a.x,a.y,'probe-actors',a.frame).setOrigin(.5,1).setDisplaySize(72,96));
          this.marker=manualMode?this.add.graphics().setDepth(10000):null;
          const gl=this.game.renderer.gl;record.capabilities={renderer:'Phaser WebGL',version:Phaser.VERSION,canvas_backing:{width:this.game.canvas.width,height:this.game.canvas.height},webgl_version:gl.getParameter(gl.VERSION),context_attributes:gl.getContextAttributes(),timer_source:'performance.now sampled at PRE_STEP; no smoothed Phaser delta used'};
          if(this.game.canvas.width!==WIDTH||this.game.canvas.height!==HEIGHT){finish('unavailable',Error('Actual Phaser backing dimensions differ from the fixed fixture.'));return;}
          this.game.events.on(Phaser.Core.Events.PRE_STEP,()=>{if(finished)return;frameClock=now();stepStart=frameClock;const delta=lastClock===null?0:frameClock-lastClock;elapsed+=delta;const updateStart=now(),points=positions(elapsed,manual,delta);for(const a of points)this.actors[a.frame].setPosition(a.x,a.y).setDepth(a.y);if(this.marker){this.marker.clear();if(manual.target)this.marker.lineStyle(2,0xfff5a6).strokeCircle(manual.target.x,manual.target.y,9);}updateCpu=now()-updateStart;});
          this.game.events.on(Phaser.Core.Events.PRE_RENDER,()=>{renderStart=now();});
          this.game.events.on(Phaser.Core.Events.POST_RENDER,()=>{if(!frameClock||finished)return;const end=now();observe(frameClock,end-renderStart,end-stepStart);frameClock=0;});
          this.game.events.on(Phaser.Core.Events.CONTEXT_LOST,()=>finish('context_lost',Error('WebGL context lost; measurements invalid.')));
          record.status='running';
        }
      }
      game=new Phaser.Game({type:Phaser.WEBGL,width:WIDTH,height:HEIGHT,resolution:1,parent:stage,scene:ProbeScene,backgroundColor:'#101813',transparent:false,banner:false,audio:{noAudio:true},input:false,autoFocus:false,fps:{target:60,limit:0,forceSetTimeOut:false,smoothStep:false},render:{antialias:true,antialiasGL:true,desynchronized:false}});
    }catch(error){finish('unavailable',error);}
  });}

  async function runComparison(){if(comparison||!assets)return;if(document.hidden){status('Make this page visible before running the comparison.');return;}comparison=true;cancelled=false;await stopActive('superseded');lastReport={protocol_version:PROTOCOL_VERSION,status:'running',started_utc:new Date().toISOString(),vendor:VENDOR,environment:environment(),design:{width:WIDTH,height:HEIGHT,resolution:1,actors:7,warmup_frames:WARMUP,observations_per_case:OBSERVATIONS,orders:ORDERS,case_timeout_ms:CASE_TIMEOUT,asset_loading:'Shared decoded HTMLImageElements before timing; Phaser texture upload/boot discarded by fixed warmup',motion:'Same elapsed-time rectangular paths and frame atlas; no game logic, API calls, labels, masks, physics, effects or automatic input',cpu_scope:'Submission and whole-step wall-time spans; no GPU completion or hardware-drop measurement',frame_independence:'Three case repetitions per renderer; frames are dependent within runs, not independent trials'},cases:[],events:[],errors:[]};toolbar();publish();try{for(let repetition=0;repetition<ORDERS.length;repetition++)for(const mode of ORDERS[repetition]){if(cancelled)break;status(`Run ${repetition+1}/3 · ${mode} · 30 warmup + 180 observations. Keep this page visible.`);const record=await runCase(mode,repetition);lastReport.cases.push(record);publish();}lastReport.status=cancelled?'interrupted':'finished';lastReport.overall_valid=!cancelled&&lastReport.cases.length===9&&lastReport.cases.every(c=>c.status==='complete'&&c.samples.length===OBSERVATIONS)&&!lastReport.errors.length;lastReport.ended_utc=new Date().toISOString();status(lastReport.overall_valid?'Finished 9/9 cases. Export JSON to preserve actual measurements.':'Comparison incomplete or unavailable in part; inspect and preserve the errors and partial samples.');}catch(error){lastReport.status='error';lastReport.overall_valid=false;lastReport.errors.push(errorText(error));status(errorText(error));}finally{comparison=false;publish();showStatic();toolbar();}}
  $('#run').onclick=runComparison;
  $('#stop').onclick=async()=>{cancelled=true;await stopActive('cancelled');status('Stopped. Partial automatic results remain available.');if(!comparison)showStatic();toolbar();};
  for(const button of document.querySelectorAll('[data-preview]'))button.onclick=async()=>{if(comparison||!assets)return;await stopActive('superseded');status(`${button.dataset.preview} manual preview. Click the fixture; no game session is involved.`);const result=await runCase(button.dataset.preview,-1,true);if(result.error)status(result.error);};
  stage.addEventListener('pointerdown',event=>{if(comparison||!active?.manual||active.mode==='empty')return;const r=stage.getBoundingClientRect(),target={x:Math.max(0,Math.min(WIDTH,(event.clientX-r.left)/r.width*WIDTH)),y:Math.max(0,Math.min(HEIGHT,(event.clientY-r.top)/r.height*HEIGHT))};active.manual.target=target;active.manual.pendingInput={at_ms:now(),target};});
  $('#export').onclick=()=>{if(!lastReport)return;const blob=new Blob([JSON.stringify(lastReport,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`kalends-renderer-probe-${new Date().toISOString().replace(/[:.]/g,'-')}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  document.addEventListener('visibilitychange',()=>{const event={event:'visibilitychange',at_ms:now(),state:document.visibilityState};if(lastReport&&comparison)lastReport.events.push(event);if(active)active.record.events.push(event);if(document.hidden&&comparison){cancelled=true;stopActive('hidden',Error('Document became hidden; comparison interrupted.'));}});
  window.addEventListener('resize',()=>{if(comparison){cancelled=true;lastReport.events.push({event:'viewport_changed',at_ms:now(),width:innerWidth,height:innerHeight});stopActive('viewport_changed',Error('Viewport changed during comparison.'));}});
  for(const kind of ['focus','blur'])window.addEventListener(kind,()=>{if(lastReport&&comparison)lastReport.events.push({event:kind,at_ms:now()});});
  window.addEventListener('error',event=>{const text=String(event.message||'Browser error').slice(0,1200);if(lastReport&&comparison){lastReport.errors.push(text);lastReport.errors=lastReport.errors.slice(-50);}if(active)active.stop('error',Error(text));});
  window.addEventListener('unhandledrejection',event=>{const text=errorText(event.reason);if(lastReport&&comparison){lastReport.errors.push(text);lastReport.errors=lastReport.errors.slice(-50);}if(active)active.stop('error',Error(text));});
  Promise.all([loadImage('/assets/street.png'),loadImage('/assets/sprites-original.png')]).then(([street,sprites])=>{assets={street,sprites};showStatic();status('Ready. No measurements yet. Use Run comparison; manual previews are separate.');toolbar();}).catch(error=>{status(errorText(error));$('#summary').textContent=JSON.stringify({status:'asset_error',error:errorText(error)},null,2);});
})();
