/* Kalends browser adapter. All world content is read from the local Python engine. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const state = { data: null, running: false, busy: false, selectedAgent: null, selectedEvent: null, timeline: 'original', filter: 'all', search: '', timer: null, traceSerial: 0, toastTimer: null };
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const human = (value) => String(value ?? '').replace(/[_.]/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  const scalar = (value) => value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const fmt = (value, digits = 1) => typeof value === 'number' ? Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: digits }) : scalar(value);
  const array = (value) => Array.isArray(value) ? value : value == null ? [] : Object.values(value);
  const identity = (agent) => agent.id ?? agent.agent_id ?? agent.name;
  const active = () => state.data?.[state.timeline] ?? state.data?.original;
  const nameOf = (id, snapshot = active()) => snapshot?.agents?.find((agent) => identity(agent) === id)?.name ?? id;
  const selectedAgent = () => active()?.agents?.find((agent) => identity(agent) === state.selectedAgent) ?? active()?.agents?.[0];
  const locationOf = (id, snapshot = active()) => snapshot?.locations?.find((location) => location.id === id)?.label ?? human(id);
  const eventId = (event) => event?.event_id ?? event?.id;
  const eventTitle = (event) => event.title ?? event.payload?.title ?? describeEvent(event);
  const eventType = (event) => event.category ?? event.etype ?? event.type ?? 'event';
  const ref = (id, timeline = state.timeline) => `<button class="event-ref" data-event-ref="${esc(id)}" data-timeline="${esc(timeline)}" title="Inspect event ${esc(id)}">#${esc(id)}</button>`;
  const raw = (value, label = 'Inspect recorded data') => `<details class="raw-data"><summary>${esc(label)}</summary><pre>${esc(JSON.stringify(value, null, 2))}</pre></details>`;

  function describeEvent(event) {
    const payload = event.payload ?? {};
    if (payload.speaker && payload.listener) return `${nameOf(payload.speaker)} → ${nameOf(payload.listener)}: ${human(payload.value ?? payload.prop ?? 'report')}`;
    if (payload.action) return `${array(event.actors).map((id) => nameOf(id)).join(', ')} · ${human(payload.action)}`;
    if (payload.prop && payload.value != null) return `${human(payload.prop)} · ${human(payload.value)}`;
    return human(event.etype ?? event.type ?? 'Recorded event');
  }

  function category(event) {
    const text = `${event.category} ${event.etype} ${event.payload?.action ?? ''}`.toLowerCase();
    if (/decision|commit|reserve|purchase|verify|abstain|cancel|defer/.test(text)) return 'decisions';
    if (/tell|message|report|observ|belief|correction|inspection|rumour|rumor|retract/.test(text)) return 'information';
    return 'world';
  }

  async function api(path, body) {
    const response = await fetch(path, body === undefined ? { cache: 'no-store' } : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    let data;
    try { data = await response.json(); } catch { throw new Error(`The local server returned an unreadable response (${response.status}).`); }
    if (!response.ok || data.error) throw new Error(data.error ?? `Request failed (${response.status}).`);
    return data;
  }

  function showError(error) { $('#error-banner').textContent = error.message ?? String(error); $('#error-banner').hidden = false; }
  function clearError() { $('#error-banner').hidden = true; }
  function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 4500); }

  function updateControls() {
    const ready = Boolean(state.data?.original);
    const done = ready && state.data.original.done && (!state.data.branch || state.data.branch.done);
    $('#run-button').disabled = !ready || done;
    $('#step-button').disabled = !ready || state.busy || done;
    $('#reset-button').disabled = !ready || state.busy;
    $('#run-label').textContent = state.running ? 'Pause city' : done ? 'Day complete' : 'Run city';
    $('#run-icon').textContent = state.running ? 'Ⅱ' : '▶';
    $('#playback-status').textContent = !ready ? 'Connecting' : state.busy ? 'Advancing' : done ? 'Complete' : state.running ? 'Running' : 'Paused';
    $('#playback-dot').classList.toggle('running', state.running);
    $('#fork-button').disabled = !ready || state.busy || !canFork();
    $('#fork-button').innerHTML = `<span aria-hidden="true">⑂</span> ${state.data?.branch ? 'Replace branch at this moment' : 'Fork this moment'} <span aria-hidden="true">→</span>`;
    $('#settings-form button').disabled = state.busy;
  }

  function pause() { state.running = false; clearTimeout(state.timer); updateControls(); }
  function schedule() {
    clearTimeout(state.timer);
    if (state.running) state.timer = setTimeout(async () => { await step(1); if (state.running) schedule(); }, Number($('#speed').value));
  }
  function toggleRun() { if (!state.data) return; if (state.running) pause(); else { state.running = true; updateControls(); step(1).then(() => { if (state.running) schedule(); }); } }

  async function step(count = 1) {
    if (state.busy || !state.data) return;
    state.busy = true; clearError(); updateControls();
    try { await accept(await api('/api/step', { count, timeline: 'both' })); if (state.data.original.done && (!state.data.branch || state.data.branch.done)) pause(); }
    catch (error) { pause(); showError(error); }
    finally { state.busy = false; updateControls(); }
  }

  async function reset(event) {
    event?.preventDefault(); pause(); if (state.busy) return;
    state.busy = true; clearError(); updateControls();
    try {
      const config = { seed: Number($('#seed').value), n_agents: Number($('#population').value), family: $('#family').value, memory: $('#memory').value, gate: $('#gate').value, threshold: Number($('#threshold').value) };
      const result = await api('/api/reset', config);
      state.selectedAgent = null; state.selectedEvent = null; state.timeline = 'original'; state.traceSerial += 1;
      await accept(result); $('.settings').open = false; toast('A new world is ready. Run the city to begin.');
    } catch (error) { showError(error); }
    finally { state.busy = false; updateControls(); }
  }

  async function accept(data) {
    const firstLoad = !state.data;
    state.data = data.original ? data : await api('/api/state');
    if (firstLoad) {
      const config = state.data.original.config ?? {};
      for (const [key, id] of Object.entries({ seed: 'seed', n_agents: 'population', family: 'family', memory: 'memory', gate: 'gate', threshold: 'threshold' })) {
        if (config[key] != null && Array.from($(`#${id}`).options ?? []).some((option) => option.value === String(config[key]))) $(`#${id}`).value = config[key];
        else if (config[key] != null && $(`#${id}`).tagName === 'INPUT') $(`#${id}`).value = config[key];
      }
    }
    if (!state.data.branch) state.timeline = 'original';
    if (!active()?.agents?.some((agent) => identity(agent) === state.selectedAgent)) state.selectedAgent = identity(active()?.agents?.[0] ?? {});
    render();
  }

  function render() {
    const snapshot = active(); if (!snapshot) return;
    const tick = state.data.original.tick;
    $('#clock-tick').textContent = tick < 0 ? 'Before dawn' : `Tick ${String(tick).padStart(2, '0')}`;
    $('#clock-detail').textContent = `${snapshot.agents?.length ?? 0} CITIZENS · SEED ${snapshot.config?.seed ?? '—'}`;
    $('#timeline-select').innerHTML = `<option value="original" ${state.timeline === 'original' ? 'selected' : ''}>Original history</option>${state.data.branch ? `<option value="branch" ${state.timeline === 'branch' ? 'selected' : ''}>Altered history</option>` : ''}`;
    renderMaps(); renderAgent(); renderTruth(); renderEvents(); renderInterventions(); renderComparison(); updateControls();
    $('#ledger-caption').textContent = `${state.timeline === 'branch' ? 'ALTERED' : 'ORIGINAL'} · APPEND-ONLY EVENT HISTORY`;
  }

  function renderMaps() {
    const grid = $('#map-grid');
    const histories = state.data.branch ? ['original', 'branch'] : ['original'];
    grid.classList.toggle('branched', Boolean(state.data.branch));
    for (const key of ['original', 'branch']) {
      let wrap = grid.querySelector(`[data-map="${key}"]`);
      if (!histories.includes(key)) { wrap?.remove(); continue; }
      const snapshot = state.data[key];
      if (!wrap) {
        grid.querySelector('.map-loading')?.remove();
        wrap = document.createElement('div'); wrap.className = `map-wrap ${key === 'branch' ? 'branch-map' : ''}`; wrap.dataset.map = key;
        wrap.innerHTML = `<div class="map-header"><span class="history-label">${key === 'branch' ? 'ALTERED HISTORY' : 'ORIGINAL HISTORY'}</span><span class="map-tick"></span></div><div class="map-canvas"><svg class="town-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"></svg><div class="location-layer"></div><div class="agent-layer"></div><div class="map-coordinates">A SCHEMATIC OF ROME</div></div>`;
        grid.appendChild(wrap);
      }
      wrap.querySelector('.map-tick').textContent = snapshot.tick < 0 ? 'BEFORE DAWN' : `TICK ${String(snapshot.tick).padStart(2, '0')}`;
      const locations = snapshot.locations ?? [];
      const mapKey = JSON.stringify(locations);
      if (wrap.dataset.locations !== mapKey) {
        wrap.dataset.locations = mapKey;
        const byId = Object.fromEntries(locations.map((location) => [location.id, location]));
        const center = byId.forum ?? locations[0];
        let lines = '<path class="river" d="M 87 -5 C 80 22 100 33 87 58 S 86 92 97 110"/><path class="river-center" d="M 87 -5 C 80 22 100 33 87 58 S 86 92 97 110"/><path class="map-wall" d="M 14 16 L 72 10 L 86 34 L 83 80 L 60 92 L 15 81 L 6 44 Z"/>';
        if (center) lines += locations.filter((location) => location !== center).map((location) => `<path class="map-road" d="M ${Number(center.x)} ${Number(center.y)} L ${Number(location.x)} ${Number(location.y)}"/>`).join('');
        lines += locations.map((location, index) => { const next = locations[(index + 1) % locations.length]; return next ? `<path class="map-road-minor" d="M ${Number(location.x)} ${Number(location.y)} L ${Number(next.x)} ${Number(next.y)}"/>` : ''; }).join('');
        wrap.querySelector('svg').innerHTML = lines;
        wrap.querySelector('.location-layer').innerHTML = locations.map((location) => `<div class="map-location" style="left:${Number(location.x)}%;top:${Number(location.y)}%"><span class="location-icon ${esc(location.id)}" aria-hidden="true">${location.id === 'forum' ? 'Π' : location.id === 'harbour' ? '⚓' : location.id === 'temple' ? 'Λ' : '▥'}</span><span class="location-label">${esc(location.label ?? human(location.id))}</span></div>`).join('');
      }
      const layer = wrap.querySelector('.agent-layer');
      const grouped = {};
      for (const agent of snapshot.agents ?? []) (grouped[agent.location] ??= []).push(agent);
      const renderedIds = new Set();
      for (const [locationId, agents] of Object.entries(grouped)) {
        const location = locations.find((item) => item.id === locationId);
        if (!location) continue;
        agents.forEach((agent, index) => {
          const id = String(identity(agent)); renderedIds.add(id);
          let pin = Array.from(layer.children).find((element) => element.dataset.agent === id);
          if (!pin) { pin = document.createElement('button'); pin.className = 'agent-pin'; pin.dataset.agent = id; pin.dataset.timeline = key; layer.appendChild(pin); }
          pin.dataset.initials = (agent.name ?? id).slice(0, 1);
          pin.textContent = agent.name ?? id;
          pin.classList.toggle('selected', id === state.selectedAgent);
          pin.classList.toggle('dense', agents.length > 8);
          const columns = agents.length > 20 ? 6 : agents.length > 8 ? 4 : agents.length > 4 ? 3 : 2;
          const row = Math.floor(index / columns); const column = index % columns;
          const spread = agents.length > 8 ? 5 : state.data.branch ? 11 : 9;
          const x = Math.max(7, Math.min(93, Number(location.x) + (column - (Math.min(columns, agents.length) - 1) / 2) * spread));
          const y = Math.max(6, Math.min(95, Number(location.y) + 9 + row * (agents.length > 8 ? 5 : 7)));
          pin.style.left = `${x}%`; pin.style.top = `${y}%`;
          pin.setAttribute('aria-label', `Inspect ${agent.name ?? id}, ${agent.role ?? 'citizen'}, at ${location.label ?? human(locationId)} in ${key === 'branch' ? 'altered' : 'original'} history`);
          pin.title = `${agent.name ?? id} · ${human(agent.role ?? 'citizen')} · ${location.label ?? human(locationId)}`;
          pin.setAttribute('aria-pressed', String(id === state.selectedAgent && state.timeline === key));
        });
      }
      Array.from(layer.children).forEach((pin) => { if (!renderedIds.has(pin.dataset.agent)) pin.remove(); });
    }
  }

  function renderAgent() {
    const agent = selectedAgent(); const snapshot = active(); if (!agent) return;
    const id = identity(agent); state.selectedAgent = id;
    const beliefs = Object.entries(agent.beliefs ?? {});
    const decisions = array(agent.decisions).slice(-4).reverse();
    const inventory = typeof agent.inventory === 'object' ? Object.values(agent.inventory ?? {}).reduce((sum, value) => sum + (typeof value === 'number' ? value : 0), 0) : agent.inventory;
    const commitmentText = (item) => typeof item === 'string' ? item : `${item.quantity ?? '—'} grain units due at tick ${item.deadline ?? '—'} · ${human(item.status ?? 'open')}${item.fulfilled ? ` (${item.fulfilled} delivered)` : ''}`;
    const commitments = Array.isArray(agent.commitments) ? agent.commitments : Object.entries(agent.commitments ?? {}).map(([key, value]) => `${human(key)}: ${scalar(value)}`);
    const goals = Array.isArray(agent.goals) ? agent.goals : typeof agent.goals === 'string' ? [agent.goals] : Object.entries(agent.goals ?? {}).map(([key, value]) => `${human(key)}: ${scalar(value)}`);
    const goalsMarkup = goals.length ? `<div class="section-label">Current goals</div><ul class="compact-list">${goals.map((goal) => `<li>${esc(typeof goal === 'string' ? goal : scalar(goal))}</li>`).join('')}</ul>` : '';
    $('#agent-inspector').innerHTML = `<div class="agent-picker"><div class="agent-avatar" aria-hidden="true">${esc((agent.name ?? id).slice(0, 1))}</div><div><select id="agent-select" aria-label="Select citizen">${snapshot.agents.map((item) => `<option value="${esc(identity(item))}" ${identity(item) === id ? 'selected' : ''}>${esc(item.name ?? identity(item))}</option>`).join('')}</select><div class="agent-role">${esc(human(agent.role ?? 'Citizen'))} <span aria-hidden="true">/</span> ${state.timeline === 'branch' ? 'ALTERED' : 'ORIGINAL'}</div></div></div><div class="agent-resources"><div><span class="metric-label">Location</span><span class="agent-location">${esc(locationOf(agent.location))}</span></div><div><span class="metric-label">Cash</span><span class="metric-value">${esc(fmt(agent.cash))}</span><span class="metric-unit">den.</span></div><div><span class="metric-label">Grain</span><span class="metric-value">${esc(fmt(inventory))}</span><span class="metric-unit">units</span></div></div><div class="section-label">Current beliefs <span class="private-pill">LOCAL KNOWLEDGE ONLY</span></div>${beliefs.length ? beliefs.map(([key, belief]) => {
      const value = belief && typeof belief === 'object' ? belief : { value: belief };
      const evidence = array(value.evidence_ids ?? value.evidence ?? value.parents);
      return `<div class="belief-card"><div class="belief-key">${esc(human(key))}</div><div class="belief-value">${esc(human(value.value))}</div><div class="belief-meta">${value.as_of != null ? `<span>AS OF T${esc(value.as_of)}</span>` : ''}${value.root_count != null ? `<span>${esc(value.root_count)} ROOT${value.root_count === 1 ? '' : 'S'}</span>` : ''}${value.source_count != null ? `<span>${esc(value.source_count)} SOURCE${value.source_count === 1 ? '' : 'S'}</span>` : ''}${value.status ? `<span>${esc(human(value.status))}</span>` : ''}</div>${evidence.length ? `<div class="evidence-links">${evidence.map((event) => ref(typeof event === 'object' ? eventId(event) : event)).join('')}</div>` : ''}</div>`;
    }).join('') : '<p class="belief-none">This citizen has no recorded belief about the shipment. Information must reach them before it can guide a decision.</p>'}<p class="inspector-note">Sources count messengers. Roots count originating observations. Repetition can share a single root.</p>${experienceHistory(agent)}${goalsMarkup}${commitments.length ? `<div class="section-label">Commitments</div><ul class="compact-list">${commitments.map((commitment) => `<li>${esc(commitmentText(commitment))}</li>`).join('')}</ul>` : ''}${decisions.length ? `<div class="section-label">Recent decisions</div>${decisions.map((decision) => `<div class="decision-item"><strong>${esc(human(decision.action ?? decision.kind ?? 'Decision'))}</strong><span class="decision-time">T${esc(decision.tick ?? '—')}</span>${decision.reason ? `<div class="inspector-note">${esc(decision.reason)}</div>` : ''}<div class="decision-evidence">${decision.event_id != null ? ref(decision.event_id) : ''}${array(decision.evidence_ids ?? decision.parents).map((event) => ref(typeof event === 'object' ? eventId(event) : event)).join('')}</div></div>`).join('')}` : ''}${agent.relationships && Object.keys(agent.relationships).length ? `<div class="section-label">Recorded relationships</div><div class="relationship-list">${esc(JSON.stringify(agent.relationships))}</div>` : ''}`;
  }

  function experienceHistory(agent) {
    const experiences = array(agent.experiences).filter((experience) => experience.subject && ['observed', 'told'].includes(experience.kind)).reverse();
    if (!experiences.length) return '';
    return `<details class="local-history" ${$('#agent-inspector .local-history')?.open ? 'open' : ''}><summary>Information received <span class="count">${experiences.length}</span></summary><p class="inspector-note">Recent local experiences, including older and rejected claims. A recorded report is not automatically an accepted belief.</p>${experiences.slice(0, 12).map((experience) => {
      const current = agent.beliefs?.[`${experience.subject}.${experience.predicate}`];
      const older = current && experience.as_of < current.as_of;
      const contradictory = current && experience.value !== current.value;
      const status = experience.accepted ? older ? 'Older evidence' : 'Accepted on receipt' : 'Not accepted on receipt';
      return `<div class="experience-item"><div class="experience-heading"><span>${experience.kind === 'observed' ? 'DIRECT OBSERVATION' : `RELAYED BY ${esc(experience.source_agent ?? 'UNKNOWN')}`}</span><span>T${esc(experience.tick)}</span></div><div class="experience-value">${esc(human(experience.subject))} ${esc(human(experience.predicate).toLowerCase())}: ${esc(human(experience.value))} ${ref(experience.event_id)}</div><p class="experience-status ${!experience.accepted || contradictory ? 'contradictory' : ''}">${esc(status)}${contradictory ? ' · differs from current belief' : ''} · as of T${esc(experience.as_of)}</p>${experience.claimed_origin_observer || experience.claimed_origin_event != null ? `<p class="experience-origin">Claimed root: ${esc(experience.claimed_origin_observer ?? 'self')}${experience.claimed_origin_event != null ? ` ${ref(experience.claimed_origin_event)}` : ''}</p>` : ''}</div>`;
    }).join('')}${experiences.length > 12 ? `<p class="inspector-note">Showing the 12 most recent informational experiences from the retained local window.</p>` : ''}</details>`;
  }

  function renderTruth() {
    const world = active()?.world ?? {};
    const rows = [];
    for (const [key, value] of Object.entries(world.facts ?? {})) rows.push([human(key), typeof value === 'object' ? value.value ?? scalar(value) : value]);
    for (const key of ['price', 'supply', 'inventory', 'available_inventory', 'reserves']) if (world[key] != null) rows.push([human(key), world[key]]);
    $('#world-truth').innerHTML = `<p>Authoritative evaluator state in the ${state.timeline === 'branch' ? 'altered' : 'original'} world. A citizen can use a fact only after a legitimate local observation.</p>${rows.map(([key, value]) => `<div class="truth-row"><span>${esc(key)}</span><span>${esc(fmt(value))}</span></div>`).join('')}${rows.length ? '' : '<p>No world facts are recorded yet.</p>'}`;
  }

  function renderEvents() {
    const snapshot = active(); const events = snapshot?.events ?? [];
    $('#event-count').textContent = events.length.toLocaleString();
    const search = state.search.toLowerCase();
    const filtered = events.filter((event) => (state.filter === 'all' || category(event) === state.filter) && (!search || `${eventTitle(event)} ${eventType(event)} ${array(event.actors).join(' ')} ${JSON.stringify(event.payload)}`.toLowerCase().includes(search)));
    $('#event-list').innerHTML = filtered.length ? filtered.slice(-300).reverse().map((event) => `<button class="event-row ${String(eventId(event)) === String(state.selectedEvent) ? 'selected' : ''}" data-event="${esc(eventId(event))}" aria-pressed="${String(eventId(event)) === String(state.selectedEvent)}"><span class="event-time">T${esc(String(event.tick).padStart(2, '0'))}</span><span class="event-dot ${category(event)}"></span><span><span class="event-row-title">${esc(eventTitle(event))}</span><span class="event-row-meta">#${esc(eventId(event))} · ${esc(human(eventType(event)))}${event.location ? ` · ${esc(locationOf(event.location))}` : ''}</span></span><span class="event-row-arrow" aria-hidden="true">›</span></button>`).join('') : `<div class="empty-state"><span aria-hidden="true">·</span><p>${events.length ? 'No events match this filter.' : 'The ledger is open. Run or step the city to begin its history.'}</p></div>`;
    if (state.selectedEvent != null) {
      const event = events.find((item) => String(eventId(item)) === String(state.selectedEvent));
      if (event && $('#event-detail').dataset.event !== `${state.timeline}:${state.selectedEvent}`) selectEvent(eventId(event), false);
    } else {
      delete $('#event-detail').dataset.event;
      $('#event-detail').innerHTML = '<div class="trace-empty"><span class="trace-glyph" aria-hidden="true">╱─╲</span><p>Every consequence has a history.</p><span>Select an event to inspect its evidence and structural ancestry.</span></div>';
    }
  }

  async function selectEvent(id, updateList = true) {
    state.selectedEvent = id;
    const event = active()?.events?.find((item) => String(eventId(item)) === String(id));
    if (!event) { toast(`Event #${id} is not in this history.`); return; }
    const detail = $('#event-detail'); detail.dataset.event = `${state.timeline}:${id}`;
    const parents = array(event.parents ?? event.payload?.parents ?? event.payload?.evidence_ids);
    detail.innerHTML = `<div class="event-kicker">EVENT #${esc(id)} · TICK ${esc(event.tick)} · ${esc(human(eventType(event)))}</div><h3>${esc(eventTitle(event))}</h3><div class="event-data">${event.actors?.length ? `<div><span>Citizens</span><span>${esc(event.actors.map((actor) => nameOf(actor)).join(', '))}</span></div>` : ''}${event.location ? `<div><span>Location</span><span>${esc(locationOf(event.location))}</span></div>` : ''}${event.scope ? `<div><span>Scope</span><span>${esc(human(event.scope))}</span></div>` : ''}${Object.entries(event.payload ?? {}).filter(([key, value]) => ['action', 'value', 'prop', 'as_of', 'speaker', 'listener', 'root_source', 'loss', 'regret', 'reason', 'root_count', 'source_count'].includes(key) && typeof value !== 'object').map(([key, value]) => `<div><span>${esc(human(key))}</span><span>${esc(fmt(value))}</span></div>`).join('')}</div><div class="trace-heading">Structural ancestry</div><div id="trace-content">${parents.length ? `<div class="evidence-links">${parents.map((parent) => ref(typeof parent === 'object' ? eventId(parent) : parent)).join('')}</div>` : '<p class="trace-note">No parent events recorded. This may be an initial condition or exogenous observation.</p>'}<p class="trace-note">Loading recorded dependency trace…</p></div>${raw(event, 'Full recorded event')}`;
    if (updateList) $('#event-list').querySelectorAll('[data-event]').forEach((row) => { const selected = String(row.dataset.event) === String(id); row.classList.toggle('selected', selected); row.setAttribute('aria-pressed', String(selected)); });
    const serial = ++state.traceSerial;
    try {
      const trace = await api(`/api/trace?event_id=${encodeURIComponent(id)}&timeline=${encodeURIComponent(state.timeline)}`);
      if (serial !== state.traceSerial) return;
      renderTrace(trace, event);
    } catch (error) {
      if (serial !== state.traceSerial) return;
      $('#trace-content').innerHTML = `${parents.length ? `<div class="evidence-links">${parents.map((parent) => ref(typeof parent === 'object' ? eventId(parent) : parent)).join('')}</div>` : ''}<p class="trace-note">${esc(error.message)} Direct parents remain available in the recorded event.</p>`;
    }
  }

  function renderTrace(trace, event) {
    let nodes = Array.isArray(trace) ? trace : trace.events ?? trace.ancestors ?? trace.nodes ?? trace.trace ?? [];
    if (!Array.isArray(nodes)) nodes = Object.values(nodes);
    nodes = nodes.map((node) => typeof node === 'object' ? node.event ?? node : active()?.events?.find((item) => String(eventId(item)) === String(node))).filter(Boolean);
    nodes = nodes.filter((node) => eventId(node) != null).sort((a, b) => a.tick - b.tick || Number(eventId(a)) - Number(eventId(b)));
    const parents = array(event.parents ?? event.payload?.parents);
    $('#trace-content').innerHTML = `${nodes.length ? `<ol class="trace-list">${nodes.map((node) => `<li class="trace-node">${ref(eventId(node))}<span>${esc(eventTitle(node))}</span><span class="decision-time">T${esc(node.tick)}</span></li>`).join('')}</ol>` : parents.length ? `<div class="evidence-links">${parents.map((parent) => ref(typeof parent === 'object' ? eventId(parent) : parent)).join('')}</div>` : '<p class="trace-note">No earlier dependencies recorded for this event.</p>'}<p class="trace-note">This is recorded evidence ancestry. A shared ancestor alone does not establish that an outcome required it.</p>${trace.necessity_available ? `<button class="button necessity-button" id="necessity-button" data-necessity="${esc(eventId(event))}">Test counterfactual necessity</button><div id="necessity-result"></div>` : ''}${raw(trace, 'Inspect trace data')}`;
  }

  function pendingMessages() {
    const snapshot = state.data?.original;
    return array(snapshot?.pending_messages ?? snapshot?.messages).filter((message) => message.status !== 'delivered' && message.delivered !== true && (message.delivery_tick == null || message.delivery_tick > snapshot.tick));
  }

  function renderInterventions() {
    const snapshot = state.data.original;
    const prior = $('#intervention-agent').value || state.selectedAgent;
    $('#intervention-agent').innerHTML = (snapshot.agents ?? []).map((agent) => `<option value="${esc(identity(agent))}" ${String(identity(agent)) === String(prior) ? 'selected' : ''}>${esc(agent.name ?? identity(agent))} · ${esc(human(agent.role ?? 'citizen'))}</option>`).join('');
    const pending = pendingMessages();
    const oldMessage = $('#intervention-message').value;
    $('#intervention-message').innerHTML = pending.length ? pending.map((message) => `<option value="${esc(message.event_id ?? message.id)}" ${String(message.event_id ?? message.id) === oldMessage ? 'selected' : ''}>#${esc(message.event_id ?? message.id)} · ${esc(nameOf(message.speaker, snapshot))} → ${esc(nameOf(message.listener, snapshot))} · T${esc(message.delivery_tick ?? '?')}</option>`).join('') : '<option value="">No messages awaiting delivery</option>';
    $('#pending-caption').textContent = pending.length ? `${pending.length} message${pending.length === 1 ? '' : 's'} queued in the original world. Only undelivered messages can be changed.` : 'Advance the original city until a message is queued, then pause to intervene.';
    $('#correction-fields .field-help').textContent = snapshot.tick < 0 ? 'Step or run the city first, so the shipment can be inspected.' : 'The citizen receives a new observation of the actual shipment state at this tick.';
    updateInterventionFields();
    $('#branch-receipt').hidden = !state.data.branch;
    if (state.data.branch) {
      $('#branch-receipt').className = 'branch-receipt';
      const interventionEvent = state.data.branch.events.find((event) => String(event.category ?? '').startsWith('intervention'));
      $('#branch-receipt').innerHTML = `<strong>⑂ Two histories are live.</strong><p>Shared history through tick ${esc(state.data.branch.parent_tick ?? '—')}. Run or step to advance both worlds.</p>${interventionEvent ? `<p>Recorded intervention ${ref(eventId(interventionEvent), 'branch')}</p>` : ''}<a href="#comparison-panel">Inspect the comparison <span aria-hidden="true">↓</span></a>`;
      $('#fork-note').textContent = 'Creating another branch replaces the altered history. The original history stays intact.';
    } else $('#fork-note').textContent = 'The original history stays intact. Both worlds use the same rules and keyed randomness.';
  }

  function updateInterventionFields() {
    const kind = $('#intervention-kind').value;
    $('#correction-fields').hidden = kind !== 'correction';
    $('#message-fields').hidden = !['remove_message', 'replace_message'].includes(kind);
    $('#replacement-fields').hidden = kind !== 'replace_message';
    updateControls();
  }

  function canFork() {
    if (!state.data?.original) return false;
    const kind = $('#intervention-kind').value;
    if (['remove_message', 'replace_message'].includes(kind)) return Boolean($('#intervention-message').value);
    if (kind === 'correction') return state.data.original.tick >= 0 && Boolean($('#intervention-agent').value);
    return true;
  }

  async function fork() {
    pause(); if (state.busy || !canFork()) return;
    state.busy = true; clearError(); updateControls();
    const kind = $('#intervention-kind').value;
    const intervention = { kind };
    if (kind === 'correction') intervention.agent = $('#intervention-agent').value;
    if (['remove_message', 'replace_message'].includes(kind)) intervention.event_id = Number($('#intervention-message').value);
    if (kind === 'replace_message') intervention.value = $('#replacement-value').value;
    try { await accept(await api('/api/fork', intervention)); toast('History forked. Run the city to see what changes.'); }
    catch (error) { showError(error); }
    finally { state.busy = false; updateControls(); }
  }

  function comparisonRows(original, branch, path = '', depth = 0) {
    if (JSON.stringify(original) === JSON.stringify(branch)) return [];
    if (depth > 3 || original == null || branch == null || typeof original !== 'object' || typeof branch !== 'object' || Array.isArray(original) || Array.isArray(branch)) return [[path || 'Value', original, branch]];
    return Array.from(new Set([...Object.keys(original), ...Object.keys(branch)])).flatMap((key) => comparisonRows(original[key], branch[key], path ? `${path} · ${human(key)}` : human(key), depth + 1));
  }

  function diffTable(rows, title) {
    const valueMarkup = (value) => value?.__event ? `${esc(value.label)}<div class="evidence-links">${ref(value.event_id, value.timeline)}</div>` : esc(fmt(value));
    return `<section class="comparison-section"><h3>${esc(title)} <span class="count">${rows.length}</span></h3>${rows.length ? `<table class="diff-table"><thead><tr><th scope="col">Changed state</th><th scope="col">Original</th><th scope="col">Altered</th></tr></thead><tbody>${rows.slice(0, 30).map(([key, original, branch]) => `<tr><td>${esc(key)}</td><td>${valueMarkup(original)}</td><td>${valueMarkup(branch)}</td></tr>`).join('')}</tbody></table>${rows.length > 30 ? `<p class="no-difference">${rows.length - 30} more differences are available in the complete comparison below.</p>` : ''}` : '<p class="no-difference">No difference at this moment.</p>'}</section>`;
  }

  function renderComparison() {
    const branch = state.data.branch; $('#comparison-panel').hidden = !branch; if (!branch) return;
    const original = state.data.original;
    $('#comparison-tick').textContent = `ORIGINAL T${original.tick} / ALTERED T${branch.tick}`;
    const stats = [['Grain price', original.world?.price, branch.world?.price, 'denarii / unit'], ['Decision regret', original.metrics?.total_regret, branch.metrics?.total_regret, 'evaluator loss relative to best action'], ['Consequential decisions', original.metrics?.decision_count ?? original.decisions?.length, branch.metrics?.decision_count ?? branch.decisions?.length, 'recorded opportunities'], ['Reservations', original.metrics?.reserves, branch.metrics?.reserves, 'recorded reserve actions']];
    const originalAgents = Object.fromEntries((original.agents ?? []).map((agent) => [identity(agent), agent]));
    const branchAgents = Object.fromEntries((branch.agents ?? []).map((agent) => [identity(agent), agent]));
    const beliefRows = [], agentRows = [], relationshipRows = [];
    for (const id of new Set([...Object.keys(originalAgents), ...Object.keys(branchAgents)])) {
      const left = originalAgents[id] ?? {}; const right = branchAgents[id] ?? {};
      const comparableBeliefs = (beliefs) => Object.fromEntries(Object.entries(beliefs ?? {}).map(([key, value]) => [key, Object.fromEntries(Object.entries(value ?? {}).filter(([field]) => field !== 'evidence_ids'))]));
      beliefRows.push(...comparisonRows(comparableBeliefs(left.beliefs), comparableBeliefs(right.beliefs), id));
      agentRows.push(...comparisonRows({ cash: left.cash, inventory: left.inventory, commitments: left.commitments, location: left.location }, { cash: right.cash, inventory: right.inventory, commitments: right.commitments, location: right.location }, id));
      relationshipRows.push(...comparisonRows(left.relationships, right.relationships, id));
    }
    const actionRows = [];
    const decisionsA = array(original.decisions).filter((decision) => decision.tick > (branch.parent_tick ?? -1));
    const decisionsB = array(branch.decisions).filter((decision) => decision.tick > (branch.parent_tick ?? -1));
    const decisionKey = (decision, index) => `${decision.tick ?? '?'} · ${decision.agent ?? decision.agent_id ?? decision.actor ?? index}`;
    const mapA = Object.fromEntries(decisionsA.map((decision, index) => [decisionKey(decision, index), decision]));
    const mapB = Object.fromEntries(decisionsB.map((decision, index) => [decisionKey(decision, index), decision]));
    for (const key of new Set([...Object.keys(mapA), ...Object.keys(mapB)])) {
      const a = mapA[key], b = mapB[key];
      const actionValue = (decision, timeline) => decision ? { __event: true, label: `${human(decision.action)}${decision.loss != null ? ` · loss ${fmt(decision.loss)}` : ''}`, event_id: decision.event_id, timeline } : 'No decision';
      if (a?.action !== b?.action || a?.loss !== b?.loss || a?.predicted_value !== b?.predicted_value) actionRows.push([`T${key}`, actionValue(a, 'original'), actionValue(b, 'branch')]);
    }
    const relationA = original.world?.relationships ?? original.relationships; const relationB = branch.world?.relationships ?? branch.relationships;
    if (Array.isArray(state.data.comparison?.relationships)) relationshipRows.push(...state.data.comparison.relationships.map((row) => [`${row.listener} ← ${row.speaker}`, row.baseline, row.branch]));
    else relationshipRows.push(...comparisonRows(relationA, relationB));
    const comparableWorld = (world) => Object.fromEntries(Object.entries(world ?? {}).filter(([key]) => key !== 'relationships'));
    const worldRows = comparisonRows(comparableWorld(original.world), comparableWorld(branch.world));
    const messageKey = (message) => `${message.speaker} → ${message.listener} · T${message.delivery_tick}`;
    const queueA = Object.fromEntries(array(original.messages).map((message) => [messageKey(message), message]));
    const queueB = Object.fromEntries(array(branch.messages).map((message) => [messageKey(message), message]));
    const messageRows = [];
    for (const key of new Set([...Object.keys(queueA), ...Object.keys(queueB)])) {
      const a = queueA[key], b = queueB[key];
      if (!a || !b || a.value !== b.value || a.as_of !== b.as_of) messageRows.push([key, a ? { __event: true, label: `${human(a.value)} · as of T${a.as_of}`, event_id: a.event_id, timeline: 'original' } : 'No queued message', b ? { __event: true, label: `${human(b.value)} · as of T${b.as_of}`, event_id: b.event_id, timeline: 'branch' } : 'No queued message']);
    }
    const differenceCount = worldRows.length + beliefRows.length + agentRows.length + actionRows.length + relationshipRows.length + messageRows.length;
    $('#comparison-content').innerHTML = `<div class="comparison-intro"><p>${differenceCount ? `${differenceCount} displayed state, action, or queued-message differences are computed from these live snapshots.` : 'The worlds currently have matching displayed outcomes. Continue both histories to test whether the intervention changes decisions.'} Shared prefix ends at tick ${esc(branch.parent_tick ?? '—')}.</p></div><div class="comparison-summary">${stats.map(([label, a, b, note]) => `<div class="compare-stat"><span class="metric-label">${esc(label)}</span><div class="compare-values"><span>${esc(fmt(a))}</span><span class="compare-arrow" aria-hidden="true">→</span><span>${esc(fmt(b))}</span></div><div class="compare-labels">ORIGINAL → ALTERED</div><div class="metric-subline">${esc(note)}</div></div>`).join('')}</div><div class="comparison-sections">${diffTable(actionRows, 'Changed actions')}${diffTable(worldRows, 'World state')}${diffTable(beliefRows, 'Private beliefs & evidence')}${diffTable(agentRows, 'Resources & commitments')}${diffTable(relationshipRows, 'Relationships')}${diffTable(messageRows, 'Information in transit')}</div><div class="comparison-raw">${raw(state.data.comparison ?? { world: worldRows, beliefs: beliefRows, actions: actionRows, agents: agentRows, relationships: relationshipRows, messages: messageRows }, 'Complete engine comparison')}</div>`;
  }

  function selectHistory(timeline) {
    if (timeline === 'branch' && !state.data.branch) return;
    state.timeline = timeline; state.traceSerial += 1; delete $('#event-detail').dataset.event;
  }

  document.addEventListener('click', async (event) => {
    const agent = event.target.closest('[data-agent]');
    if (agent) { selectHistory(agent.dataset.timeline); state.selectedAgent = agent.dataset.agent; render(); return; }
    const eventLink = event.target.closest('[data-event-ref]');
    if (eventLink) { selectHistory(eventLink.dataset.timeline ?? state.timeline); render(); await selectEvent(eventLink.dataset.eventRef); $('#ledger-heading').scrollIntoView({ behavior: 'smooth', block: 'nearest' }); return; }
    const row = event.target.closest('[data-event]');
    if (row) { await selectEvent(row.dataset.event); return; }
    const filter = event.target.closest('[data-filter]');
    if (filter) { state.filter = filter.dataset.filter; document.querySelectorAll('[data-filter]').forEach((button) => { button.classList.toggle('active', button === filter); button.setAttribute('aria-pressed', String(button === filter)); }); renderEvents(); return; }
    const necessity = event.target.closest('[data-necessity]');
    if (necessity) {
      necessity.disabled = true; $('#necessity-result').innerHTML = '<p class="trace-note">Replaying the selected intervention…</p>';
      try { const result = await api(`/api/necessity?event_id=${encodeURIComponent(necessity.dataset.necessity)}&timeline=${encodeURIComponent(state.timeline)}`); $('#necessity-result').innerHTML = `<div class="necessity-result">${raw(result, 'Counterfactual test result')}</div>`; }
      catch (error) { $('#necessity-result').innerHTML = `<p class="error-inline">${esc(error.message)}</p>`; }
      finally { necessity.disabled = false; }
    }
  });
  document.addEventListener('change', (event) => {
    if (event.target.id === 'agent-select') { state.selectedAgent = event.target.value; renderMaps(); renderAgent(); }
    if (event.target.id === 'timeline-select') { selectHistory(event.target.value); render(); }
    if (event.target.id === 'intervention-kind') updateInterventionFields();
    if (event.target.id === 'intervention-message') updateControls();
    if (event.target.id === 'speed' && state.running) schedule();
  });
  $('#event-search').addEventListener('input', (event) => { state.search = event.target.value; renderEvents(); });
  $('#run-button').addEventListener('click', toggleRun);
  $('#step-button').addEventListener('click', () => { pause(); step(); });
  $('#reset-button').addEventListener('click', reset);
  $('#settings-form').addEventListener('submit', reset);
  $('#fork-button').addEventListener('click', fork);
  document.addEventListener('keydown', (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,select,textarea,button,summary,a,[contenteditable]')) return;
    if (event.code === 'Space') { event.preventDefault(); if (!$('#run-button').disabled) toggleRun(); }
    if (event.code === 'ArrowRight') { event.preventDefault(); if (!$('#step-button').disabled) { pause(); step(); } }
    if (event.key === 'Escape') $('.settings').open = false;
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  api('/api/state').then(accept).catch((error) => { showError(error); $('#playback-status').textContent = 'Disconnected'; });
})();
