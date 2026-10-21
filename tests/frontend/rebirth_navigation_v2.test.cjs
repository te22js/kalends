'use strict';
// Offline integration of BOTH shipped scripts with V2 capabilities. Server and
// painting are independently gated; native focus and actual latency need UI QA.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/app.js'), 'utf8');
const navigationSource = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/navigation.js'), 'utf8');
const markup = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/index.html'), 'utf8');
const copy = value => JSON.parse(JSON.stringify(value));
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return {promise, resolve, reject}; };

class Element {
  constructor(id, tag = 'div') {
    this.id = id; this.tag = tag; this.hidden = false; this.open = false;
    this.checked = false; this.disabled = false; this.value = ''; this.dataset = {};
    this.textContent = ''; this.innerHTML = ''; this.listeners = new Map();
    const classes = new Set();
    this.classList = { add: name => classes.add(name), remove: name => classes.delete(name), contains: name => classes.has(name), toggle(name, force) { const enabled = force ?? !classes.has(name); enabled ? classes.add(name) : classes.delete(name); return enabled; } };
    this.style = {setProperty() {}};
  }
  addEventListener(name, fn) { this.listeners.set(name, [...(this.listeners.get(name) || []), fn]); }
  async emit(name, event = {}) { for (const fn of this.listeners.get(name) || []) await fn({target: this, preventDefault() {}, ...event}); }
  closest(selector) { return selector.split(',').includes(this.tag) ? this : null; }
  setAttribute(name, value) { this[name] = value; }
  focus() {}
  scrollIntoView() {}
  setPointerCapture() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  getBoundingClientRect() { return {left: 0, top: 0, width: 1280, height: 720}; }
}

function fixture({inside = false, telemetry = false, atDoor = false, withSabina = false} = {}) {
  const locations = [
    {id: 'bakery', name: 'Bread counter', x: 650, y: 80, w: 320, h: 230, door: {x: 810, y: 350}, interior: true},
    {id: 'fullery', name: 'Fullery', x: 220, y: 500, w: 330, h: 240, door: {x: 385, y: 480}, interior: true},
  ];
  return {mode: 'game', capabilities: {navigation_revision: 2, route_preview: true}, telemetry_enabled: telemetry, world: {
    minute: 0, day: 1, clock: '08:00', historical_note: 'Fictional fixture',
    player: {id: 'Player', name: 'Aelia', cash: 10, inventory: 0, x: inside || atDoor ? 810 : 650, y: inside ? 275 : atDoor ? 350 : 415, location: inside ? 'bakery' : 'street', path: [], progression: {access: []}, commitments: [], commissions: []},
    agents: [{id: 'Felix', name: 'Felix', role: 'baker', x: inside ? 810 : 750, y: inside ? 230 : 415, location: inside ? 'bakery' : 'street'}, ...(withSabina ? [{id:'Sabina',name:'Sabina',role:'food seller',x:700,y:415,location:'street'}] : [])],
    nearby: withSabina ? ['Felix','Sabina'] : ['Felix'], map: {width: 1600, height: 1100, locations},
    objective: {title: 'Two promises', description: 'Find the terms.'},
    story: {stage: 'unresolved', route: null, leads: []}, journal: [],
  }};
}
const conversation = () => ({speaker: 'Felix', greeting: {text: 'The flour must arrive.'}, topics: [{id: 'role', label: 'Your life here', text: 'I bake.'}], choices: [{id: 'buy', label: 'Buy one flour unit', description: 'A real trade.', cost: '2 coins', enabled: true, action: {action: 'buy', recipient: 'Felix', quantity: 1}}], relationship: {reliability: .6, credibility: .6, affinity: .5, favors: 0}});
const proposal = () => ({proposal_id: 'review-1', interpretations: [{id: '0', label: 'Buy one flour unit', transmission: 'A real trade.', action: {action: 'buy', recipient: 'Felix', quantity: 1}}]});

async function harness(options = {}) {
  const elements = new Map();
  for (const match of markup.matchAll(/<([a-z][\w-]*)\b([^>]*\bid="([^"]+)"[^>]*)>/gi)) {
    const element = new Element(match[3], match[1]); element.hidden = /\bhidden\b/.test(match[2]); elements.set('#' + match[3], element);
  }
  const element = selector => { if (!elements.has(selector)) elements.set(selector, new Element(selector)); return elements.get(selector); };
  const document = new Element('document'); document.body = new Element('body'); document.hidden = false;
  document.querySelector = selector => selector === 'dialog[open]' ? [...elements.values()].find(e => e.tag === 'dialog' && e.open) || null : element(selector);
  document.querySelectorAll = selector => {
    if (selector === '#pace button') return ['live', 'wait', 'montage', 'map-button'].map(id => element('#' + id));
    if (selector === '[data-tab]') return ['story', 'people', 'bag', 'places', 'records'].map(tab => { const e = element('tab:' + tab); e.dataset.tab = tab; return e; });
    if (selector === '[data-direction]') return ['up', 'down', 'left', 'right'].map(direction => { const e = element('direction:' + direction); e.dataset.direction = direction; return e; });
    return [];
  };
  const canvas = element('#town'); canvas.clientWidth = 1280; canvas.clientHeight = 720;
  const drawCalls = [], frames = [];
  canvas.getContext = () => new Proxy({measureText: text => ({width: text.length * 6}), drawImage: (...args) => drawCalls.push(args)}, {get: (target, key) => key in target ? target[key] : () => {}});
  const requests = [], handlers = new Map(), timers = new Map(); let timerId = 0, state = fixture(options);
  handlers.set('/api/state', () => copy(state));
  handlers.set('/api/context?recipient=Felix', () => conversation());
  handlers.set('/api/context?recipient=Sabina', () => ({...conversation(),speaker:'Sabina',choices:[]}));
  handlers.set('/api/route', body => ({points: [copy(state.world.player), {x: body.x ?? 810, y: body.y ?? 275, location: body.location || state.world.player.location}], destination: {x: body.x ?? 810, y: body.y ?? 275, location: body.location || state.world.player.location}}));
  handlers.set('/api/mode', body => { state = copy(state); state.mode = body.mode; return copy(state); });
  handlers.set('/api/advance', body => { state = copy(state); state.world.minute += body.minutes; return copy(state); });
  handlers.set('/api/move', body => { state = copy(state); state.world.minute++; Object.assign(state.world.player, body); state.world.player.path = []; return copy(state); });
  const sandbox = {
    document, window: new Element('window'), console, devicePixelRatio: 1,
    matchMedia: () => ({matches: false}), localStorage: {getItem: () => null, setItem() {}},
    requestAnimationFrame: callback => frames.push(callback), performance: {now: () => 0},
    setTimeout: callback => { timers.set(++timerId, callback); return timerId; }, clearTimeout: id => timers.delete(id),
    Image: class { set src(value) { this.srcValue = value; queueMicrotask(() => this.onload()); } get src() { return this.srcValue; } },
    fetch: async (url, init = {}) => {
      const request = {url, body: init.body ? JSON.parse(init.body) : undefined}; requests.push(request);
      const handler = handlers.get(url); if (!handler) throw new Error('Unexpected fixture endpoint: ' + url);
      const result = await handler(request.body);
      return {ok: true, json: async () => copy(result)};
    },
  };
  vm.runInNewContext(navigationSource, sandbox, {filename: 'navigation.js'});
  vm.runInNewContext(source, sandbox, {filename: 'app.js'});
  const flush = async () => { await new Promise(setImmediate); };
  await flush(); assert.equal(element('#loading').hidden, true, 'fixture boot must finish');
  const click = async selector => { await element(selector).onclick?.({target: element(selector), preventDefault() {}}); await flush(); };
  const documentClick = async dataset => { const button = new Element('fixture-button', 'button'); button.dataset = dataset; await document.emit('click', {target: button}); await flush(); };
  const walk = async () => { await canvas.emit('pointerdown', {clientX: 640, clientY: 400, button: 0}); await canvas.emit('pointerup', {clientX: 640, clientY: 400}); await flush(); };
  const frame = time => { const callback = frames.shift(); assert.ok(callback, 'animation frame registered'); const before = drawCalls.length; callback(time); return drawCalls.slice(before); };
  return {element, document, window: sandbox.window, requests, handlers, flush, click, documentClick, walk, frame, getState: () => copy(state), setState: value => { state = value; }};
}

const moves = h => h.requests.filter(r => r.url === '/api/move');
const previews = h => h.requests.filter(r => r.url === '/api/route');
async function paintUntilSettled(h, frames = 60, start = 100) {
  for (let i = 0; i < frames; i++) { h.frame(start+i*33); await h.flush(); }
}

test('V2 shipped app preserves a key tap released before RAF', async () => {
  const h = await harness(); await h.click('#enter');
  await h.document.emit('keydown', {key: 'ArrowRight', target: h.element('#town')});
  await h.document.emit('keyup', {key: 'ArrowRight', target: h.element('#town')}); await h.flush();
  assert.equal(previews(h).length, 1); assert.equal(moves(h).length, 1);
  assert.deepEqual(moves(h)[0].body, {x: 676, y: 415});
  await paintUntilSettled(h); assert.equal(moves(h).length, 1);
});

test('V2 Stop cancels the uncommitted tail of a click walk', async () => {
  const h = await harness(); await h.click('#enter'); await h.walk();
  assert.equal(moves(h).length, 1); assert.match(h.element('#interact').innerHTML, /Stop/);
  await h.click('#interact'); await paintUntilSettled(h);
  assert.equal(moves(h).length, 1);
});

test('V2 journal open discards a pending read-only route response', async () => {
  const h = await harness(), gate = deferred(); h.handlers.set('/api/route', () => gate.promise);
  await h.click('#enter'); await h.walk(); await h.click('#journal-button');
  gate.resolve({points: [{x: 650, y: 415, location: 'street'}, {x: 900, y: 415, location: 'street'}], destination: {x: 900, y: 415, location: 'street'}});
  await h.flush(); await h.click('#close-journal'); await paintUntilSettled(h);
  assert.equal(moves(h).length, 0); assert.equal(h.element('#journal').hidden, true);
});

test('V2 journal open during a step preserves that step and discards the rest', async () => {
  const h = await harness(), gate = deferred(); h.handlers.set('/api/move', body => gate.promise.then(() => { const next = h.getState(); Object.assign(next.world.player, body); h.setState(next); return next; }));
  await h.click('#enter'); await h.walk(); await h.click('#journal-button');
  assert.equal(moves(h).length, 1); gate.resolve(); await h.flush();
  await h.click('#close-journal'); await paintUntilSettled(h);
  assert.equal(moves(h).length, 1);
});

test('V2 focus loss cancels the remaining walk rather than resuming on return', async () => {
  const h = await harness(); await h.click('#enter'); await h.walk();
  await h.window.emit('blur'); await paintUntilSettled(h);
  assert.equal(moves(h).length, 1);
});

test('V2 Lab inspection cancels walking before and after the modal closes', async () => {
  const h = await harness(); await h.click('#enter'); await h.walk();
  await h.click('#open-lab'); assert.equal(h.element('#lab').open, true);
  await h.click('#close-lab'); assert.equal(h.element('#lab').open, false);
  await paintUntilSettled(h); assert.equal(moves(h).length, 1);
});

test('V2 waiting cancels a walk before advancing the world', async () => {
  const h = await harness(); await h.click('#enter'); await h.walk(); await h.click('#wait');
  assert.equal(h.requests.filter(r => r.url === '/api/advance').length, 1);
  await paintUntilSettled(h); assert.equal(moves(h).length, 1);
});

test('V2 direction rejected during conversation cannot resume after closing it', async () => {
  const h = await harness(); await h.click('#enter'); await h.click('#interact');
  assert.equal(h.element('#conversation').hidden, false);
  await h.document.emit('keydown', {key: 'ArrowRight', target: h.element('#town')});
  await h.click('#close-conversation'); await paintUntilSettled(h);
  assert.equal(moves(h).length, 0);
});

test('V2 HUD room label follows the displayed scene at a portal', async () => {
  const h = await harness({atDoor: true}); await h.click('#enter'); const before = h.element('#place-label').textContent;
  // A real portal commit changes authority first. The fixture deliberately
  // leaves the displayed actor 55 units outside, independently of the response.
  h.handlers.set('/api/route', () => ({points: [{x: 810, y: 350, location: 'street'}, {x: 810, y: 295, location: 'bakery'}], destination: {x: 810, y: 295, location: 'bakery'}}));
  await h.walk(); assert.equal(moves(h).length, 1);
  assert.equal(h.element('#place-label').textContent, before, 'room label must not jump ahead of the street image');
});


test('V2 Lab waits for an accepted step response before requesting the mode change', async () => {
  const h = await harness(), gate = deferred();
  h.handlers.set('/api/move', body => gate.promise.then(() => { const next = h.getState(); Object.assign(next.world.player, body); h.setState(next); return next; }));
  await h.click('#enter'); await h.walk();
  const opening = h.click('#open-lab'); await h.flush();
  assert.equal(h.requests.filter(r => r.url === '/api/mode').length, 0, 'mode change must not race a movement response');
  gate.resolve(); await opening; await h.flush();
  assert.equal(h.requests.filter(r => r.url === '/api/mode').length, 1); assert.equal(h.element('#lab').open, true);
  await h.click('#close-lab'); await paintUntilSettled(h); assert.equal(moves(h).length, 1);
});


test('Escape closes a conversation while the speech input has keyboard focus', async () => {
  const h = await harness(); await h.click('#enter'); await h.click('#interact');
  let prevented = false;
  await h.document.emit('keydown', {key: 'Escape', target: h.element('#speech'), preventDefault() { prevented = true; }});
  assert.equal(h.element('#conversation').hidden,true); assert.equal(prevented,true);
  await h.walk(); assert.equal(moves(h).length,1,'closing from the input must release conversation movement blocking');
});

test('Escape inside an open native dialog is left to its native cancellation path', async () => {
  const h = await harness(); await h.click('#enter'); await h.click('#interact');
  h.element('#settings').showModal(); let prevented = false;
  await h.document.emit('keydown', {key: 'Escape', target: h.element('#telemetry'), preventDefault() { prevented = true; }});
  assert.equal(prevented,false,'the document handler must preserve browser dialog cancellation');
  assert.equal(h.element('#conversation').hidden,false,'a native dialog Escape must not close the underlying conversation');
  // This VM does not pretend to execute a browser's default dialog action.
});

test('Lab native cancel still performs its authoritative game-mode transition', async () => {
  const h = await harness(); await h.click('#enter'); await h.click('#open-lab');
  let prevented = false;
  await h.element('#lab').emit('cancel', {preventDefault() { prevented = true; }}); await h.flush();
  assert.equal(prevented,true,'Lab waits for its mode transaction before closing');
  assert.equal(h.element('#lab').open,false); assert.equal(h.getState().mode,'game');
});

test('focus loss discards an unfinished left click rather than accepting a late pointerup', async () => {
  const h = await harness(); await h.click('#enter');
  await h.element('#town').emit('pointerdown',{clientX:640,clientY:400,button:0});
  await h.window.emit('blur');
  await h.element('#town').emit('pointerup',{clientX:640,clientY:400,button:0}); await h.flush();
  assert.equal(moves(h).length,0);
  await h.walk(); assert.equal(moves(h).length,1,'a fresh click after return must remain usable');
});

for (const interruption of ['blur','pointercancel','lostpointercapture']) {
  test('an interrupted camera drag does not swallow the next click: '+interruption, async () => {
    const h = await harness(); await h.click('#enter');
    await h.element('#town').emit('pointerdown',{clientX:640,clientY:400,button:1,pointerId:7});
    if(interruption === 'blur') await h.window.emit('blur');
    else await h.element('#town').emit(interruption,{pointerId:7});
    await h.walk(); assert.equal(moves(h).length,1);
  });
}


test('unsent speech survives reopening its recipient and clears when changing recipient', async () => {
  const h = await harness({withSabina:true}); await h.click('#enter'); await h.click('#interact');
  h.element('#speech').value = 'What do you remember?';
  await h.document.emit('keydown',{key:'Escape',target:h.element('#speech')});
  await h.click('#interact'); assert.equal(h.element('#speech').value,'What do you remember?');
  await h.click('#close-conversation'); await h.documentClick({approach:'Sabina'});
  assert.equal(h.element('#speaker-name').textContent,'Sabina'); assert.equal(h.element('#speech').value,'');
  assert.equal(h.requests.filter(r=>r.url==='/api/propose').length,0,'switching recipient must not submit the abandoned draft');
});

test('a delayed old context cannot clear the new recipient speech draft', async () => {
  const h = await harness({withSabina:true}), pending = deferred();
  h.handlers.set('/api/context?recipient=Felix',()=>pending.promise);
  await h.click('#enter'); await h.click('#interact');
  await h.document.emit('keydown',{key:'Escape',target:h.element('#town')});
  await h.documentClick({approach:'Sabina'}); h.element('#speech').value = 'My question for Sabina';
  pending.resolve(conversation()); await h.flush();
  assert.equal(h.element('#speaker-name').textContent,'Sabina');
  assert.equal(h.element('#speech').value,'My question for Sabina');
  assert.equal(h.requests.filter(r=>r.url==='/api/propose').length,0);
});
