const test = require('node:test');
const assert = require('node:assert/strict');
const source = require('node:fs').readFileSync(require('node:path').join(__dirname, '../../kalends_3d/src/measurements.js'), 'utf8');
const Measurements = new Function(source.replace('export class Measurements', 'class Measurements') + '\nreturn Measurements;')();

test('frozen diagnostics never throw when an accepted movement has no trace token', () => {
  const trace = new Measurements();
  trace.frozen = true;
  const token = trace.input('destination', true, '', {from_visual_idle: true});
  assert.equal(token, undefined);
  assert.doesNotThrow(() => trace.committed(token));
  assert.equal(trace.inputPending, null);
});

test('late acceptance after cancellation is ignored and a matching live input is measured', () => {
  const trace = new Measurements();
  const cancelled = trace.input('direction', true, '', {from_visual_idle: true});
  trace.cancelInput('escape');
  assert.doesNotThrow(() => trace.committed(cancelled));
  const token = trace.input('direction', true, '', {from_visual_idle: true});
  trace.committed(token);
  trace.changedDraw();
  assert.equal(trace.report().idle_input_to_committed_draw_ms.n, 1);
  assert.equal(trace.counts.cancelled, 1);
});
