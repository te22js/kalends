'use strict';
// Execute the real iframe compatibility adapter. Fake fetch only records its
// request boundary; these checks cannot mutate a real world or open a socket.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '../../kalends/experience_os/static/game-host.js'), 'utf8');
const copy = value => JSON.parse(JSON.stringify(value));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
};

function harness({href = 'http://127.0.0.1:8800/immersion/?experience=custom_life', top = false, fetchImpl} = {}) {
  const location = {href, origin: new URL(href).origin};
  const requests = [], messages = [];
  const response = Object.freeze({ok: true, status: 200, json() { throw Error('Adapter must not consume the bridge response'); }});
  const window = {location};
  const parent = {postMessage(payload, origin) {
    assert.equal(this, parent, 'postMessage must retain the parent receiver');
    messages.push({payload: copy(payload), origin});
  }};
  window.parent = top ? window : parent;
  window.postMessage = (payload, origin) => messages.push({payload: copy(payload), origin, top: true});
  window.fetch = function(input, options) {
    assert.equal(this, window, 'native browser fetch must be bound to its window');
    requests.push({input, options});
    return fetchImpl ? fetchImpl(input, options) : Promise.resolve(response);
  };
  vm.runInNewContext(source, {window, location, URL}, {filename: 'game-host.js'});
  return {window, location, requests, messages, response};
}

test('a custom compiled iframe routes character context to its own life and preserves recipient/query/options', async () => {
  const h = harness();
  const options = Object.freeze({cache: 'no-store', credentials: 'same-origin'});
  const response = await h.window.fetch('/api/context?recipient=Felix&topic=history', options);
  const routed = new URL(h.requests[0].input, h.location.origin);
  assert.equal(routed.pathname, '/api/context');
  assert.equal(routed.searchParams.get('experience'), 'custom_life');
  assert.equal(routed.searchParams.get('recipient'), 'Felix');
  assert.equal(routed.searchParams.get('topic'), 'history');
  assert.equal(h.requests[0].options, options, 'the bridge retains ownership of request options');
  assert.equal(response, h.response, 'the untouched response belongs to the shipped 3D bridge');
  assert.deepEqual(h.messages, []);
});

test('an existing wrong-life query is replaced once without losing encoded parameter values', async () => {
  const h = harness({href: 'http://localhost:8800/immersion/?experience=author_retry_2'});
  await h.window.fetch('/api/context?recipient=Felix%20%26%20Sabina&experience=pompeii_life&experience=another_life');
  const routed = new URL(h.requests[0].input, h.location.origin);
  assert.deepEqual(routed.searchParams.getAll('experience'), ['author_retry_2']);
  assert.equal(routed.searchParams.get('recipient'), 'Felix & Sabina');
});

test('an iframe without an explicit life retains the established Pompeii default', async () => {
  const h = harness({href: 'http://127.0.0.1:8800/immersion/'});
  await h.window.fetch('/api/state');
  assert.equal(new URL(h.requests[0].input, h.location.origin).searchParams.get('experience'), 'pompeii_life');
});

test('successful API POST preserves the exact confirmation body and sends a life-bound same-origin refresh', async () => {
  const h = harness({href: 'http://localhost:8800/immersion/?experience=participant_branch'});
  const body = JSON.stringify({proposal_id: 'review-9', interpretation_id: '0'});
  const options = Object.freeze({method: 'POST', credentials: 'same-origin',
    headers: Object.freeze({'Content-Type': 'application/json'}), body});
  const response = await h.window.fetch('/api/act', options);
  assert.equal(h.requests.length, 1, 'the adapter must not resubmit an economic command');
  assert.equal(h.requests[0].options, options);
  assert.equal(h.requests[0].options.body, body);
  assert.deepEqual(JSON.parse(h.requests[0].options.body), {proposal_id: 'review-9', interpretation_id: '0'});
  assert.equal(new URL(h.requests[0].input, h.location.origin).searchParams.get('experience'), 'participant_branch');
  assert.equal(response, h.response);
  assert.deepEqual(h.messages, [{payload: {kind: 'kalends:accepted', operation:'action', experience: 'participant_branch'}, origin: 'http://localhost:8800'}]);
});

test('the parent receives no early acceptance signal while the native POST is still unresolved', async () => {
  const gate = deferred();
  const h = harness({fetchImpl: () => gate.promise});
  const pending = h.window.fetch('/api/move', {method: 'POST', body: '{"x":810,"y":275.5}'});
  assert.equal(h.requests.length, 1);
  assert.deepEqual(h.messages, []);
  const response = {ok: true, status: 200};
  gate.resolve(response);
  assert.equal(await pending, response);
  assert.equal(h.messages.length, 1);
});

test('failed API POST returns its response without announcing acceptance', async () => {
  const rejected = Object.freeze({ok: false, status: 400});
  const h = harness({fetchImpl: async () => rejected});
  assert.equal(await h.window.fetch('/api/act', {method: 'POST', body: '{}'}), rejected);
  assert.equal(h.requests.length, 1);
  assert.deepEqual(h.messages, [{payload:{kind:'kalends:rejected',reason:'rejected',experience:'custom_life'},origin:'http://127.0.0.1:8800'}]);
});

test('route previews, proposed choices and mode reads are not accepted world actions', async () => {
  const h = harness();
  for (const path of ['/api/route', '/api/propose', '/api/mode']) {
    await h.window.fetch(path, {method: 'POST', body: '{}'});
  }
  assert.equal(h.requests.length, 3);
  assert.deepEqual(h.messages, [], 'only accepted act/move/advance responses may count as meaningful actions');
});

test('network rejection propagates unchanged and cannot trigger a parent refresh', async () => {
  const error = new TypeError('Fixture connection rejected');
  const h = harness({fetchImpl: async () => { throw error; }});
  await assert.rejects(h.window.fetch('/api/advance', {method: 'POST', body: '{"minutes":30}'}), received => received === error);
  assert.equal(h.requests.length, 1);
  assert.deepEqual(h.messages, [{payload:{kind:'kalends:rejected',reason:'network',experience:'custom_life'},origin:'http://127.0.0.1:8800'}]);
});

test('successful reads and non-POST requests do not announce accepted actions', async () => {
  const h = harness();
  for (const options of [undefined, null, {method: 'GET'}, {method: 'HEAD'}, {method: 'PUT'}]) {
    await h.window.fetch('/api/state', options);
  }
  assert.equal(h.requests.length, 5);
  assert.ok(h.requests.every(request => new URL(request.input, h.location.origin).searchParams.get('experience') === 'custom_life'));
  assert.deepEqual(h.messages, []);
});

test('models, portraits, navigation, console API and unrelated URLs bypass the game adapter intact', async () => {
  const h = harness();
  const inputs = ['/immersion-assets/characters/characters.json', '/immersion-assets/environment/pompeii_district.glb',
    '/assets/portraits.png', '/navigation.js', '/os/state?experience=another_life', '/apiary/image.png',
    'https://example.invalid/api/state'];
  const options = Object.freeze({method: 'POST', body: 'fixture-only; not a real asset upload'});
  for (const input of inputs) await h.window.fetch(input, options);
  assert.deepEqual(h.requests.map(request => request.input), inputs);
  assert.ok(h.requests.every(request => request.options === options));
  assert.deepEqual(h.messages, [], 'only root-relative /api/ calls belong to the shipped bridge adapter');
});

test('non-string fetch inputs pass through unchanged rather than being converted into game commands', async () => {
  const h = harness();
  const input = new URL('http://127.0.0.1:8800/immersion-assets/characters/characters.json');
  const requestLike = Object.freeze({url: '/api/state', method: 'GET'});
  await h.window.fetch(input);
  await h.window.fetch(requestLike);
  assert.equal(h.requests[0].input, input);
  assert.equal(h.requests[1].input, requestLike);
  assert.deepEqual(h.messages, []);
});

test('two custom iframes retain independent routing with no global active-world state', async () => {
  const a = harness({href: 'http://127.0.0.1:8800/immersion/?experience=life_a'});
  const b = harness({href: 'http://127.0.0.1:8800/immersion/?experience=life_b'});
  await Promise.all([a.window.fetch('/api/move', {method: 'POST', body: '{"x":700,"y":415}'}),
                    b.window.fetch('/api/move', {method: 'POST', body: '{"x":900,"y":415}'})]);
  await a.window.fetch('/api/context?recipient=Marcus');
  assert.ok(a.requests.every(request => new URL(request.input, a.location.origin).searchParams.get('experience') === 'life_a'));
  assert.ok(b.requests.every(request => new URL(request.input, b.location.origin).searchParams.get('experience') === 'life_b'));
  assert.equal(a.messages[0].payload.experience, 'life_a');
  assert.equal(b.messages[0].payload.experience, 'life_b');
});

test('top-level gameplay routes correctly but never posts a notification to itself', async () => {
  const h = harness({top: true});
  await h.window.fetch('/api/move', {method: 'POST', body: '{"location":"street"}'});
  assert.equal(new URL(h.requests[0].input, h.location.origin).searchParams.get('experience'), 'custom_life');
  assert.deepEqual(h.messages, []);
});

test('typed scene acceptance reads only a clone and forwards its exact accepted revision',async()=>{
  let cloneReads=0;const response={ok:true,status:200,json(){throw Error('original response consumed');},clone(){return {json:async()=>{cloneReads++;return {accepted_revision:7,receipt:{text:'PRIVATE RECEIPT'}};}};}};
  const h=harness({fetchImpl:async()=>response});assert.equal(await h.window.fetch('/api/act',{method:'POST',body:'{}'}),response);
  assert.equal(cloneReads,1);assert.deepEqual(h.messages,[{payload:{kind:'kalends:accepted',operation:'action',accepted_revision:7,experience:'custom_life'},origin:'http://127.0.0.1:8800'}]);
  assert.doesNotMatch(JSON.stringify(h.messages),/PRIVATE RECEIPT/);
});

test('navigation and advances never forward a meaningful revision even if a response contains one',async()=>{
  const response={ok:true,status:200,clone(){throw Error('must not inspect movement content');}};
  const h=harness({fetchImpl:async()=>response});await h.window.fetch('/api/move',{method:'POST',body:'{}'});await h.window.fetch('/api/advance',{method:'POST',body:'{}'});
  assert.deepEqual(h.messages.map(m=>m.payload.operation),['move','advance']);assert.ok(h.messages.every(m=>!('accepted_revision' in m.payload)));
});

test('missing revision on a reviewed wait preserves refresh but cannot claim meaningful acceptance',async()=>{
  const response={ok:true,status:200,clone(){return {json:async()=>({receipt:{action:'wait'},accepted_revision:null})};}};
  const h=harness({fetchImpl:async()=>response});await h.window.fetch('/api/act',{method:'POST',body:'{}'});assert.equal(h.messages[0].payload.operation,'action');assert.equal('accepted_revision' in h.messages[0].payload,false);
});

test('journal rejection forwards only a fixed save failure category',async()=>{
  const response={ok:false,status:400,clone(){return {json:async()=>({save_failed:true,error:'PRIVATE FILE PATH'})};}};
  const h=harness({fetchImpl:async()=>response});assert.equal(await h.window.fetch('/api/act',{method:'POST',body:'{}'}),response);
  assert.equal(h.messages[0].payload.reason,'save_failed');assert.doesNotMatch(JSON.stringify(h.messages),/PRIVATE FILE PATH/);
});
