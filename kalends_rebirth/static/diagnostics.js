/* Local developer diagnostics. Enabled only by ?dev=1; never sent as telemetry. */
(() => {
  'use strict';
  if (new URLSearchParams(location.search).get('dev') !== '1') return;
  const limit = 3000, samples = [], pending = new Map();
  let sequence = 0, previousFrame = null, lastPanel = 0, movementInput = null, frozen = false;
  let inputCounts = {accepted:0,ignored:0,from_visual_idle:0};
  let observations = {next_changed_actor_draw:0,idle_committed_actor_draw:0,cancelled_before_next_draw:0};
  const clock = () => performance.now();
  const record = (kind, values = {}) => {
    if(frozen)return;
    samples.push({sequence: ++sequence, at_ms: +clock().toFixed(3), kind, ...values});
    if (samples.length > limit) samples.shift();
  };
  const metric = (kind, field = 'duration_ms') => {
    const values = samples.filter(s => s.kind === kind && Number.isFinite(s[field])).map(s => s[field]).sort((a,b) => a-b);
    if (!values.length) return null;
    const percentile = p => {const at=(values.length-1)*p,lo=Math.floor(at),hi=Math.ceil(at);return +(values[lo]+(values[hi]-values[lo])*(at-lo)).toFixed(3);};
    return {n: values.length, p50: percentile(.5), p95: percentile(.95), p99: percentile(.99), max: values.at(-1)};
  };
  const panel = document.createElement('details');
  panel.id = 'developer-diagnostics';
  panel.innerHTML = '<summary>Developer trace · local</summary><pre aria-label="Performance measurements"></pre><button type="button" data-focus-game>Focus game</button><button type="button" data-reset-trace>Reset trace</button><button type="button" data-freeze-trace>Freeze raw trace</button><button type="button" data-export-trace>Export trace</button>';
  document.body.append(panel);
  const report = (includeSamples=false) => {
    const frame = metric('frame','interval_ms'), draw = metric('frame','draw_ms');
    const memory = performance.memory ? {used_bytes: performance.memory.usedJSHeapSize, total_bytes: performance.memory.totalJSHeapSize, scope:'Chromium JS heap estimate; excludes GPU and server'} : null;
    return {schema:'kalends-browser-trace-v2', quantile_method:'linear interpolation at (n-1)*p', viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
      sample_limit:limit, samples_retained:samples.length, frame_intervals_ms:frame, canvas_draw_ms:draw,
      backend_roundtrip_ms:metric('backend'), input_to_next_changed_actor_draw_ms:metric('movement_feedback'),
      idle_input_to_committed_actor_draw_ms:metric('movement_committed_feedback'),
      conversation_feedback_ms:metric('conversation'), scene_transition_ms:metric('scene_transition'),
      long_tasks_ms:metric('long_task'), memory,
      inputs:{...inputCounts}, input_count_scope:'Since last reset; frame/latency percentiles describe retained samples only.',
      observations_since_reset:{...observations},
      estimated_missed_60hz_slots:samples.filter(s=>s.kind==='frame').reduce((n,s)=>n+Math.max(0,Math.floor(s.interval_ms/(1000/60))-1),0),
      pending_movement_input:movementInput?{input_id:movementInput.input_id,label:movementInput.label,from_visual_idle:movementInput.from_visual_idle,authority_accepted:movementInput.authority_accepted,waiting_ms:+(clock()-movementInput.start).toFixed(3)}:null,
      notes:['Developer-only local trace; no typed dialogue or NPC private state.', 'Frame callback/render measurements are not physical-device or GPU benchmarks.', 'Next-changed-actor draw can be continuing prior animation and is not causally attributed to the input.', 'Committed-actor draw includes only inputs accepted with no active navigation or remaining animation, followed by the matching accepted move and a changed actor draw. Nonidle, cancelled, superseded and unmoved inputs are excluded, not zero latency.', 'Draw ends at JavaScript Canvas submission, not browser composition or physical display.', 'Backend samples include local HTTP and serialization; they do not isolate Python CPU.', 'Pathfinding CPU is measured separately in the Python navigation study.'], ...(includeSamples?{samples:[...samples]}:{})};
  };
  const refresh = () => {panel.querySelector('pre').textContent=JSON.stringify(report(),null,2);};
  panel.querySelector('[data-focus-game]').onclick = () => document.querySelector('#town')?.focus();
  panel.querySelector('[data-reset-trace]').onclick = () => {frozen=false;samples.length=0;pending.clear();movementInput=null;previousFrame=null;inputCounts={accepted:0,ignored:0,from_visual_idle:0};observations={next_changed_actor_draw:0,idle_committed_actor_draw:0,cancelled_before_next_draw:0};record('trace_reset');refresh();};
  panel.querySelector('[data-freeze-trace]').onclick = () => {frozen=true;panel.querySelector('pre').textContent=JSON.stringify(report(true),null,2);};
  panel.querySelector('[data-export-trace]').onclick = () => {
    const url=URL.createObjectURL(new Blob([JSON.stringify(report(true),null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='kalends-browser-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  try {if (PerformanceObserver.supportedEntryTypes.includes('longtask')) {
    new PerformanceObserver(list => list.getEntries().forEach(e=>record('long_task',{duration_ms:e.duration}))).observe({type:'longtask',buffered:true});
  }} catch {record('capability_unavailable',{capability:'longtask'});}
  window.KalendsDiagnostics = {
    begin(kind, label) {const token=++sequence;pending.set(token,{kind,label,start:clock()});return token;},
    end(token, values={}) {const p=pending.get(token);if(!p)return;pending.delete(token);record(p.kind,{label:p.label,duration_ms:+(clock()-p.start).toFixed(3),...values});},
    input(label,accepted,reason='',{from_visual_idle=false}={}) {if(frozen)return;inputCounts[accepted?'accepted':'ignored']++;const start=clock(),input_id=++sequence;if(accepted&&from_visual_idle)inputCounts.from_visual_idle++;record('input',{input_id,label,accepted,reason,from_visual_idle});if(accepted)movementInput={start,label,input_id,from_visual_idle,authority_accepted:false};return input_id;},
    committed(input_id) {if(!frozen&&movementInput&&movementInput.input_id===input_id){movementInput.authority_accepted=true;record('movement_authority_accepted',{input_id});}},
    cancelInput(reason) {if(!frozen&&movementInput){observations.cancelled_before_next_draw++;record('movement_observation_cancelled',{input_id:movementInput.input_id,reason});movementInput=null;}},
    moved() {if(!frozen&&movementInput){const values={input_id:movementInput.input_id,label:movementInput.label,duration_ms:+(clock()-movementInput.start).toFixed(3),from_visual_idle:movementInput.from_visual_idle,authority_accepted:movementInput.authority_accepted};observations.next_changed_actor_draw++;record('movement_feedback',values);if(values.from_visual_idle&&values.authority_accepted){observations.idle_committed_actor_draw++;record('movement_committed_feedback',values);}movementInput=null;}},
    frame(time,draw_ms,moving) {if(frozen)return;if(previousFrame!==null)record('frame',{interval_ms:+(time-previousFrame).toFixed(3),draw_ms:+draw_ms.toFixed(3),moving});previousFrame=time;if(time-lastPanel>1000){lastPanel=time;refresh();}},
    paused() {previousFrame=null;}, record
  };
  record('trace_start');refresh();
})();
