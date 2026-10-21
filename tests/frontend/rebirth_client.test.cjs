'use strict';
// Offline integration checks of the shipped script. No browser, socket or DOM library.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/app.js'), 'utf8');
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
  closest(selector) { return selector === 'button' && this.tag === 'button' ? this : null; }
  setAttribute(name, value) { this[name] = value; }
  focus() {}
  scrollIntoView() {}
  setPointerCapture() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  getBoundingClientRect() { return {left: 0, top: 0, width: 1280, height: 720}; }
}

function fixture({inside = false, telemetry = false} = {}) {
  const locations = [
    {id: 'bakery', name: 'Bread counter', x: 650, y: 80, w: 320, h: 230, door: {x: 810, y: 350}, interior: true},
    {id: 'fullery', name: 'Fullery', x: 220, y: 500, w: 330, h: 240, door: {x: 385, y: 480}, interior: true},
  ];
  return {mode: 'game', telemetry_enabled: telemetry, world: {
    minute: 0, day: 1, clock: '08:00', historical_note: 'Fictional fixture',
    player: {id: 'Player', name: 'Aelia', cash: 10, inventory: 0, x: inside ? 810 : 650, y: inside ? 275 : 415, location: inside ? 'bakery' : 'street', path: [], progression: {access: []}, commitments: [], commissions: []},
    agents: [{id: 'Felix', name: 'Felix', role: 'baker', x: inside ? 810 : 750, y: inside ? 230 : 415, location: inside ? 'bakery' : 'street'}],
    nearby: ['Felix'], map: {width: 1600, height: 1100, locations},
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
  handlers.set('/api/move', body => { state = copy(state); state.world.minute++; if (body.location === 'street') state.world.player.location = 'street'; else if (body.location) state.world.player.location = body.location; else Object.assign(state.world.player, body); state.world.player.path = []; return copy(state); });
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
  vm.runInNewContext(source, sandbox, {filename: 'app.js'});
  const flush = async () => { await new Promise(setImmediate); };
  await flush(); assert.equal(element('#loading').hidden, true, 'fixture boot must finish');
  const click = async selector => { await element(selector).onclick?.({target: element(selector), preventDefault() {}}); await flush(); };
  const documentClick = async dataset => { const button = new Element('fixture-button', 'button'); button.dataset = dataset; await document.emit('click', {target: button}); await flush(); };
  const walk = async () => { await canvas.emit('pointerdown', {clientX: 640, clientY: 400, button: 0}); await canvas.emit('pointerup', {clientX: 640, clientY: 400}); await flush(); };
  const frame = time => { const callback = frames.shift(); assert.ok(callback, 'animation frame registered'); const before = drawCalls.length; callback(time); return drawCalls.slice(before); };
  return {element, document, requests, handlers, flush, click, documentClick, walk, frame, setState: value => { state = value; }};
}

test('a closed conversation ignores a delayed context response', async () => {
  const h = await harness(), pending = deferred();
  h.handlers.set('/api/context?recipient=Felix', () => pending.promise);
  await h.click('#enter'); await h.click('#interact');
  await h.document.emit('keydown', {key: 'Escape', target: h.element('#town')});
  pending.resolve(conversation()); await h.flush();
  assert.equal(h.element('#conversation').hidden, true);
  assert.equal(h.document.body.classList.contains('talking'), false);
  await h.walk(); assert.equal(h.requests.filter(r => r.url === '/api/move').length, 1);
});

test('reopening the same person cannot be overwritten by the earlier conversation', async () => {
  const h = await harness(), pending = deferred(); let contextCalls = 0;
  const fresh = conversation(); fresh.greeting.text = 'The new terms are ready.';
  h.handlers.set('/api/context?recipient=Felix', () => contextCalls++ === 0 ? pending.promise : fresh);
  await h.click('#enter'); await h.click('#interact');
  await h.document.emit('keydown', {key: 'Escape', target: h.element('#town')});
  await h.click('#interact');
  assert.equal(h.element('#dialogue-line').textContent, fresh.greeting.text);
  const old = conversation(); old.greeting.text = 'The old terms are stale.';
  pending.resolve(old); await h.flush();
  assert.equal(h.element('#conversation').hidden, false);
  assert.equal(h.element('#dialogue-line').textContent, fresh.greeting.text);
});

test('a late proposal cannot leave a hidden review blocking later movement', async () => {
  const h = await harness(), pending = deferred();
  h.handlers.set('/api/propose', () => pending.promise);
  await h.click('#enter'); await h.click('#interact'); await h.documentClick({choice: 'buy'});
  assert.equal(h.requests.filter(r => r.url === '/api/propose').length, 1);
  await h.click('#close-conversation'); pending.resolve(proposal()); await h.flush();
  assert.equal(h.element('#conversation').hidden, true);
  await h.walk(); assert.equal(h.requests.filter(r => r.url === '/api/move').length, 1);
});

test('a failed proposal releases its request lock and keeps movement usable', async () => {
  const h = await harness(); h.handlers.set('/api/propose', () => { throw new Error('Fixture provider unavailable'); });
  await h.click('#enter'); await h.click('#interact'); await h.documentClick({choice: 'buy'});
  assert.match(h.element('#toast').textContent, /provider unavailable/);
  await h.click('#close-conversation'); await h.walk();
  assert.equal(h.requests.filter(r => r.url === '/api/move').length, 1);
});

test('an unavailable reviewed trade shows its exact price and reason with confirmation disabled', async () => {
  const h = await harness(), quote = proposal();
  Object.assign(quote.interpretations[0], {cost: '4 × 2 = 8 coins', available: false, unavailable_reason: 'You need 8 coins for this purchase.'});
  h.handlers.set('/api/propose', () => quote);
  await h.click('#enter'); await h.click('#interact'); await h.documentClick({choice: 'buy'});
  const review = h.element('#proposal').innerHTML;
  assert.match(review, /4 × 2 = 8 coins/);
  assert.match(review, /You need 8 coins for this purchase\./);
  assert.match(review, /data-confirm="0" disabled/);
  assert.equal(h.requests.filter(r => r.url === '/api/act').length, 0);
});

test('consent changes are serialized and restore authoritative saved state', async () => {
  const h = await harness(), pending = deferred();
  h.handlers.set('/api/settings', () => pending.promise);
  const checkbox = h.element('#telemetry'); checkbox.checked = true;
  const save = checkbox.onchange({target: checkbox});
  assert.equal(checkbox.disabled, true);
  checkbox.checked = false; await checkbox.onchange({target: checkbox});
  assert.equal(h.requests.filter(r => r.url === '/api/settings').length, 1);
  pending.resolve(fixture({telemetry: true})); await save; await h.flush();
  assert.equal(checkbox.checked, true); assert.equal(checkbox.disabled, false);
  h.handlers.set('/api/settings', () => fixture({telemetry: false})); checkbox.checked = false;
  await checkbox.onchange({target: checkbox});
  assert.equal(checkbox.checked, false); assert.equal(checkbox.disabled, false);
  assert.deepEqual(h.requests.filter(r => r.url === '/api/settings').map(r => r.body.telemetry_enabled), [true, false]);
});

test('failed consent persistence restores the prior state and permits retry', async () => {
  const h = await harness({telemetry: true});
  h.handlers.set('/api/settings', () => { throw new Error('Fixture save failed'); });
  const checkbox = h.element('#telemetry'); checkbox.checked = false;
  await checkbox.onchange({target: checkbox});
  assert.equal(checkbox.checked, true); assert.equal(checkbox.disabled, false);
  assert.match(h.element('#toast').textContent, /save failed/);
  h.handlers.set('/api/settings', () => fixture({telemetry: false})); checkbox.checked = false;
  await checkbox.onchange({target: checkbox});
  assert.equal(checkbox.checked, false); assert.equal(checkbox.disabled, false);
  assert.equal(h.requests.filter(r => r.url === '/api/settings').length, 2);
});

test('walking from one interior to another renders the intervening street', async () => {
  const h = await harness({inside: true}); await h.click('#enter');
  const first = h.frame(50); assert.ok(first.some(call => call[0].src.endsWith('/interiors.png')));
  const destination = fixture({inside: true}); destination.world.minute = 10;
  Object.assign(destination.world.player, {x: 385, y: 704, location: 'fullery', path: [[810, 275], [810, 350], [810, 415], [385, 415], [385, 480], [385, 704]]});
  h.handlers.set('/api/move', () => destination);
  await h.documentClick({visit: 'fullery'});
  const scenes = [];
  for (let time = 100; time <= 6000; time += 50) {
    const background = h.frame(time).find(call => /\/(street|interiors)\.png$/.test(call[0].src));
    if (background) scenes.push({asset: background[0].src, cropY: background[2]});
  }
  assert.ok(scenes.some(scene => scene.asset.endsWith('/street.png')), 'actual exterior must appear between rooms');
  const last = scenes.at(-1); assert.ok(last.asset.endsWith('/interiors.png')); assert.equal(last.cropY, 512, 'fullery is atlas cell2');
  assert.equal(h.document.body.classList.contains('inside'), true);
  assert.equal(h.element('#exit-room').hidden, false);
});
