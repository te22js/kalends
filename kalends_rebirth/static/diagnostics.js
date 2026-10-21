/* Local developer diagnostics. Enabled only by ?dev=1; never sent as telemetry. */
(() => {
  'use strict';
  if (new URLSearchParams(location.search).get('dev') !== '1') return;
  const limit = 3000, samples = [], pending = new Map();
  let sequence = 0, previousFrame = null, lastPanel = 0, movementInput = null;
  const clock = () => performance.now();
  const record = (kind, values = {}) => {
    samples.push({sequence: ++sequence, at_ms: +clock().toFixed(3), kind, ...values});
    if (samples.length > limit) samples.shift();
  };
  const metric = (kind, field = 'duration_ms') => {
    const values = samples.filter(s => s.kind === kind && Number.isFinite(s[field])).map(s => s[field]).sort((a,b) => a-b);
    if (!values.length) return null;
    const percentile = p => +values[Math.min(values.length-1, Math.floor((values.length-1)*p))].toFixed(3);
    return {n: values.length, p50: percentile(.5), p95: percentile(.95), p99: percentile(.99), max: values.at(-1)};
  };
  const panel = document.createElement('details');
  panel.id = 'developer-diagnostics';
  panel.innerHTML = '<summary>Developer trace · local</summary><pre aria-label="Performance measurements"></pre><button type="button" data-reset-trace>Reset trace</button><button type="button" data-export-trace>Export trace</button>';
  document.body.append(panel);
  const report = (includeSamples=false) => {
    const frame = metric('frame','interval_ms'), draw = metric('frame','draw_ms');
    const memory = performance.memory ? {used_bytes: performance.memory.usedJSHeapSize, total_bytes: performance.memory.totalJSHeapSize, scope:'Chromium JS heap estimate; excludes GPU and server'} : null;
    return {schema:'kalends-browser-trace-v1', viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
      sample_limit:limit, samples_retained:samples.length, frame_intervals_ms:frame, canvas_draw_ms:draw,
      backend_roundtrip_ms:metric('backend'), input_to_first_actor_render_ms:metric('movement_feedback'),
      conversation_feedback_ms:metric('conversation'), scene_transition_ms:metric('scene_transition'),
      long_tasks_ms:metric('long_task'), memory,
      inputs:{accepted:samples.filter(s=>s.kind==='input'&&s.accepted).length,ignored:samples.filter(s=>s.kind==='input'&&!s.accepted).length},
      estimated_missed_60hz_slots:samples.filter(s=>s.kind==='frame').reduce((n,s)=>n+Math.max(0,Math.floor(s.interval_ms/(1000/60))-1),0),
      pending_movement_input:movementInput?{label:movementInput.label,waiting_ms:+(clock()-movementInput.start).toFixed(3)}:null,
      notes:['Developer-only local trace; no typed dialogue or NPC private state.', 'Frame callback/render measurements are not physical-device or GPU benchmarks.', 'Input feedback ends at the first changed actor position rendered by the game.', 'Backend samples include local HTTP and serialization; they do not isolate Python CPU.', 'Pathfinding CPU is measured separately in the Python navigation study.'], ...(includeSamples?{samples:[...samples]}:{})};
  };
  const refresh = () => {panel.querySelector('pre').textContent=JSON.stringify(report(),null,2);};
  panel.querySelector('[data-reset-trace]').onclick = () => {samples.length=0;pending.clear();movementInput=null;previousFrame=null;record('trace_reset');refresh();};
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
    input(label,accepted,reason='') {record('input',{label,accepted,reason});if(accepted)movementInput={start:clock(),label};},
    moved() {if(movementInput){record('movement_feedback',{label:movementInput.label,duration_ms:+(clock()-movementInput.start).toFixed(3)});movementInput=null;}},
    frame(time,draw_ms,moving) {if(previousFrame!==null)record('frame',{interval_ms:+(time-previousFrame).toFixed(3),draw_ms:+draw_ms.toFixed(3),moving});previousFrame=time;if(time-lastPanel>1000){lastPanel=time;refresh();}},
    paused() {previousFrame=null;}, record
  };
  record('trace_start');refresh();
})();
