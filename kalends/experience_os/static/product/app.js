'use strict';
/* The shell is deliberately independent of the retained scene. Routes redraw
 * text, while life-keyed iframe nodes and pending operations keep their identity. */
(function (global) {
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  class StaleRequest extends Error { constructor() { super('This view has changed.'); this.name = 'StaleRequest'; } }
  class LifeRequestGate {
    constructor() { this.id = null; this.epoch = 0; this.controllers = new Set(); }
    select(id) { if (this.id === id) return; this.id = id; this.epoch++; for (const c of this.controllers) c.abort(); this.controllers.clear(); }
    async run(task) {
      const id = this.id, epoch = this.epoch, controller = new AbortController(); this.controllers.add(controller);
      try { const result = await task(controller.signal); if (id !== this.id || epoch !== this.epoch) throw new StaleRequest(); return result; }
      catch (error) { if (id !== this.id || epoch !== this.epoch) throw new StaleRequest(); throw error; }
      finally { this.controllers.delete(controller); }
    }
  }
  class LifeRevisionGate {
    constructor() { this.latest = new Map(); }
    admit(id, data) {
      const revision=data?.life?.revision??data?.history?.revision??data?.snapshot?.command_count;
      if(!Number.isInteger(revision)||revision<0)return false;
      if(revision<(this.latest.get(id)??-1))return false;
      this.latest.set(id,revision);return true;
    }
  }
  function acceptsSceneMessage(event, frame, origin, id) {
    return !!frame && event.origin === origin && event.source === frame.contentWindow &&
      (event.data?.life_id === id || event.data?.experience === id);
  }
  function describeAction(action, names = {}) {
    const name = id => names[id] || ({team_a:'Amir',team_b:'Mira',team_c:'Lin'}[id]) || id || 'the participant';
    if (!action) return 'A supported choice';
    if (action.action === 'share') return `Ask ${name(action.recipient)} to share a dated report`;
    if (action.action === 'inspect') return 'Buy a direct instrument inspection';
    if (action.action === 'commit') return `Promise ${action.quantity} units to ${name(action.recipient)}`;
    if (action.action === 'allocate') return 'Commit the proposed allocation';
    if (action.action === 'wait') return 'Wait in the world';
    return String(action.action || 'choice').replaceAll('_', ' ');
  }
  const core = {escapeHTML, LifeRequestGate, LifeRevisionGate, StaleRequest, acceptsSceneMessage, describeAction};
  if (typeof module !== 'undefined' && module.exports) module.exports = core;
  if (typeof document === 'undefined') return;

  const $ = selector => document.querySelector(selector), $$ = selector => [...document.querySelectorAll(selector)], esc = escapeHTML;
  const API = '/product/api/';
  const S = {catalog:null, id:null, data:null, routeEpoch:0, conversationEpoch:0, proposalEpoch:0, gate:new LifeRequestGate(), revisions:new LifeRevisionGate(), readVersions:new Map(), chapterLimits:new Map(), frames:new Map(), views:new Map(), drafts:new Map(), selected:new Map(), pending:new Set(), uncertain:new Set(), proposal:null, reflection:null, storyTab:'history', returnSeen:new Set(), lab:null, toastTimer:null, lastSceneRequest:0, sessionId:crypto.randomUUID(), activeSince:performance.now()};
  class ApiError extends Error { constructor(message, code, status) { super(message); this.name='ApiError'; this.code=code; this.status=status; } }
  async function api(path, body, signal) {
    const response = await fetch(API + path, body === undefined ? {cache:'no-store',signal} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
    let result;
    try { result = await response.json(); } catch (_) { throw new ApiError('The local server returned an unreadable response. Refresh to reconcile this life.', 'unreadable_response', response.status); }
    if (!response.ok || result.error) throw new ApiError(typeof result.error === 'string' ? result.error : result.error?.message || result.message || 'The local request could not be completed.', result.code || result.error?.code, response.status);
    return result;
  }
  function status(message, duration = 6500) { const node=$('#global-status'); node.textContent=message; node.hidden=false; clearTimeout(S.toastTimer); S.toastTimer=setTimeout(()=>{node.hidden=true;},duration); }
  function notifyError(error) { if (error instanceof StaleRequest || error.name==='AbortError') return; status(error.message || 'The local request could not be completed.',10000); }
  function timeLabel(minute,setting) { const n=Number(minute||0);if(setting==='pompeii'||setting===undefined&&S.data?.snapshot?.setting==='pompeii')return `World minute ${n.toLocaleString()}`;return `Day ${Math.floor(n/1440)+1} · ${String(Math.floor(n%1440/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`; }
  function personName(id) { return (S.data?.people || S.data?.history?.people || []).find(p=>p.id===id)?.name || ({team_a:'Amir',team_b:'Mira',team_c:'Lin',Player:S.data?.snapshot?.setting==='commons'?'You':'Aelia'}[id]) || id; }
  function human(text) { return String(text||'').replace(/team_[abc]|Player/g, match=>personName(match)); }
  function text(value) { if (typeof value==='string') return value; return value?.text || value?.body || value?.title || value?.label || ''; }
  function metadata(data) { return data?.life || data || {}; }
  function lifeId(life) { return life.id || life.life_id || life.experience; }
  function lifeURL(id, suffix='') { return '/lives/'+encodeURIComponent(id)+suffix; }
  function savedLives() { return [...S.catalog?.lives||[],...S.catalog?.examples||[],...S.catalog?.failures||[]].sort((a,b)=>String(b.updated_at||b.created_at||'').localeCompare(String(a.updated_at||a.created_at||''))); }
  function usableLives() { return savedLives().filter(l=>!l.example && !['incompatible','incompatible_version','writer_conflict'].includes(l.save_status)); }
  function template(id) { return S.catalog?.templates?.find(t=>t.id===id); }
  function isPompeii(t) { return /pompeii/i.test([t?.id,t?.template_id,t?.setting,t?.adapter].filter(Boolean).join(' ')); }
  function badges(t) { return (t.badges || (isPompeii(t)?['Historical fiction','3D','Persistent life']:['Decision experience','Conversation & planning','Persistent consequences'])).map(b=>`<span class="badge">${esc(b)}</span>`).join(''); }
  function orbit(label='Illustration of three teams sharing an instrument') { return `<div class="observatory-art world-card-visual" role="img" aria-label="${esc(label)}"><div class="orbit-diagram"><span></span><span></span><span></span></div><span class="small-label">Concept diagram · playable decision experience</span></div>`; }
  function worldCard(t) {
    const pompeii=isPompeii(t), id=encodeURIComponent(t.id);
    return `<article class="world-card">${pompeii?`<div class="world-card-visual"><img src="${esc(t.preview_url||'/product/assets/hero.png')}" alt="An actual Kalends Pompeii prototype capture with an inhabited neighborhood" loading="lazy"><span class="small-label">Actual prototype capture</span></div>`:orbit()}<div class="world-card-body"><h3>${esc(pompeii?'Pompeii':'Shared Observatory')}</h3><div class="world-subtitle">${esc(t.subtitle||(pompeii?'A place in the city':'Three teams, one instrument'))}</div><p>${esc(t.description||(pompeii?'Work, trade and navigate obligations in a small Roman-inspired neighborhood. Your decisions become part of your local history.':'Coordinate competing requests with incomplete information. Find out what your promises mean when the instrument’s capacity is revealed through events.'))}</p><div class="badges">${badges(t)}</div><div class="card-bottom"><small>${pompeii?'A small fictional neighborhood, not a full reconstructed city.':'A fictional coordination task. Training benefit is untested.'}</small><a class="text-link" href="/worlds/${id}">Explore <span aria-hidden="true">↗</span></a></div></div></article>`;
  }
  function pageHead(label, title, description='') { return `<div class="page-intro"><p class="eyebrow">${esc(label)}</p><h1>${title}</h1>${description?`<p>${description}</p>`:''}</div>`; }
  function homePage() {
    const recent=usableLives()[0], worlds=S.catalog.templates || [];
    return `<div class="page hero"><div class="hero-copy"><p class="eyebrow">Kalends · Early experience prototype</p><h1>Enter a world.<br><em>Leave a history.</em></h1><p class="intro-copy">Make choices, build relationships, and return to the consequences. Explore two early worlds whose people and institutions keep track of what happens.</p><div class="hero-actions"><a class="button" href="${recent?lifeURL(lifeId(recent)):'/worlds'}">${recent?'Continue your world':'Explore worlds'} <span aria-hidden="true">↗</span></a><a class="text-link" href="${recent?'/worlds':'/#remember'}">${recent?'Explore worlds':'See how a world remembers'} <span aria-hidden="true">↘</span></a></div><p class="capability-note">Two playable prototypes. Saved locally by this installation.<br>Worlds advance when you play or choose to advance time.</p></div><figure class="hero-visual"><img class="hero-image" src="/product/assets/hero.png" alt="Actual Pompeii prototype: Aelia in a small Roman-inspired neighborhood" fetchpriority="high"><span class="image-label"><span class="live-dot"></span>Pompeii · A place in the city</span><figcaption><span>An actual prototype capture</span><span>One neighborhood. A history of your own.</span></figcaption></figure></div><section class="page premise section-rule" id="remember"><div class="section-topline"><p class="eyebrow">A world continues through what happens</p><p class="fine-print">The promise is persistence.<br>The proof is in the record.</p></div><div class="premise-intro"><h2>A choice is only the beginning.</h2></div><div class="premise-grid"><article class="premise-step"><span class="step-number">01</span><h3>You make a promise.</h3><p>A delivery, a shared resource, a commitment to someone. Review the actual terms before your choice becomes part of the world.</p></article><article class="premise-step"><span class="step-number">02</span><h3>Someone acts on it.</h3><p>People have their own work and information. The world executes what follows; requested, promised and delivered are different things.</p></article><article class="premise-step"><span class="step-number">03</span><h3>You return to what followed.</h3><p>Read an accepted choice, its later consequence and the dated evidence. Continue the same life from its saved moment.</p></article></div><p class="fine-print" style="margin-top:28px;margin-bottom:0">These panels describe supported interactions. They are not events inserted into your life. <a href="/research">Read the saved-life evidence</a>.</p></section><section class="page worlds-section section-rule"><div class="worlds-heading"><h2>Two places to begin.<br>Two ways to inhabit a world.</h2><p>Different settings. The same promise: what happens becomes part of a saved history.</p></div><div class="world-grid">${worlds.map(worldCard).join('')}</div></section><section class="page" style="padding-top:0"><div class="research-band"><div><p class="eyebrow">Built alongside a research program</p><h2>What does a world<br>really remember?</h2></div><div><p>Kalends studies memory, information and persistent consequences. The prototypes are working experiments, with results and limits you can inspect.</p><a class="text-link" href="/research">Explore the research <span aria-hidden="true">↗</span></a></div></div></section>`;
  }
  function worldsPage() { return `<div class="page">${pageHead('Choose a world','A place to begin.','Enter an existing experience. Every new life gets its own saved history; your other worlds stay intact.')}<div class="world-grid">${(S.catalog.templates||[]).map(worldCard).join('')}</div></div>`; }
  function detailPage(id) {
    const t=template(id); if(!t) return errorPage('World unavailable','This installation does not contain that world.','/worlds','Choose an available world');
    const pompeii=isPompeii(t), title=pompeii?'Pompeii':'Shared Observatory';
    return `<div class="page"><div class="breadcrumbs"><a href="/worlds">Worlds</a> / ${esc(title)}</div><div class="world-detail"><div><p class="eyebrow">${pompeii?'Historical fiction · An inhabited neighborhood':'Decision experience · A shared instrument'}</p><h1>${esc(title)}<br><em>${esc(t.subtitle||(pompeii?'A place in the city.':'Three teams, one instrument.'))}</em></h1><p>${esc(t.description||'')}</p><div class="badges">${badges(t)}</div><div class="detail-inset"><h2>Who you are here</h2><p>${esc(t.role||(pompeii?'You are Aelia, finding your place in a small Roman-inspired neighborhood.':'You coordinate a consortium with three research teams, a shared instrument and finite inspection credits.'))}</p><p>${esc(t.opening||(pompeii?'Walk, meet the people nearby and understand your existing agreement before choosing what to take on.':'Each team has legitimate work to complete. Ask about dated evidence before making promises, then choose how to allocate the instrument.'))}</p><ul class="detail-list">${(t.actions || (pompeii?['Walk and look around the neighborhood.','Talk to nearby people and review supported choices.','Keep, miss or repair obligations over simulated time.']:['Ask the systems team for a dated report.','Promise capacity and review an allocation.','Advance to settlement and read what was delivered.'])).map(a=>`<li>${esc(text(a)||a)}</li>`).join('')}</ul></div><button class="button" data-start="${esc(t.id)}">Begin a new life <span aria-hidden="true">→</span></button><p class="start-note">Creates a separate local journal. Existing lives are preserved.<br>${pompeii?'The 3D scene loads after you enter. The setting combines sourced context and fictional microhistory.':'A fictional decision task. No accredited astronomy or human training benefit is claimed.'}</p></div><figure>${pompeii?`<img class="detail-image" src="${esc(t.preview_url||'/product/assets/hero.png')}" alt="Actual Pompeii prototype capture"><figcaption class="fine-print">Actual prototype capture. Full controls appear when you enter.</figcaption>`:orbit()}<div class="detail-inset"><h2>Your pace, your history.</h2><p>The world does not run while this local server is stopped. Return to a saved moment, or explicitly choose to advance time.</p><a class="text-link" href="/your-worlds">Continue an existing life <span aria-hidden="true">↗</span></a></div></figure></div></div>`;
  }
  function savesPage() {
    const lives=savedLives();
    return `<div class="page">${pageHead('Your worlds','Pick up where you left off.','Each life has its own choices, people and history. Nothing progressed simply because you were away.')}<div class="save-grid">${lives.filter(l=>!l.example).map((l,i)=>saveCard(l,i===0)).join('')}</div>${!lives.some(l=>!l.example)?`<div class="empty-state"><p class="eyebrow">Your first history starts here</p><h2>Choose a place to begin.</h2><p>Your choices will be saved as part of that world’s history. Two supported prototypes are ready to explore.</p><a class="button" href="/worlds">Explore worlds <span aria-hidden="true">↗</span></a></div>`:''}${lives.some(l=>l.example)?`<section style="margin-top:48px"><h2>Recorded research lives</h2><p class="fine-print">Read-only examples from actual runs. They are kept separate from your personal worlds.</p><div class="save-grid">${lives.filter(l=>l.example).map(l=>saveCard(l,false)).join('')}</div></section>`:''}</div>`;
  }
  function saveCard(l, recent) {
    const id=lifeId(l), unavailable=['incompatible','incompatible_version','writer_conflict'].includes(l.save_status), unresolved=(l.unresolved||[])[0];
    return `<article class="save-card"><p class="eyebrow">${l.example?'Recorded example':recent?'Most recently used':'Saved life'}</p><h2>${esc(l.title||template(l.template_id)?.title||'Saved world')}</h2><p class="save-person">${esc(l.participant||(/pompeii/i.test(l.template_id||id)?'Aelia':'Consortium coordinator'))} · ${esc(isPompeii(l)?`Day ${l.day||Math.floor((l.minute||0)/1440)+1} · ${timeLabel(l.minute,'pompeii')}`:timeLabel(l.minute,'commons'))}${l.location?' · '+esc(l.location):''}</p><p class="save-summary">${esc(unavailable?'This journal could not be opened. Its saved contents have been preserved.':text(unresolved)||`Paused ${l.location?'at '+l.location:'at its saved moment'}. Continue when you choose.`)}</p><div class="save-actions">${!unavailable?`<a class="button" href="${lifeURL(id)}">${l.example?'Inspect example':'Continue'} <span aria-hidden="true">→</span></a><a class="text-link" href="${lifeURL(id,'/history')}">Your story <span aria-hidden="true">↗</span></a>`:`<button class="button secondary" data-save-diagnostic="${esc(id)}">Show diagnostics</button>`}</div><span class="save-status">${esc(l.example?'Read-only example · Original preserved':saveStatus(l.save_status))}</span></article>`;
  }
  function saveStatus(value) { return ({saving:'Saving…',saved:'Saved on this installation',error:'Save error · Your previous history is preserved',incompatible:'Incompatible save · Preserved for inspection',incompatible_version:'Incompatible version · Preserved for inspection',writer_conflict:'Another writer is active'})[value] || 'Saved locally by this installation'; }
  function researchPage() {
    return `<div class="page prose-page">${pageHead('Research','Evidence before possibility.','What is built, what the experiments found, and what is still unknown. Engineering results and human value are separate questions.')}<article class="evidence-card"><p class="eyebrow">Implemented · Local prototype</p><h2>Two worlds. One replayable history contract.</h2><p>Pompeii and Shared Observatory use a common lifecycle around existing world rules. Choices are validated, saved and replayed. Private knowledge, accepted receipts and exact simulated time remain distinct.</p><div class="evidence-meta">Scope: two finite adapters with authored rules · No universal world generation</div><a class="text-link" href="/your-worlds">Inspect an available saved life <span aria-hidden="true">↗</span></a></article><article class="evidence-card"><p class="eyebrow">Exploratory study · Previous phase</p><h2>V3 and V2 tied in 432 matched pairs.</h2><p>The earlier cognition study ran 972 one-day worlds. Every matched V3–V2 pair tied on executed outcomes and ledgers. Some retention policies reduced missed promises and inspection costs in authored tasks; the added plan state did not improve these outcomes.</p><div class="evidence-meta">Independent comparison unit: paired world seed within nine authored families<br>Budget: matched record limits, unequal serialized state · No held-out or human efficacy claim</div><a class="text-link" href="/research/artifacts/cognition">Read the study artifact <span aria-hidden="true">↗</span></a></article><article class="evidence-card"><p class="eyebrow">Exploratory study · Previous phase</p><h2>Persistence across 90 and 120 days.</h2><p>Recorded Observatory and Pompeii lives restart at declared checkpoints. Omission replay executes a history without one accepted choice while preserving the original. Persistence over months does not establish cognitive improvement over months.</p><div class="evidence-meta">Samples: one authored life per domain · No measured human learning, enjoyment or retention</div><a class="text-link" href="/research/artifacts/lives">Read the saved-life evidence <span aria-hidden="true">↗</span></a></article><article class="evidence-card"><p class="eyebrow">Next-phase diagnostic</p><h2>What evidence changes a later decision?</h2><p>The next study first checks whether delayed obligations actually depend on retained evidence. It compares memory under declared budgets, with corrections, interruptions and negative controls. A tie or regression remains a result.</p><div id="next-research-summary"><p class="fine-print">The current report and reproduction details are available through the local research artifact route when generated. No new superiority result is implied by this page.</p></div><a class="text-link" href="/research/artifacts/next-phase">Open the current research report <span aria-hidden="true">↗</span></a></article><article class="evidence-card"><p class="eyebrow">Boundaries</p><h2>What we have not measured.</h2><p>No consenting participant study, customer demand, paid-model quality or subjective-time benefit follows from a passing test suite. Offline authored language remains the default. Human-use guides prepare observation; they are not human results.</p><p><a href="/studio">Experimental authoring</a> supports the existing finite domains. Research Lab deliberately reveals private simulator information and marks the life as operator-exposed.</p></article></div>`;
  }
  async function loadResearchSummary(epoch) {
    const result=await api('research');if(epoch!==S.routeEpoch||!$('#next-research-summary'))return;
    const comparison=result.comparison,cases=[['review_current_correction','A current correction'],['review_hidden_reversal','A hidden reversal'],['review_improvement_overload','Improvement with overload'],['review_unchanged_interruption','An unchanged obligation after interruption']],groups=comparison?.groups||[],arms=['v3_hybrid','dependency_retention','bm25_fifo'];
    const group=(caseId,arm)=>groups.find(g=>g.case===caseId&&g.arm===arm);
    const results=comparison?`<p><strong>${Number(comparison.worlds)} offline world runs</strong> across development and frozen internal review cases. The candidate completed more chains in one review case, tied in two and shared an information limit in the fourth.</p><div class="research-table-wrap"><table class="research-table"><caption>Completed obligation chains in internal review cases</caption><thead><tr><th scope="col">Case</th><th scope="col">Shipped V3</th><th scope="col">Candidate</th><th scope="col">FIFO + BM25</th></tr></thead><tbody>${cases.map(([id,label])=>`<tr><th scope="row">${label}</th>${arms.map(arm=>{const g=group(id,arm);return `<td>${g?`${Number(g.completed_chains)} / ${Number(g.worlds)}`:'Unreported'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div><p class="fine-print">${esc(comparison.scope||comparison.interpretation||'Internal authored variants of one scaffold; no general intelligence or human result.')} The report includes total retained-state bytes, costs, source fingerprints and failures. A zero-width conditional interval does not establish general certainty.</p>`:`<p class="fine-print">${result.next_phase_report_available?'A current next-phase report has been generated. Open it for the frozen design, actual results and reproduction details.':'The next-phase report is not available in this installation yet. No new result is claimed.'}</p>`;
    $('#next-research-summary').innerHTML=results+`<p class="fine-print">Live-model calls recorded by this server: ${Number(result.live_model_calls||0)}. This is an execution count, not an expression-quality evaluation.</p>`;
  }
  function prosePage(path) {
    const pages={
      '/about':['The idea','Worlds worth spending time in.',`<p>Kalends explores curated persistent worlds: places you can inhabit, people with their own circumstances, and choices that leave a history.</p><p>The long-term ambition spans different settings, learning through experience and replaceable interfaces. Today’s working expression is smaller: a Roman-inspired neighborhood and a shared-instrument decision experience.</p><h2>Ordinary life belongs here.</h2><p>A recognizable routine, an unhurried exchange and returning to a person matter alongside consequential decisions. The world need not turn every moment into a reward, crisis or score.</p><h2>What persistence means today.</h2><p>Accepted actions are kept in a local journal. People and institutions act through authored rules and bounded memories. Time advances during play or when you explicitly choose it. This is a local early prototype, with no claim of sentience, unrestricted generation or validated training.</p><p><a href="/worlds">Explore the two worlds</a> or <a href="/research">read the evidence and limits</a>.</p>`],
      '/accessibility':['Accessibility','A readable way into the world.',`<p>The web shell uses semantic controls, visible focus, keyboard navigation, labelled dialogs and reduced-motion support. The Observatory decision experience presents consequential choices as text.</p><p>Pompeii retains its existing 3D client and settings. A participant history presents recorded consequences and evidence in text. A full assistive-technology audit has not been completed; this page does not claim WCAG certification.</p><h2>Keyboard controls</h2><p>Use Tab and Shift+Tab to move between controls, Enter or Space to activate buttons, and Escape to close dialogs or the story drawer. The 3D client lists its own movement and interaction controls.</p><h2>Reading and motion</h2><p>Your browser’s text zoom is supported. The shell respects the system reduced-motion preference. The world keeps its own accessibility settings, preserved when opening and closing your story.</p>`],
      '/data-and-saves':['Data & saves','Your history stays on this installation.',`<p>World journals are saved by the local Kalends server. “Local” means this installation’s filesystem, rather than a cloud account or synchronized browser profile. This release has no account system.</p><h2>Separate lives, explicit identity.</h2><p>Beginning a new life creates a new journal. It does not reset another life. Incompatible journals are preserved and reported rather than silently replaced. Only one server writer may open a save directory.</p><h2>Paused time.</h2><p>The world does not simulate while its local server is stopped. Returning after a real-world interval resumes the recorded moment. Advancing simulated time is an explicit choice.</p><h2>Optional local usage events.</h2><p>You may opt in through the world menu. Events record limited actions such as entering a life, opening history and accepted choices, with build, life and anonymous session identifiers. Raw conversation text is not collected by these events. The world’s accepted action journal is separate.</p><h2>Research exposure.</h2><p>Research Lab reveals information your participant may not know. Opening it requires an explicit acknowledgement and marks that life as operator-exposed for future analysis. Viewing research does not install hidden facts into NPC memories.</p><p>No automatic upload, recruitment or external model use is enabled by these pages.</p>`],
      '/acknowledgements':['Sources & assets','An authored world, honestly labelled.',`<p>Pompeii is historical fiction in a small Roman-inspired neighborhood. It is not a surveyed reconstruction or a complete ancient city. Microhistories, situations and character speech are authored or reconstructed.</p><p>The public Pompeii image is an actual capture from this repository’s existing prototype. It shows the earlier interface; the playable scene may use a newer shell. Shared Observatory’s orbital illustration is a labelled conceptual diagram.</p><p>Shared Observatory is a project-authored instrument-allocation scenario, not an operational observatory or accredited curriculum. Its representative names are fictional display metadata over fixed internal team identities.</p><h2>Existing project asset register</h2><p>The retained renderer and its source assets remain in the Kalends repository. <a href="/research/artifacts/assets">Open the local asset and source register</a> for provenance and usage details.</p>`]
    };
    const p=pages[path];return p?`<div class="page prose-page">${pageHead(p[0],p[1])}${p[2]}</div>`:errorPage('Page unavailable','That page is not available in this local prototype.','/','Return to Kalends');
  }
  function errorPage(title, message, href='/', label='Return to Kalends') { return `<div class="page"><div class="error-panel"><p class="eyebrow">Your saved history is preserved</p><h2>${esc(title)}</h2><p>${esc(message)}</p><a class="button secondary" href="${esc(href)}">${esc(label)}</a></div></div>`; }
  async function loadCatalog() { const result=await api('catalog'); S.catalog=result; return result; }
  function navigate(path, replace=false) { if(location.pathname+location.search+location.hash===path) { route().catch(notifyError); return; } history[replace?'replaceState':'pushState']({},'',path); route().catch(notifyError); }
  function routeParts() { const path=decodeURIComponent(location.pathname).replace(/\/$/,'') || '/'; const match=path.match(/^\/lives\/([^/]+)(?:\/(history|reflect))?$/); return {path,life:match&&{id:match[1],view:match[2]||null}}; }
  async function route() {
    const epoch=++S.routeEpoch, r=routeParts(); S.lab=null;
    for(const d of $$('dialog[open]')) d.close();
    if(!S.catalog) await loadCatalog(); if(epoch!==S.routeEpoch) return;
    if(r.life) {
      $('#main').replaceChildren();
      $('#public-shell').hidden=true; $('#life-shell').hidden=false; document.body.classList.add('in-world');
      await enterLife(r.life.id, epoch);
      if(epoch!==S.routeEpoch)return;
      if(r.life.view) await openStory(r.life.view==='reflect'?'reflect':'history'); else closeStory(false);
      document.title=`${metadata(S.data).title||'Your world'} · Kalends`; return;
    }
    pauseFrames(); S.gate.select(null); S.id=null; S.data=null; S.proposal=null; S.reflection=null; closeStory(false);
    $('#life-shell').hidden=true;$('#public-shell').hidden=false;document.body.classList.remove('in-world');
    for(const a of $$('.site-header nav a')) a.setAttribute('aria-current',r.path.startsWith(a.pathname)?'page':'false');
    if(r.path==='/') $('#main').innerHTML=homePage();
    else if(r.path==='/worlds') $('#main').innerHTML=worldsPage();
    else if(r.path.startsWith('/worlds/')) $('#main').innerHTML=detailPage(r.path.slice(8));
    else if(r.path==='/your-worlds') {await loadCatalog();if(epoch!==S.routeEpoch)return;$('#main').innerHTML=savesPage();}
    else if(r.path==='/research') {$('#main').innerHTML=researchPage();loadResearchSummary(epoch).catch(notifyError);}
    else if(r.path.startsWith('/lab/')) await renderLab(r.path.slice(5),epoch);
    else if(r.path==='/studio') await renderStudio(epoch);
    else $('#main').innerHTML=prosePage(r.path);
    document.title=r.path==='/'?'Kalends · Enter a world. Leave a history.':`${({'/worlds':'Worlds','/your-worlds':'Your worlds','/research':'Research','/about':'About','/studio':'Experimental Studio','/data-and-saves':'Data & saves','/accessibility':'Accessibility','/acknowledgements':'Sources & assets'})[r.path]||'Kalends'} · Kalends`;
    if(location.hash) requestAnimationFrame(()=>document.getElementById(location.hash.slice(1))?.scrollIntoView());else scrollTo(0,0);
  }
  async function enterLife(id, routeEpoch) {
    const changed=S.id!==id; if(changed){saveCommonDraft();pauseFrames();S.id=id;S.gate.select(id);S.data=null;S.reflection=null;S.proposal=null;S.conversationEpoch++;$('#life-loading').hidden=false;}
    try {
      const readVersion=(S.readVersions.get(id)||0)+1;S.readVersions.set(id,readVersion);
      const data=await S.gate.run(signal=>api('life?id='+encodeURIComponent(id),undefined,signal));
      if(routeEpoch!==S.routeEpoch)return;
      if(readVersion!==S.readVersions.get(id)||!S.revisions.admit(id,data))return;
      S.data=data;S.uncertain.delete(id);renderLife();
      if(changed) { await api('resume',{id}); if(id!==S.id)return; showReturn(); telemetry('life_entered'); }
    } catch(error) {
      if(error instanceof StaleRequest||error.name==='AbortError')return;
      $('#life-loading').hidden=true;
      if(!S.data){$('#public-shell').hidden=false;$('#life-shell').hidden=true;document.body.classList.remove('in-world');$('#main').innerHTML=errorPage('We could not open this life.',error.message,'/your-worlds','Back to your worlds');}
      else notifyError(error);
    }
  }
  function renderLife() {
    const d=S.data,s=d.snapshot||{},l=metadata(d),roman=s.setting==='pompeii'||isPompeii(l);
    $('#world-title').textContent=roman?'Pompeii':'Shared Observatory';
    $('#world-participant').textContent=(l.participant||(roman?'Aelia':'Consortium coordinator'))+' · '+String(l.id||S.id).slice(-8);
    $('#world-date').textContent=(roman&&s.world?.clock?`Day ${s.world.day} · ${s.world.clock}`:timeLabel(l.minute??s.minute))+' · World time';$('#world-saving').textContent=S.pending.has(S.id)?'Saving…':saveStatus(l.save_status);
    $('#scene-frames').hidden=!roman;$('#observatory-stage').hidden=roman;$('#life-loading').hidden=true;
    $('#menu-lab').href='/lab/'+encodeURIComponent(S.id);$('#telemetry-opt-in').checked=!!d.telemetry?.opt_in;
    if(roman) ensureFrame(S.id);else renderObservatory();
    if(!$('#story-drawer').hidden) renderStory();
  }
  function ensureFrame(id) {
    let item=S.frames.get(id),wasHidden=!!item?.wrapper.hidden;
    if(!item){const wrapper=document.createElement('div');wrapper.className='scene-frame-wrap';wrapper.dataset.life=id;const frame=document.createElement('iframe');frame.className='scene-frame';frame.title='Pompeii · your saved life';frame.src='/immersion/?experience='+encodeURIComponent(id);wrapper.append(frame);const loading=document.createElement('div');loading.className='scene-frame-loading';loading.textContent='Entering the neighborhood…';wrapper.append(loading);$('#scene-frames').append(wrapper);let persisted=null;try{persisted=JSON.parse(sessionStorage.getItem('kalends:scene:'+id)||'null');}catch(_){}item={wrapper,frame,loading,ready:false,initialView:persisted,requests:new Map(),retryCount:0};S.frames.set(id,item);}
    for(const [key,value] of S.frames){value.wrapper.hidden=key!==id;if(key!==id)host(key,'pause');}
    if(item.ready&&wasHidden&&$('#story-drawer').hidden) host(id,'refresh');
  }
  function host(id, action, view) { const item=S.frames.get(id);if(!item)return;const request_id=String(++S.lastSceneRequest);item.requests.set(request_id,{action,view});if(item.requests.size>20)item.requests.delete(item.requests.keys().next().value);item.frame.contentWindow?.postMessage({kind:'kalends:host',life_id:id,request_id,action,...(view?{view}:{})},location.origin); }
  function pauseFrames() { for(const [id,item] of S.frames){host(id,'pause');item.wrapper.hidden=true;} }
  function draft(id) { if(!S.drafts.has(id))S.drafts.set(id,{});return S.drafts.get(id); }
  function saveCommonDraft() { const stage=$('#observatory-stage');if(!S.id||stage.dataset.life!==S.id)return;const state=draft(S.id);for(const input of $$('#observatory-stage input[name],#observatory-stage select[name]'))state[input.name==='speech'?'speech:'+stage.dataset.recipient:input.name]=input.value; }
  function commonPeople() { const source=S.data?.people||S.data?.history?.people||[];return ['team_a','team_b','team_c'].map((id,i)=>({...source.find(p=>p.id===id),id,name:source.find(p=>p.id===id)?.name||['Amir','Mira','Lin'][i],role:source.find(p=>p.id===id)?.role||['Survey team','Instrument systems','Follow-up team'][i]})); }
  function renderObservatory() {
    const active=document.activeElement,focus=active?.closest('#observatory-stage')?{name:active.name,start:active.selectionStart,end:active.selectionEnd,person:active.dataset.person}:null;
    saveCommonDraft();const d=S.data,s=d.snapshot||{},people=commonPeople(),selected=S.selected.get(S.id)||'team_b',p=people.find(a=>a.id===selected)||people[1],inputs=draft(S.id),requests=s.requests||{},allocation=s.allocation||{},promises=s.promises||{},history=d.history||{},ended=s.terminated||metadata(d).example,roundClosed=!!s.round_closed,allocationRecorded=s.allocation!==null&&s.allocation!==undefined;
    const report=(s.own_reports||[]).at(-1),condition=report?.payload?.value;
    const reportLine=condition?`The report you received described the condition as “${condition}”, dated ${timeLabel(report.payload.as_of??report.tick)}. This is dated evidence, not a fresh check.`:'Actual current condition is unconfirmed in your received reports. Nominal capacity is 12; ask for dated evidence before promising it.';
    let reply=text(p.reply)||text(p.greeting);if(reply==='We can discuss the work, a dated report, or the current allocation.')reply='';
    if(!reply)reply=selected==='team_b'?'I work on the instrument systems. You can ask me for the report I retained before you decide what to promise.':selected==='team_a'?'Our survey work has a deadline. Please distinguish what you promise us from what the instrument actually delivers.':'Our follow-up work also depends on time at the instrument. I need to know what we can actually count on.';
    const recent=(history.beats||[]).filter(b=>b.kind!=='routine').slice(-3).reverse();
    $('#observatory-stage').innerHTML=`<div class="observatory">
      <div class="obs-heading"><div><p class="eyebrow">Shared Observatory · You are the coordinator</p><h1>Three teams. One instrument.</h1><p>Each team has work to complete. Ask what they know, make a supported promise, and decide how to share the next round. Delivery follows the public order: Amir → Mira → Lin.</p></div><span class="obs-round">${ended?'Recorded horizon reached':`Current round · ${timeLabel(s.minute)}`}</span></div>
      <div class="obs-layout"><div>
        <section class="instrument-stage"><p class="eyebrow">The shared instrument</p><h2>Twelve nominal slots.<br>Three legitimate needs.</h2><p class="instrument-caption">${esc(reportLine)}</p><p class="instrument-caption">Under the declared rule, a fragile condition supports 8 usable slots; a stable (sound) condition supports 12. A dated report may be out of date.</p><div class="capacity-track" aria-hidden="true">${Array.from({length:12},(_,i)=>`<span class="capacity-unit${i<Object.values(allocation).reduce((a,b)=>a+Number(b),0)?' allocated':''}"></span>`).join('')}</div><div class="capacity-key">Nominal slots · Requested: ${people.map(person=>`${esc(person.name)} ${Number(requests[person.id]||0)}`).join(' / ')}<br>Allocated amounts are requests for execution. Usable capacity and actual delivery may differ.</div></section>
        <div class="people-list" aria-label="People you can speak with">${people.map(person=>`<button class="person-button${selected===person.id?' selected':''}" data-person="${person.id}" aria-pressed="${selected===person.id}"><span class="person-avatar" aria-hidden="true">${esc(person.name[0])}</span><strong>${esc(person.name)}</strong><small>${esc(person.role)}</small></button>`).join('')}</div>
        <section class="conversation" aria-label="Conversation with ${esc(p.name)}"><span class="speaker-role">${esc(p.role)}</span><h2>${esc(p.name)}</h2><p class="conversation-line">“${esc(reply)}”</p>
          ${p.outcome?`<p class="fine-print">Recorded settlement: ${esc(text(p.outcome))} ${supportLink(p.outcome.evidence_ids)}</p>`:''}
          ${!ended?`<div class="suggestions">${selected==='team_b'?'<button data-action="report" data-life-write>Ask for your dated report</button>':''}<button data-action="promise" data-recipient="${esc(selected)}" ${roundClosed?'disabled':''}>Discuss a promise</button><button data-action="inspect" data-life-write>Buy a direct inspection · 1 credit</button></div><form class="speech-form" id="common-speech"><input name="speech" id="common-speech-input" aria-label="What would you like to say to ${esc(p.name)}?" maxlength="600" value="${esc(inputs['speech:'+selected]||'')}" placeholder="Ask about a report, promise, or allocation…"><button class="button" data-life-write>Say <span aria-hidden="true">→</span></button></form><p class="speech-help">Offline supported language. Unsupported requests receive a clarification; speaking alone does not commit a choice.</p>`:'<p class="fine-print">This recorded life is available for history and reflection. Begin a new life to make new choices.</p>'}
        </section>
        <section class="obs-timeline"><h2>A few recent moments</h2><div class="quiet-events">${recent.length?recent.map(b=>`<article class="quiet-event"><small>${esc(timeLabel(b.at))}</small><p>${esc(text(b))}</p>${supportLink(b.evidence_ids)}</article>`).join(''):'<p class="story-empty">Your first accepted choice will begin this part of your history. Opening a conversation does not change the world.</p>'}</div></section>
      </div><aside class="obs-sidebar">
        <section class="obs-panel"><p class="eyebrow">Requested → Promised → Allocated → Delivered</p><h2>Choose an allocation.</h2><p>The teams’ current requests are shown below. A promise creates an obligation; an allocation is a separate choice. Actual delivery is recorded at settlement.</p>
          <form id="allocation-form" class="allocation-form">${people.map(person=>`<div class="allocation-row"><label for="allocate-${person.id}">${esc(person.name)}<small>${Number(requests[person.id]||0)} requested · ${Number(promises[person.id]||0)} promised · ${Number(allocation[person.id]||0)} allocated</small></label><input id="allocate-${person.id}" name="${person.id}" type="number" min="0" max="12" step="1" required value="${esc(inputs[person.id]??allocation[person.id]??4)}" ${ended||roundClosed||allocationRecorded?'disabled':''}></div>`).join('')}<button class="button" data-life-write data-allocation-review ${ended||roundClosed||allocationRecorded?'disabled':''}>${roundClosed?'Round settled':allocationRecorded?'Allocation already recorded':'Review allocation'} <span aria-hidden="true">→</span></button></form>${roundClosed?'<p class="fine-print">This round has settled. Advance to the next day for new choices.</p>':allocationRecorded?'<p class="fine-print">This allocation is already saved. It cannot be replaced within this round.</p>':''}
          <p class="own-credits">You have <strong>${Number(s.credits??s.metrics?.credits??0)} credits</strong>. A direct inspection costs 1.</p>
        </section>
        <section class="obs-panel"><h2>What you have promised</h2>${(d.known_commitments||history.known_commitments||[]).length?`<ul class="commitment-list">${(d.known_commitments||history.known_commitments).map(c=>`<li>${esc(text(c))} ${supportLink(c.evidence_ids)}</li>`).join('')}</ul>`:'<p>No open promise is recorded for this round.</p>'}</section>
        <button class="obs-time-button" data-open-time ${ended?'disabled':''}><span><strong>Let the day continue.</strong><small>Choose how far to advance. Known deadlines remain visible.</small></span><span aria-hidden="true">→</span></button><a class="text-link" href="${lifeURL(S.id,'/history')}">Read your complete story <span aria-hidden="true">↗</span></a>
      </aside></div></div>`;
    $('#observatory-stage').dataset.life=S.id;
    $('#observatory-stage').dataset.recipient=selected;
    setPendingControls();
    if(focus){const target=focus.name?$('#observatory-stage').querySelector('[name="'+focus.name+'"]'):focus.person?$('#observatory-stage').querySelector('[data-person="'+focus.person+'"]'):null;if(target&&!target.disabled){target.focus({preventScroll:true});if(target.type==='text'&&Number.isInteger(focus.start))target.setSelectionRange(focus.start,focus.end);}}
  }
  function supportLink(ids) { return ids?.length?`<button class="text-link" data-evidence="${Number(ids[0])}" style="background:transparent">Inspect dated support <span aria-hidden="true">↗</span></button>`:''; }
  function setPendingControls() { for(const b of $$('[data-life-write]'))b.disabled=S.pending.has(S.id)||S.uncertain.has(S.id)||!!S.data?.snapshot?.terminated||!!metadata(S.data).example||(b.hasAttribute('data-allocation-review')&&(S.data?.snapshot?.round_closed||S.data?.snapshot?.allocation!==null&&S.data?.snapshot?.allocation!==undefined));$('#confirm-choice').disabled=S.pending.has(S.id)||S.uncertain.has(S.id); }
  async function refreshLife() { const id=S.id;if(!id)return;const readVersion=(S.readVersions.get(id)||0)+1;S.readVersions.set(id,readVersion);const data=await S.gate.run(signal=>api('life?id='+encodeURIComponent(id),undefined,signal));if(id!==S.id||readVersion!==S.readVersions.get(id)||!S.revisions.admit(id,data))return;S.data=data;S.uncertain.delete(id);renderLife();return data; }
  async function mutate(path, body, onSuccess) {
    const id=S.id;if(!id||S.pending.has(id))return;if(S.uncertain.has(id)){status('Refresh this life to reconcile its last request before making another choice.');return;}
    S.pending.add(id);setPendingControls();$('#world-saving').textContent='Saving…';
    try { const result=await api(path,{id,...body}); if(id!==S.id)return result;if(result.life&&S.revisions.admit(id,result))S.data=result; if(onSuccess)await onSuccess(result); await refreshLife(); $('#world-saving').textContent='Saved locally';return result; }
    catch(error){if(!(error instanceof ApiError)||error.code==='unreadable_response'){S.uncertain.add(id);if(id===S.id){showNotice('The save status needs checking.','The response was interrupted. The server may have accepted the choice. Refresh this life before trying again.',true);}}else if(id===S.id){$('#world-saving').textContent='Choice not accepted';}throw error;}
    finally {S.pending.delete(id);if(id===S.id)setPendingControls();}
  }
  async function propose(action) {
    const id=S.id,epoch=S.gate.epoch,conversationEpoch=S.conversationEpoch,proposalEpoch=++S.proposalEpoch;if(!id||S.pending.has(id)||S.uncertain.has(id))return;
    const proposal=await S.gate.run(signal=>api('propose',{id,action},signal));if(id!==S.id||epoch!==S.gate.epoch||conversationEpoch!==S.conversationEpoch||proposalEpoch!==S.proposalEpoch)return;
    S.proposal={id,...proposal};$('#review-heading').textContent=describeAction(proposal.action||action);$('#review-error').textContent='';
    const a=proposal.action||action, people=commonPeople();
    let terms=a.action==='allocate'?`<div class="review-amounts">${people.map(p=>`<span>${esc(p.name)} · ${esc(p.role)}</span><strong>${Number(a.allocation?.[p.id]||0)} units</strong>`).join('')}</div><p class="fine-print" style="margin-top:16px">These are allocated amounts. The instrument executes the actual available capacity in the disclosed order Amir → Mira → Lin.</p>`:a.action==='commit'?`<p>Promise <strong>${Number(a.quantity)} units</strong> to <strong>${esc(personName(a.recipient))}</strong>.</p><small>This becomes an obligation. Allocating capacity and actually delivering it remain separate steps.</small>`:a.action==='inspect'?'<p>Spend <strong>1 of your credits</strong> on a direct dated inspection.</p><small>The result is disclosed only after this interaction is accepted and saved.</small>':`<p>Request a legitimate disclosure of ${esc(personName(a.recipient))}’s retained report.</p><small>The contents become available to you after acceptance. A retained report is dated testimony; it does not guarantee the instrument’s present condition.</small>`;
    const due=(S.data?.time?.known_stops||[]).find(stop=>stop.kind==='public_round_deadline');
    $('#review-content').innerHTML=`<div class="review-terms">${terms}${due&&['commit','allocate'].includes(a.action)?`<p style="margin-top:16px"><strong>Settlement: ${esc(timeLabel(due.at))}</strong><small>The public round deadline is world minute ${Number(due.at)}. A promise and an allocation are recorded separately.</small></p>`:''}</div><p>No change has been accepted yet. Confirmation rechecks this exact proposal against your saved world. If time or terms changed, review again.</p>`;
    $('#confirm-choice').hidden=false;$('#confirm-choice').textContent='Confirm this choice →';setPendingControls();$('#review-dialog').showModal();
  }
  async function confirmChoice() {
    const proposal=S.proposal;if(!proposal||proposal.id!==S.id)return;
    $('#review-error').textContent='';$('#confirm-choice').textContent='Committing and saving…';
    try {await mutate('confirm',{proposal_id:proposal.proposal_id},()=>{if(proposal.id===S.id){S.proposal=null;$('#review-dialog').close();status('Accepted, recorded and saved.');telemetry('meaningful_action');}});}
    catch(error){if(proposal.id===S.id){$('#review-error').textContent=error.message;$('#confirm-choice').textContent='Review this choice again';S.proposal=null;$('#confirm-choice').disabled=true;}notifyError(error);}
  }
  function showNotice(title,body,reconcile=false) { const n=$('#world-notice');n.innerHTML=`<strong>${esc(title)}</strong>${esc(body)}<br>${reconcile?'<button class="text-link" data-reconcile style="background:transparent">Refresh this life →</button>':''}<button class="text-link" data-dismiss-return style="background:transparent">Continue from here →</button>`;n.hidden=false; }
  function showReturn() {
    if(!S.data||S.returnSeen.has(S.id))return;const d=S.data,r=d.return_summary||d.history?.return_summary||{},changes=r.changes||r.clauses||[],l=metadata(d);
    const summary=returnText(r)||r.text||`Paused ${l.location?'at '+l.location:'at your recorded moment'}. Time advances when you choose.`;
    showNotice('Your place is still here.',summary);S.returnSeen.add(S.id);
  }
  function returnText(summary) {const elsewhere=(summary.independent_developments||[]).at(-1),independent=new Set((summary.independent_developments||[]).flatMap(b=>b.evidence_ids||[])),changes=(summary.changes||summary.clauses||[]).filter(b=>!(b.evidence_ids||[]).some(id=>independent.has(id))),unresolved=summary.unresolved?.[0];return [changes.slice(-2).map(text).join(' '),unresolved?'Still open: '+text(unresolved):'',elsewhere?'Elsewhere in this world: '+text(elsewhere):''].filter(Boolean).join(' ');}
  async function dismissReturn() { $('#world-notice').hidden=true;if(!S.id||!S.data)return;try{await api('seen',{id:S.id,revision:metadata(S.data).revision??S.data.history?.revision??S.data.snapshot?.command_count??0});}catch(error){notifyError(error);} }
  async function openStory(tab) {
    if(!S.data)return;S.storyTab=tab;$('#story-backdrop').hidden=false;$('#story-drawer').hidden=false;$('#world-main').inert=true;$('.world-header').inert=true;host(S.id,'pause');renderStory();$('#close-story').focus();telemetry('history_opened');if(tab==='reflect')await loadReflection();
  }
  function closeStory(updateRoute=true) {
    const wasOpen=!$('#story-drawer').hidden;$('#story-backdrop').hidden=true;$('#story-drawer').hidden=true;$('#world-main').inert=false;$('.world-header').inert=false;
    if(wasOpen&&S.id){host(S.id,'refresh');$('#story-button').focus();}
    if(updateRoute&&S.id)navigate(lifeURL(S.id));
  }
  function beatHTML(beat,options) { const body=beat.body||beat.text||'',title=beat.title||'Recorded moment';return `<article class="story-beat">${options?.heading===false?'':`<h4>${esc(title)}</h4>`}${body&&body!==title?`<p>${esc(body)}</p>`:''}${(beat.uncertainties||[]).map(u=>`<p class="fine-print">${esc(u)}</p>`).join('')}${supportLink(beat.evidence_ids)} ${beat.evidence_ids?.length&&!metadata(S.data).example?`<button class="text-link" data-bookmark="${Number(beat.evidence_ids[0])}" style="background:transparent;margin-left:12px">Bookmark</button>`:''}</article>`; }
  function renderStory() {
    if(!S.data)return;for(const b of $$('.story-tabs button'))b.setAttribute('aria-current',b.dataset.storyTab===S.storyTab?'page':'false');
    const h=S.data.history||{},container=$('#story-content');
    if(S.storyTab==='people'){container.innerHTML=`<p class="story-empty">These are your recorded encounters. A past event does not prove what someone currently remembers.</p>${(S.data.people||h.people||[]).map(p=>`<section class="story-person"><h3>${esc(p.name||p.id)}</h3><p>${esc(p.role||'')}</p>${p.outcome?`<p>${esc(text(p.outcome))} ${supportLink(p.outcome.evidence_ids)}</p>`:''}${(p.episodes||[]).length?(p.episodes||[]).slice(-3).map(beatHTML).join(''):'<p>No admitted encounter has been recorded yet.</p>'}</section>`).join('')}`;return;}
    if(S.storyTab==='reflect'){renderReflection();return;}
    const chapters=h.chapters||[],chapterLimit=S.chapterLimits.get(S.id)||8;
    const elsewhere=(S.data.return_summary?.independent_developments||h.return_summary?.independent_developments||[]).at(-1);
    container.innerHTML=`<p class="story-empty">A history from what your participant did, saw or legitimately learned. Related records support a claim; they do not by themselves prove its necessary cause.</p>${elsewhere?`<section class="chapter"><h3>Elsewhere in this world</h3>${beatHTML(elsewhere)}</section>`:''}${(h.unresolved||[]).length?`<section class="chapter"><h3>Still open</h3>${h.unresolved.map(c=>`<p>${esc(text(c))} ${supportLink(c.evidence_ids)}</p>`).join('')}</section>`:''}${chapters.length?chapters.slice(-chapterLimit).reverse().map(c=>`<section class="chapter"><small>${esc(timeLabel(c.at))} · ${esc(String(c.kind||'chapter').replaceAll('_',' '))}</small><h3>${esc(c.title||'A chapter in your history')}</h3>${(c.beats||[]).map(b=>beatHTML(b,{heading:b.title!==c.title})).join('')}${(c.routines||[]).map(r=>`<details><summary class="fine-print">${esc(r.title||'Everyday activity')} · ${Number(r.count||(r.beats||[]).length)} records</summary>${(r.beats||[]).map(beatHTML).join('')}</details>`).join('')}</section>`).join(''):'<p class="story-empty">Your life has just begun. Look around, meet someone, and make a supported choice when you are ready.</p>'}${chapters.length>chapterLimit?'<button class="button secondary" data-earlier-chapters>Read earlier chapters →</button>':''}${notesHTML()}`;
  }
  function notesHTML() {
    const notes=S.data?.notes||[],bookmarks=S.data?.bookmarks||[];
    return `<section class="chapter"><h3>Your personal notes</h3><p>These are your interpretations. They are kept separate from recorded history and are never installed into another person’s memory.</p>${notes.map(n=>`<article class="story-beat"><small>${esc(timeLabel(n.minute))} · Personal note</small><p>${esc(n.text)}</p></article>`).join('')}${bookmarks.length?`<details><summary class="fine-print">Your ${bookmarks.length} bookmarked moments</summary><div class="suggestions">${bookmarks.map(id=>`<button data-evidence="${Number(id)}">Record ${Number(id)}</button>`).join('')}</div></details>`:''}${!metadata(S.data).example?`<form id="history-notes" class="note-form"><label for="personal-note">Add a personal note</label><textarea id="personal-note" name="note" maxlength="1200" rows="3" required>${esc(draft(S.id).note||'')}</textarea><button class="button secondary">Save personal note</button></form>`:''}</section>`;
  }
  async function loadReflection() {
    const id=S.id;$('#story-content').innerHTML='<p class="story-empty" role="status">Restoring the evidence available at each choice…</p>';
    try{const r=await S.gate.run(signal=>api('reflect?id='+encodeURIComponent(id),undefined,signal));if(id!==S.id)return;S.reflection=r;if(S.storyTab==='reflect')renderReflection();}catch(error){if(id===S.id)$('#story-content').innerHTML=`<p class="story-empty">${esc(error.message)}</p>`;notifyError(error);}
  }
  function reflectionChoices() { const r=S.reflection||{};return r.choices||r.then_choices||r.history?.choices||[]; }
  function renderReflection() {
    const r=S.reflection;if(!r){$('#story-content').innerHTML='<p class="story-empty">Choose a recorded action to restore what you knew then.</p>';return;}
    const choices=reflectionChoices();
    $('#story-content').innerHTML=`<section class="reflect-block"><h3>What you chose. What followed.</h3><p>Revisit an exact accepted action and the evidence available before it. Later corrections are not inserted into your earlier knowledge.</p></section>${choices.length?`<section class="reflect-block"><h3>A choice to revisit</h3><select id="reflect-choice" aria-label="Accepted action to revisit">${choices.map(c=>`<option value="${c.index}">${esc(timeLabel(c.at))} · ${esc(describeAction(c.action||c.data))}</option>`).join('')}</select><div id="then-evidence"></div><h3>Try this history without that choice.</h3><p>This executes one omission. Later declared choices stay the same where they remain feasible. It is not an optimal alternative, and it never replaces your original life.</p><button class="button secondary" id="execute-alternative">Execute this alternative <span aria-hidden="true">→</span></button><div id="alternative-result"></div></section>`:'<p class="story-empty">No accepted participant action is available to omit yet. Look around and make a supported choice when you are ready.</p>'}<section class="reflect-block"><h3>What remains uncertain</h3><p>Testimony may be dated. Events outside your participant’s knowledge remain outside this view. Executed differences are specific to the declared alternative and continuation.</p></section>`;
    renderThenEvidence();
  }
  function renderThenEvidence() {
    const node=$('#then-evidence');if(!node)return;const index=Number($('#reflect-choice').value),choice=reflectionChoices().find(c=>c.index===index);if(!choice)return;
    const evidence=choice.then_evidence||choice.evidence||[];
    node.innerHTML=`<div class="then-evidence"><h4>What you knew then</h4>${evidence.length?evidence.slice(-8).map(e=>`<div class="evidence-item"><p><strong>${esc(timeLabel(e.at??e.tick))}</strong> · ${esc(e.title||text(e))}</p>${e.value!==undefined?evidenceValueHTML(e.value):''}</div>`).join(''):'<p>No earlier admitted evidence was attached to this choice.</p>'}<p>This is the admitted prefix before the choice. It is separate from another person’s current retained memory.</p></div>`;
  }
  function evidenceValueHTML(raw) {let value=raw;if(typeof raw==='string'){try{value=JSON.parse(raw);}catch(_){}}if(value&&typeof value==='object'){const rows=Object.entries(value);return `<details><summary class="fine-print">Supported register · ${rows.length} entries</summary><ul>${rows.slice(0,12).map(([key,v])=>`<li>${esc(human(key).replaceAll('_',' '))}: ${esc(v&&typeof v==='object'?Array.isArray(v)?`${v.length} recorded items`:'recorded constraints':v)}</li>`).join('')}</ul></details>`;}return `<p>Recorded value: ${esc(value)}</p>`;}
  async function executeAlternative() {
    const id=S.id,index=Number($('#reflect-choice')?.value),button=$('#execute-alternative');if(!Number.isInteger(index))return;button.disabled=true;button.textContent='Executing a separate history…';
    try{const result=await S.gate.run(signal=>api('fork',{id,command_index:index},signal));if(id!==S.id)return;const differences=result.differences||{},skipped=result.skipped||[];$('#alternative-result').innerHTML=`<div class="alternative-result"><h4>Your original life is preserved.</h4><p>Accepted command ${index} was omitted. Later declared commands were replayed at their recorded times where possible.</p>${Object.keys(differences).length?`<ul>${Object.entries(differences).map(([k,v])=>`<li>${esc(k.replaceAll('_',' '))}: ${esc(v.original)} → ${esc(v.alternative)}</li>`).join('')}</ul>`:'<p>No difference appeared in the reported measures at the matching horizon.</p>'}${skipped.length?`<p class="warning">${skipped.length} later command(s) became infeasible.</p><ul>${skipped.map(x=>`<li>Command ${Number(x.index)}: ${esc(x.reason||'Not feasible in the alternative')}</li>`).join('')}</ul>`:'<p>All later declared commands remained feasible.</p>'}<p class="fine-print">${esc(result.interpretation||'One executed omission, with a fixed continuation. This does not prove a necessary cause or discover the best possible history.')}</p></div>`;telemetry('consequence_viewed');}
    finally{if(id===S.id&&button.isConnected){button.disabled=false;button.textContent='Execute this alternative →';}}
  }
  async function inspectEvidence(eventId) {
    const id=S.id;$('#evidence-content').innerHTML='<p role="status">Loading the participant’s accessible support…</p>';$('#evidence-dialog').showModal();
    try{const result=await S.gate.run(signal=>api('trace?id='+encodeURIComponent(id)+'&event_id='+eventId,undefined,signal));if(id!==S.id)return;$('#evidence-content').innerHTML=`<p>Related records provide support and accounting. An executed alternative tests a particular intervention.</p>${(result.events||[]).map(e=>`<article class="quiet-event"><small>${esc(timeLabel(e.tick??e.at))} · Record ${Number(e.event_id)}</small><p>${esc(human(e.payload?.title||e.title||e.payload?.category||'Recorded observation'))}</p>${e.payload?.value!==undefined&&['report','condition'].includes(e.payload?.category)?`<p>Recorded condition: ${esc(e.payload.value)} · observed ${esc(timeLabel(e.payload.as_of??e.tick))}</p>`:''}</article>`).join('')}${result.hidden_parent_count?'<p class="fine-print">Some related records are outside your participant’s knowledge.</p>':''}`;}catch(error){if(id===S.id)$('#evidence-content').innerHTML=`<p>${esc(error.message)}</p>`;notifyError(error);}
  }
  function openTime() {
    const stops=S.data?.time?.known_stops||S.data?.history?.known_stops||[],commitments=S.data?.known_commitments||S.data?.history?.known_commitments||[],minute=S.data?.snapshot?.minute||0;
    const imminent=stops.find(x=>Number(x.at??x.deadline)<=minute+1);
    $('#known-deadlines').innerHTML=stops.length?`<div class="known-deadlines"><p><strong>Known before you advance</strong></p>${stops.slice(0,5).map(x=>`<p>${esc(timeLabel(x.at??x.deadline))} · ${esc(x.title||text(x))}</p>`).join('')}<p>Stop at a known choice window first. Continuing after that point is another explicit choice.</p>${imminent?'<p>You are at the choice window. Letting this deadline pass settles the choices already recorded; missed promises may have consequences.</p><button class="button secondary" data-advance="1" data-mode="compress" data-protect="false">Let this known deadline pass →</button>':''}</div>`:commitments.length?`<div class="known-deadlines">${commitments.map(c=>`<p>${esc(text(c))}</p>`).join('')}</div>`:'<p class="fine-print">No future participant-known commitment is currently shown. An advance can still have consequences.</p>';
    $('#time-dialog').showModal();
  }
  async function advance(minutes, mode, protect=true) {
    const id=S.id;$('#time-dialog').close();status('Advancing this world through its exact scheduler…');
    await mutate('advance',{minutes,mode,protect_known:protect},r=>{if(id===S.id){const detail=r.protected_stop||r.stopped_at||r.stop;status(detail?'Stopped at a participant-known choice window. Review what is due before advancing again.':'Time advanced and the resulting history was saved.');}});
    if(id===S.id){host(id,'refresh');showReturnChanges();telemetry('consequence_viewed');}
  }
  function showReturnChanges() { const r=S.data?.return_summary||S.data?.history?.return_summary||{},summary=returnText(r);if(summary)showNotice('What followed.',summary); }
  async function renderLab(id,epoch) {
    const l=(S.catalog.lives||[]).find(l=>lifeId(l)===id);
    $('#main').innerHTML=`<div class="page prose-page">${pageHead('Research Lab','Beyond your participant’s view.')}<div class="lab-warning"><h2>This view reveals private information.</h2><p>It can show canonical truth, private minds and records your character may not know. Entering marks this life as operator-exposed for research analysis.</p><p>Hidden facts are not installed into the characters’ memories. This is a local operator tool, without production multi-user authorization.</p><button class="button" data-enter-lab="${esc(id)}">I understand · Open Lab <span aria-hidden="true">↗</span></button></div><a class="text-link" href="${lifeURL(id)}">Return to ${esc(l?.title||'this life')} <span aria-hidden="true">→</span></a></div>`;
  }
  async function enterLab(id) {
    const epoch=S.routeEpoch,r=await api('lab',{id,acknowledged:true});if(epoch!==S.routeEpoch||routeParts().path!=='/lab/'+id)return;S.lab=r;
    const snapshot=r.snapshot||r,lab=snapshot.lab||r.lab||{};
    $('#main').innerHTML=`<div class="page lab-container">${pageHead('Research Lab','The same life, an operator’s view.')}<p class="lab-exposed">Operator-exposed · This life is marked as having revealed private information.</p><a class="text-link" href="${lifeURL(id)}">Return to participant view <span aria-hidden="true">→</span></a><h2>Canonical truth</h2><p class="fine-print">This includes facts unavailable to the participant. Dependency links are recorded support, rather than automatic proof of necessary causes.</p><details><summary>Inspect full simulator truth</summary><pre>${esc(JSON.stringify(lab.truth||{},null,2))}</pre></details><h2>People, goals and retained evidence</h2>${Object.entries(lab.minds||{}).map(([actor,mind])=>`<details><summary>${esc(human(actor))} · Retained state</summary><pre>${esc(JSON.stringify(mind,null,2))}</pre></details>`).join('')}<details><summary>Accepted command history</summary><pre>${esc(JSON.stringify(lab.commands||[],null,2))}</pre></details></div>`;
  }
  async function renderStudio(epoch) {
    $('#main').innerHTML=`<div class="page prose-page">${pageHead('Experimental Studio','Author within real boundaries.','Create a supported variation of an existing world. The compiler has two finite adapters with fixed identities and executable rules.')}<div class="lab-warning"><h2>Authoring reveals initial private conditions.</h2><p>Studio is an operator surface. You can edit supported fields and validate a new identity. It cannot create arbitrary rules or execute untrusted scripts.</p><button class="button" id="open-studio">Open supported forms <span aria-hidden="true">→</span></button></div><a class="text-link" href="/worlds">Return to the worlds <span aria-hidden="true">→</span></a></div>`;
  }
  async function openStudio() {
    const t=S.catalog.templates?.[0];if(t)renderStudioForm(t.id);
  }
  function renderStudioForm(templateId) {
    const t=template(templateId);
    $('#main').innerHTML=`<div class="page">${pageHead('Experimental Studio','A supported variation.','Changes compile into a new identity. Existing lives and source templates are preserved.')}<form id="studio-form" class="studio-form"><label>Supported template<select name="template_id" id="studio-template">${(S.catalog.templates||[]).map(item=>`<option value="${esc(item.id)}" ${item.id===templateId?'selected':''}>${esc(item.title)}</option>`).join('')}</select></label><label>Title<input name="title" value="${esc((t?.title||'World')+' · authored variation')}" required maxlength="160"></label><fieldset><legend>Supported parameters</legend><label>Simulation seed<input name="seed" type="number" min="0" max="2147483647" step="1" value="2718" required></label><label>Horizon in world days<input name="horizon_days" type="number" min="1" max="365" step="1" value="30" required></label><p class="studio-note">The backend validator enforces supported ranges and dependencies. Actor IDs, initial private evidence, executable rules and arbitrary code cannot be changed here.</p></fieldset><div class="hero-actions"><button class="button secondary" type="button" id="validate-studio">Validate this specification</button><button class="button" type="submit">Compile into a new life →</button></div><div id="studio-result" role="status"></div></form></div>`;
  }
  function studioSpec() {const form=$('#studio-form');if(!form.reportValidity())return null;return {template_id:form.elements.template_id.value,title:form.elements.title.value.trim(),seed:Number(form.elements.seed.value),horizon_days:Number(form.elements.horizon_days.value)};}
  function telemetry(event) { if(!S.id||!S.data?.telemetry?.opt_in)return;const now=performance.now(),active_ms=document.hidden?0:Math.min(3600000,Math.max(0,Math.round(now-S.activeSince)));S.activeSince=now;api('telemetry',{id:S.id,event,active_ms,session_id:S.sessionId}).catch(()=>{}); }

  document.addEventListener('click',event=>{
    const a=event.target.closest('a[href]');
    if(a&&a.origin===location.origin&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey&&event.button===0&&!a.download&&!a.target){if(a.pathname.startsWith('/research/artifacts/')||a.pathname==='/legacy/'||a.pathname.startsWith('/immersion/'))return;event.preventDefault();navigate(a.pathname+a.search+a.hash);return;}
    const b=event.target.closest('button');if(!b||b.disabled)return;
    const task=async()=>{
      if(b.hasAttribute('data-close-dialog')){b.closest('dialog').close();return;}
      if(b.dataset.start){b.disabled=true;b.textContent='Creating a separate life…';try{const result=await api('start',{template_id:b.dataset.start});await loadCatalog();const id=lifeId(metadata(result));if(!id)throw Error('The server did not return a new life identity.');navigate(lifeURL(id));}finally{if(b.isConnected){b.disabled=false;b.textContent='Begin a new life →';}}return;}
      if(b.dataset.person){saveCommonDraft();S.selected.set(S.id,b.dataset.person);S.conversationEpoch++;renderObservatory();return;}
      if(b.dataset.action==='report'){await propose({action:'share',recipient:'team_b'});return;}
      if(b.dataset.action==='inspect'){await propose({action:'inspect'});return;}
      if(b.dataset.action==='promise'){await promiseDialog(b.dataset.recipient);return;}
      if(b.hasAttribute('data-open-time')){openTime();return;}
      if(b.dataset.advance){await advance(Number(b.dataset.advance),b.dataset.mode,b.dataset.protect!=='false');return;}
      if(b.dataset.evidence){await inspectEvidence(Number(b.dataset.evidence));return;}
      if(b.dataset.bookmark){const id=S.id;await api('annotation',{id,event_id:Number(b.dataset.bookmark)});if(id===S.id){await refreshLife();status('Bookmarked in your personal history.');}return;}
      if(b.hasAttribute('data-earlier-chapters')){S.chapterLimits.set(S.id,(S.chapterLimits.get(S.id)||8)+8);renderStory();return;}
      if(b.dataset.storyTab){S.storyTab=b.dataset.storyTab;renderStory();if(S.storyTab==='reflect')await loadReflection();return;}
      if(b.dataset.enterLab){b.disabled=true;try{await enterLab(b.dataset.enterLab);}finally{b.disabled=false;}return;}
      if(b.hasAttribute('data-dismiss-return')){await dismissReturn();return;}
      if(b.hasAttribute('data-reconcile')){await refreshLife();$('#world-notice').hidden=true;status('This life has been reconciled with its saved journal.');return;}
      if(b.dataset.saveDiagnostic){const life=(S.catalog.lives||[]).find(l=>lifeId(l)===b.dataset.saveDiagnostic);status(life?.error||life?.diagnostic||saveStatus(life?.save_status),12000);return;}
      if(b.id==='confirm-choice'){await confirmChoice();return;}
      if(b.id==='story-button'){navigate(lifeURL(S.id,'/history'));return;}
      if(b.id==='close-story'){closeStory();return;}
      if(b.id==='world-menu-button'){$('#world-menu').showModal();return;}
      if(b.id==='menu-time'){$('#world-menu').close();openTime();return;}
      if(b.id==='execute-alternative'){await executeAlternative();return;}
      if(b.id==='open-studio'){await openStudio();return;}
      if(b.id==='validate-studio'){const spec=studioSpec();if(!spec)return;const r=await api('studio/validate',spec);$('#studio-result').textContent=r.valid?'Valid supported specification. Compile to create a new life.':r.message||'Validation complete.';return;}
    };task().catch(notifyError);
  });
  async function promiseDialog(recipient) {
    $('#review-heading').textContent='Discuss a promise with '+personName(recipient);$('#review-error').textContent='';S.proposal=null;
    $('#review-content').innerHTML=`<p>A promise becomes an obligation. Choose the amount, then review the exact supported action.</p><form id="promise-form"><label for="promise-quantity">Capacity units for ${esc(personName(recipient))}</label><input style="display:block;width:100%;padding:12px;border:1px solid var(--line);background:var(--surface);margin:12px 0" id="promise-quantity" type="number" min="1" max="12" step="1" value="4" required><input type="hidden" id="promise-recipient" value="${esc(recipient)}"><button class="button" type="submit">Review this promise →</button></form>`;
    $('#confirm-choice').hidden=true;$('#review-dialog').showModal();
  }
  document.addEventListener('submit',event=>{
    if(!['allocation-form','common-speech','promise-form','studio-form','history-notes'].includes(event.target.id))return;event.preventDefault();
    const task=async()=>{
      if(event.target.id==='allocation-form'){saveCommonDraft();await propose({action:'allocate',allocation:Object.fromEntries(['team_a','team_b','team_c'].map(id=>[id,Number(event.target.elements[id].value)]))});}
      else if(event.target.id==='common-speech'){saveCommonDraft();const input=$('#common-speech-input'),utterance=input.value.trim();if(!utterance)return;const id=S.id,person=S.selected.get(id)||'team_b',conversationEpoch=S.conversationEpoch;status('Interpreting within the supported offline actions…');let result;try{result=await S.gate.run(signal=>api('intent',{id,text:utterance,recipient:person},signal));}catch(error){if(error.status===404){status('Try “ask for the report”, “inspect”, or use a suggested choice. This installation uses a finite offline grammar.');return;}throw error;}if(id!==S.id||conversationEpoch!==S.conversationEpoch)return;if(result.action){await propose(result.action);}else status(result.clarification||result.reply||result.message||'Choose a suggested action or ask about a report, inspection, promise or allocation.');}
      else if(event.target.id==='promise-form'){const quantity=Number($('#promise-quantity').value),recipient=$('#promise-recipient').value;$('#review-dialog').close();$('#confirm-choice').hidden=false;await propose({action:'commit',recipient,quantity});}
      else if(event.target.id==='studio-form'){const spec=studioSpec();if(!spec)return;const r=await api('studio/compile',spec);await loadCatalog();navigate(lifeURL(lifeId(metadata(r))));}
      else if(event.target.id==='history-notes'){const id=S.id,note=$('#personal-note').value.trim();if(!note)return;await api('annotation',{id,note});if(id===S.id){draft(id).note='';await refreshLife();status('Personal note saved separately from world history.');}}
    };task().catch(error=>{if(event.target.id==='studio-form'&&$('#studio-result'))$('#studio-result').textContent=error.message;notifyError(error);});
  });
  document.addEventListener('input',event=>{if(event.target.closest('#observatory-stage'))saveCommonDraft();if(event.target.id==='personal-note'&&S.id)draft(S.id).note=event.target.value;});
  document.addEventListener('change',event=>{
    if(event.target.id==='reflect-choice')renderThenEvidence();
    if(event.target.id==='telemetry-opt-in'&&S.id){const opt_in=event.target.checked,id=S.id,epoch=S.gate.epoch;event.target.disabled=true;S.readVersions.set(id,(S.readVersions.get(id)||0)+1);api('telemetry',{id,opt_in}).then(()=>{S.readVersions.set(id,(S.readVersions.get(id)||0)+1);if(id!==S.id||epoch!==S.gate.epoch)return;if(S.data)S.data.telemetry={...S.data.telemetry,opt_in};status(opt_in?'Optional usage events are enabled locally.':'Optional usage events are disabled.');}).catch(error=>{if(id!==S.id||epoch!==S.gate.epoch)return;event.target.checked=!opt_in;notifyError(error);}).finally(()=>{event.target.disabled=false;});}
    if(event.target.id==='studio-template')renderStudioForm(event.target.value);
  });
  $('#review-dialog').addEventListener('close',()=>{if(!S.pending.has(S.id))S.proposal=null;$('#confirm-choice').hidden=false;});
  $('#story-backdrop').addEventListener('click',()=>closeStory());
  document.addEventListener('keydown',event=>{
    const drawer=$('#story-drawer');if(drawer.hidden||$('dialog[open]'))return;
    if(event.key==='Escape'){event.preventDefault();closeStory();return;}
    if(event.key==='Tab'){const nodes=[...drawer.querySelectorAll('button:not(:disabled),a[href],select,input,textarea,summary')].filter(n=>n.getClientRects().length);if(!nodes.length)return;const first=nodes[0],last=nodes.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
  });
  window.addEventListener('message',event=>{
    const id=event.data?.life_id||event.data?.experience,item=S.frames.get(id);if(!acceptsSceneMessage(event,item?.frame,location.origin,id))return;
    if(event.data.kind==='kalends:scene'){
      const request=item.requests.get(event.data.request_id);
      if(event.data.view&&event.data.status!=='ready'){
        S.views.set(id,event.data.view);try{sessionStorage.setItem('kalends:scene:'+id,JSON.stringify(event.data.view));}catch(_){}
      }
      if(event.data.status==='ready'){item.ready=true;item.loading.hidden=true;const initialView=item.initialView;item.initialView=null;if(id===S.id&&$('#story-drawer').hidden){item.wrapper.hidden=false;host(id,initialView?'restore':'refresh',initialView);}else host(id,'pause');}
      if(event.data.status==='pending'&&request&&['refresh','restore'].includes(request.action)){
        item.pendingRequest=request;clearTimeout(item.retryTimer);
        if(id===S.id&&!document.hidden&&$('#story-drawer').hidden&&item.retryCount<7){const delay=Math.min(1200,100*2**item.retryCount++);item.retryTimer=setTimeout(()=>{if(id===S.id&&!document.hidden&&$('#story-drawer').hidden){item.wrapper.hidden=false;host(id,request.action,request.view);}},delay);}
      }
      if(event.data.status==='ok'&&request&&['refresh','restore'].includes(request.action)){item.pendingRequest=null;item.retryCount=0;clearTimeout(item.retryTimer);}
      if(event.data.status==='error'&&id===S.id)status(event.data.error||'The scene could not refresh its saved state.');
    }
    if(event.data.kind==='kalends:accepted'&&id===S.id){refreshLife().then(()=>{telemetry('meaningful_action');if(item.pendingRequest&&!document.hidden&&$('#story-drawer').hidden){item.wrapper.hidden=false;const pending=item.pendingRequest;host(id,pending.action,pending.view);}}).catch(notifyError);}
  });
  window.addEventListener('popstate',()=>route().catch(notifyError));
  document.addEventListener('visibilitychange',()=>{S.activeSince=performance.now();if(document.hidden)pauseFrames();else if(S.id&&$('#story-drawer').hidden){const item=S.frames.get(S.id);if(item){item.wrapper.hidden=false;host(S.id,item.pendingRequest?.action||'refresh',item.pendingRequest?.view);}}});
  route().catch(error=>{notifyError(error);$('#main').innerHTML=errorPage('Kalends could not connect.',error.message,'/','Try again');});
})(typeof window!=='undefined'?window:globalThis);
