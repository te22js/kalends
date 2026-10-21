'use strict';
// Exercise the shipped controller with independent server/paint gates. This is
// not a browser test: real focus, key timing, portals and paint require UI QA.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/navigation.js'), 'utf8');
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return {promise, resolve, reject}; };
const flush = () => new Promise(setImmediate);
const copy = value => JSON.parse(JSON.stringify(value));

function harness() {
  const window = {};
  vm.runInNewContext(source, {window}, {filename: 'navigation.js'});
  let position = {x: 100, y: 415, location: 'street'}, remaining = 0, direction = {dx: 0, dy: 0}, blocked = false;
  const requests = [], commits = [], arrivals = [], errors = [], inputs = [];
  let preview = body => Promise.resolve({points: [copy(position), {...body, location: body.location || position.location}], destination: {...body, location: body.location || position.location}});
  let commit = body => {
    const request = {body: copy(body), start: copy(position), gate: deferred()}; commits.push(request);
    return request.gate.promise.then(() => { remaining = Math.hypot(body.x-position.x, body.y-position.y); position = {...position, ...body}; });
  };
  const nav = new window.KalendsNavigation({
    blocked: () => blocked, position: () => copy(position), remaining: () => remaining, direction: () => direction,
    clearKeys: () => { direction = {dx: 0, dy: 0}; },
    preview: body => { requests.push(copy(body)); return preview(body); },
    commit: body => commit(body), started() {}, changed() {}, target() {},
    arrived: id => arrivals.push(id), error: error => errors.push(error.message),
    trace: {record() {}, input: (...data) => inputs.push(data)},
  });
  return {
    nav, requests, commits, arrivals, errors, inputs,
    setPreview: fn => { preview = fn; }, setCommit: fn => { commit = fn; },
    setDirection: value => { direction = value; }, setBlocked: value => { blocked = value; },
    paint: distance => { remaining = distance; nav.tick(); },
    position: () => position,
    settle: async index => { commits[index].gate.resolve(); await flush(); },
  };
}

test('a tap remains queued after key release before any animation frame', async () => {
  const h = harness();
  h.setDirection({dx: 1, dy: 0}); assert.equal(h.nav.nudge(1, 0), true);
  h.setDirection({dx: 0, dy: 0}); await flush();
  assert.equal(h.commits.length, 1); assert.deepEqual(h.commits[0].body, {x: 126, y: 415});
  await h.settle(0); h.paint(0); await flush();
  assert.equal(h.commits.length, 1, 'release must not become a held walk');
  assert.equal(h.nav.active, false);
});

test('diagonal tap covers 26 units instead of gaining diagonal speed', async () => {
  const h = harness(); h.nav.nudge(1, 1); await flush();
  const q = h.commits[0].body;
  assert.ok(Math.abs(Math.hypot(q.x-100, q.y-415)-26) < 1e-9);
});

test('long routes commit one short step and wait for visible catch-up', async () => {
  const h = harness(); h.nav.go({x: 800, y: 415}); await flush();
  assert.equal(h.commits.length, 1); assert.equal(h.commits[0].body.x, 148);
  h.nav.tick(); h.nav.tick(); assert.equal(h.commits.length, 1, 'only one request in flight');
  await h.settle(0); assert.equal(h.commits.length, 1, '48 unpainted units must gate the next request');
  h.paint(12); await flush(); assert.equal(h.commits.length, 2);
  assert.equal(h.commits[1].body.x, 196);
});

test('retarget during a committed step preserves that step and replaces its tail', async () => {
  const h = harness(); h.nav.go({x: 800, y: 415}); await flush();
  assert.equal(h.nav.go({x: 80, y: 415}), true); await flush();
  assert.equal(h.requests.length, 1, 'new route waits for in-flight step to settle');
  await h.settle(0); h.paint(0); await flush();
  assert.equal(h.position().x, 148, 'accepted movement is not rolled back');
  assert.equal(h.requests.length, 2); assert.equal(h.requests[1].x, 80);
  assert.equal(h.commits.length, 2); assert.equal(h.commits[1].body.x, 100);
});

test('opposite directional tap replaces a click route while its step is pending', async () => {
  const h = harness(); h.nav.go({x: 800, y: 415}); await flush(); h.nav.nudge(-1, 0);
  await h.settle(0); h.paint(0); await flush();
  assert.deepEqual(h.commits[1].body, {x: 122, y: 415});
  await h.settle(1); h.paint(0); await flush();
  assert.equal(h.commits.length, 2); assert.equal(h.nav.active, false);
});

test('Stop while a step is pending permits only that already accepted step', async () => {
  const h = harness(); h.nav.go({x: 800, y: 415}, 'Felix'); await flush(); h.nav.cancel('player stopped');
  await h.settle(0); h.paint(0); await flush();
  assert.equal(h.position().x, 148); assert.equal(h.commits.length, 1);
  assert.equal(h.nav.active, false); assert.deepEqual(h.arrivals, []);
});

test('cancelled read-only preview never commits a destination', async () => {
  const h = harness(), gate = deferred(); h.setPreview(() => gate.promise);
  h.nav.go({x: 800, y: 415}); h.nav.cancel('journal opened');
  gate.resolve({points: [{x: 100, y: 415, location: 'street'}, {x: 800, y: 415, location: 'street'}], destination: {x: 800, y: 415, location: 'street'}});
  await flush(); assert.equal(h.commits.length, 0); assert.equal(h.nav.active, false);
});

test('a delayed cancelled preview cannot overwrite the most recent destination', async () => {
  const h = harness(), gate = deferred(); let first = true;
  h.setPreview(body => {
    if (first) { first = false; return gate.promise; }
    return Promise.resolve({points: [h.position(), {...body, location: 'street'}], destination: {...body, location: 'street'}});
  });
  h.nav.go({x: 800, y: 415}); h.nav.go({x: 90, y: 415});
  gate.resolve({points: [{x: 100, y: 415, location: 'street'}, {x: 800, y: 415, location: 'street'}], destination: {x: 800, y: 415, location: 'street'}});
  await flush(); assert.equal(h.commits.length, 1); assert.deepEqual(h.commits[0].body, {x: 90, y: 415});
});

test('arrival conversation waits until the final accepted step is visibly complete', async () => {
  const h = harness(); h.nav.go({x: 126, y: 415}, 'Felix'); await flush(); await h.settle(0);
  assert.deepEqual(h.arrivals, []); h.paint(10); assert.deepEqual(h.arrivals, []);
  h.paint(0); assert.deepEqual(h.arrivals, ['Felix']); h.nav.tick(); assert.deepEqual(h.arrivals, ['Felix']);
});

test('room transitions retain the explicit portal location', async () => {
  const h = harness(); h.setPreview(() => Promise.resolve({points: [h.position(), {x: 100, y: 400, location: 'bakery'}, {x: 100, y: 350, location: 'bakery'}], destination: {x: 100, y: 350, location: 'bakery'}}));
  h.nav.go({location: 'bakery'}); await flush();
  assert.deepEqual(h.commits[0].body, {x: 100, y: 400, location: 'bakery'});
  await h.settle(0); h.paint(0); await flush();
  assert.deepEqual(h.commits[1].body, {x: 100, y: 352});
});

test('a projected boundary no-op clears held directions instead of polling forever', async () => {
  const h = harness(); h.setDirection({dx: 1, dy: 0});
  h.setPreview(() => Promise.resolve({points: [h.position()], destination: h.position()}));
  h.nav.nudge(1, 0); await flush(); h.nav.tick(); await flush();
  assert.equal(h.requests.length, 1); assert.equal(h.commits.length, 0); assert.equal(h.nav.active, false);
});

test('route rejection releases the controller and permits a later valid input', async () => {
  const h = harness(); let first = true;
  h.setPreview(body => first ? (first = false, Promise.reject(Error('Outside the floor'))) : Promise.resolve({points: [h.position(), {...body, location: 'street'}], destination: {...body, location: 'street'}}));
  h.nav.go({x: 900, y: 1}); await flush(); assert.deepEqual(h.errors, ['Outside the floor']); assert.equal(h.nav.active, false);
  h.nav.go({x: 126, y: 415}); await flush(); assert.equal(h.commits.length, 1);
});

test('a failed superseded step does not erase a newer destination', async () => {
  const h = harness(); h.nav.go({x: 800, y: 415}); await flush(); h.nav.go({x: 80, y: 415});
  h.commits[0].gate.reject(Error('Old step unavailable')); await flush();
  assert.deepEqual(h.errors, []); assert.equal(h.commits.length, 2); assert.deepEqual(h.commits[1].body, {x: 80, y: 415});
});

test('blocked inputs are acknowledged as rejected and do not queue movement', async () => {
  const h = harness(); h.setBlocked(true); assert.equal(h.nav.go({x: 126, y: 415}), false); assert.equal(h.nav.nudge(1, 0), false);
  h.setBlocked(false); h.nav.tick(); await flush(); assert.equal(h.commits.length, 0); assert.equal(h.nav.active, false);
  assert.equal(h.inputs.length, 2); assert.ok(h.inputs.every(row => row[1] === false));
});
