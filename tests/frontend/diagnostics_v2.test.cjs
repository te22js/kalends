'use strict';
// Exercise the shipped diagnostics with independent input, accepted-response and
// changed-draw clocks. These checks validate attribution/accounting, not native
// browser timing, physical paint or controller integration.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../../kalends_rebirth/static/diagnostics.js'), 'utf8');

function harness(search = '?dev=1') {
  let clock = 0;
  const appended = [];
  const elements = new Map();
  const element = selector => {
    if (!elements.has(selector)) elements.set(selector, {textContent: '', onclick: null, focus() {}});
    return elements.get(selector);
  };
  const panel = {innerHTML: '', querySelector: element};
  const window = {};
  const sandbox = {
    window, location: {search}, URLSearchParams,
    document: {
      createElement: () => panel,
      body: {append: value => appended.push(value)},
      querySelector: element,
    },
    performance: {now: () => clock},
    innerWidth: 1280, innerHeight: 720, devicePixelRatio: 1,
    PerformanceObserver: class { static supportedEntryTypes = []; },
  };
  vm.runInNewContext(source, sandbox, {filename: 'diagnostics.js'});
  return {
    d: window.KalendsDiagnostics, appended,
    at: time => { clock = time; },
    reset: () => element('[data-reset-trace]').onclick(),
    report: () => {
      element('[data-freeze-trace]').onclick();
      return JSON.parse(element('pre').textContent);
    },
  };
}

const rows = (report, kind) => report.samples.filter(row => row.kind === kind);
const idle = {from_visual_idle: true};
const moving = {from_visual_idle: false};

test('diagnostics stay absent without the explicit developer query', () => {
  const h = harness('');
  assert.equal(h.d, undefined);
  assert.equal(h.appended.length, 0);
});

test('a committed nonidle intent measures next changed draw but never causal idle latency', () => {
  const h = harness();
  h.at(10); const token = h.d.input('direction', true, '', moving);
  h.at(12); h.d.committed(token);
  h.at(16); h.d.moved();
  const report = h.report();
  assert.equal(report.schema, 'kalends-browser-trace-v2');
  assert.equal(report.input_to_next_changed_actor_draw_ms.n, 1);
  assert.equal(report.input_to_next_changed_actor_draw_ms.p50, 6);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  const input = rows(report, 'input')[0], next = rows(report, 'movement_feedback')[0];
  assert.equal(input.input_id, token);
  assert.equal(input.from_visual_idle, false);
  assert.equal(next.input_id, token);
  assert.equal(next.authority_accepted, true);
  assert.equal(rows(report, 'movement_committed_feedback').length, 0);
});

test('residual draw before a response cannot be counted as committed feedback', () => {
  const h = harness();
  h.at(10); const token = h.d.input('direction', true, '', moving);
  h.at(16); h.d.moved();
  h.at(20); h.d.committed(token);
  const report = h.report();
  assert.equal(report.input_to_next_changed_actor_draw_ms.p50, 6);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  assert.equal(rows(report, 'movement_feedback')[0].authority_accepted, false);
});

test('an idle intent still needs its own accepted authority before causal draw feedback', () => {
  const h = harness();
  h.at(10); const token = h.d.input('direction', true, '', idle);
  h.at(30); h.d.committed(token);
  h.at(43); h.d.moved();
  const report = h.report();
  assert.equal(report.idle_input_to_committed_actor_draw_ms.n, 1);
  assert.equal(report.idle_input_to_committed_actor_draw_ms.p50, 33,
    'latency starts at input, not at the response');
  const feedback = rows(report, 'movement_committed_feedback')[0];
  assert.equal(feedback.input_id, token);
  assert.equal(feedback.authority_accepted, true);
  assert.equal(rows(report, 'input')[0].from_visual_idle, true);
});

test('an idle declaration alone cannot turn an uncommitted draw into causal feedback', () => {
  const h = harness();
  h.at(10); h.d.input('direction', true, '', idle);
  h.at(15); h.d.moved();
  const report = h.report();
  assert.equal(report.input_to_next_changed_actor_draw_ms.p50, 5);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  assert.equal(rows(report, 'movement_feedback')[0].authority_accepted, false);
});

test('a superseded response cannot authorize the latest input', () => {
  const h = harness();
  h.at(10); const oldToken = h.d.input('direction', true, '', idle);
  h.at(12); const latestToken = h.d.input('destination', true, '', idle);
  assert.notEqual(oldToken, latestToken, 'accepted intents need distinct identities');
  h.at(15); h.d.committed(oldToken);
  h.at(19); h.d.moved();
  const report = h.report();
  assert.equal(report.inputs.accepted, 2);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  const feedback = rows(report, 'movement_feedback')[0];
  assert.equal(feedback.input_id, latestToken);
  assert.equal(feedback.authority_accepted, false);
  assert.equal(feedback.duration_ms, 7);
});

test('the latest matching response can authorize feedback after an older response is ignored', () => {
  const h = harness();
  h.at(10); const oldToken = h.d.input('direction', true, '', idle);
  h.at(12); const latestToken = h.d.input('destination', true, '', idle);
  h.at(15); h.d.committed(oldToken);
  h.at(21); h.d.committed(latestToken);
  h.at(31); h.d.moved();
  const report = h.report();
  assert.equal(report.idle_input_to_committed_actor_draw_ms.p50, 19);
  assert.equal(rows(report, 'movement_committed_feedback')[0].input_id, latestToken);
});

test('cancelled pending input cannot be resurrected by its late response or draw', () => {
  const h = harness();
  h.at(10); const token = h.d.input('direction', true, '', idle);
  h.at(12); h.d.cancelInput('focus lost');
  h.at(21); h.d.committed(token);
  h.at(31); h.d.moved();
  const report = h.report();
  assert.equal(report.input_to_next_changed_actor_draw_ms, null);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  assert.equal(report.pending_movement_input, null);
});

test('repeated draw and response hooks do not duplicate an observed intent', () => {
  const h = harness();
  h.at(10); const token = h.d.input('direction', true, '', idle);
  h.at(15); h.d.committed(token);
  h.at(20); h.d.moved();
  h.at(21); h.d.committed(token);
  h.at(30); h.d.moved();
  const report = h.report();
  assert.equal(report.input_to_next_changed_actor_draw_ms.n, 1);
  assert.equal(report.idle_input_to_committed_actor_draw_ms.n, 1);
});

test('trace reset prevents a late old token from authorizing a new input', () => {
  const h = harness();
  h.at(10); const oldToken = h.d.input('direction', true, '', idle);
  h.at(12); h.reset();
  h.at(15); const latestToken = h.d.input('destination', true, '', idle);
  h.at(20); h.d.committed(oldToken);
  h.at(25); h.d.moved();
  const report = h.report();
  assert.notEqual(oldToken, latestToken, 'reset must not reuse an identity a response still carries');
  assert.equal(report.inputs.accepted, 1);
  assert.equal(report.idle_input_to_committed_actor_draw_ms, null);
  assert.equal(rows(report, 'movement_feedback')[0].authority_accepted, false);
});

test('linear quantiles include the conventional even-sample median', () => {
  const h = harness();
  for (const [index, duration] of [1, 3, 5, 7].entries()) {
    const start = 100 * index + 10;
    h.at(start); const token = h.d.input('direction', true, '', idle);
    h.at(start + 0.5); h.d.committed(token);
    h.at(start + duration); h.d.moved();
  }
  const report = h.report();
  assert.equal(report.quantile_method, 'linear interpolation at (n-1)*p');
  for (const name of ['input_to_next_changed_actor_draw_ms', 'idle_input_to_committed_actor_draw_ms']) {
    assert.deepEqual(report[name], {n: 4, p50: 4, p95: 6.7, p99: 6.94, max: 7});
  }
});
