// Minimal GTM sandbox test runner: runs template.tpl's ___TESTS___ scenarios
// against its ___SANDBOXED_JS_FOR_WEB_TEMPLATE___ code with GTM-style mocks.
// Usage: node test/run-tests.js template.tpl [--trace]
const fs = require('fs');
const assert = require('assert');

const src = fs.readFileSync(process.argv[2], 'utf8');
const trace = process.argv.includes('--trace');
function section(name) {
  const start = src.indexOf('___' + name + '___');
  const rest = src.slice(start + name.length + 6);
  const next = rest.search(/\n___[A-Z_]+___/);
  return next === -1 ? rest : rest.slice(0, next);
}
const code = section('SANDBOXED_JS_FOR_WEB_TEMPLATE');
const tests = section('TESTS');

// scenarios: "- name: X" then "  code: |-" then lines indented 4 spaces.
const scenarios = [];
let cur = null;
for (const line of tests.split('\n')) {
  const m = line.match(/^- name: (.*)$/);
  if (m) { cur = { name: m[1], lines: [] }; scenarios.push(cur); continue; }
  if (!cur || line.match(/^\s+code: \|-$/)) continue;
  if (line.startsWith('    ')) cur.lines.push(line.slice(4));
  else if (line.trim() === '') cur.lines.push('');
}

function defaults(calls) {
  const rec = (n, f) => function () { calls.push([n, Array.from(arguments)]); return f ? f.apply(null, arguments) : undefined; };
  return {
    logToConsole: () => {},
    injectScript: (url, ok) => { if (ok) ok(); },
    encodeUriComponent: encodeURIComponent,
    makeInteger: (v) => { const n = parseInt(v, 10); return isNaN(n) ? undefined : n; },
    JSON: { parse: (s) => { try { return JSON.parse(s); } catch (e) { return undefined; } }, stringify: JSON.stringify },
    getCookieValues: () => [],
    copyFromDataLayer: () => undefined,
    addConsentListener: () => {},
    setDefaultConsentState: () => {},
    updateConsentState: () => {},
  };
}

let failed = 0;
for (const s of scenarios) {
  const mocks = defaults();
  const calls = [];
  const log = [];
  const mock = (name, fn) => { mocks[name] = fn; };
  const wrap = (name) => function () {
    calls.push(name);
    if (trace && (name === 'setDefaultConsentState' || name === 'updateConsentState')) log.push(name + ' ' + JSON.stringify(arguments[0]));
    if (trace && name === 'getCookieValues') log.push('getCookieValues(' + arguments[0] + ') -> ' + JSON.stringify(mocks[name].apply(null, arguments)));
    return mocks[name].apply(null, arguments);
  };
  const runCode = (data) => {
    data = Object.assign({}, data, {
      gtmOnSuccess: () => calls.push('gtmOnSuccess'),
      gtmOnFailure: () => calls.push('gtmOnFailure'),
    });
    const req = (name) => (name === 'JSON' ? mocks.JSON : wrap(name));
    new Function('require', 'data', code)(req, data);
  };
  const assertThat = (actual) => ({
    isEqualTo: (e) => assert.deepStrictEqual(actual, e),
    isUndefined: () => assert.strictEqual(actual, undefined),
    isGreaterThan: (e) => assert.ok(actual > e, actual + ' > ' + e),
  });
  const assertApi = (name) => ({ wasCalled: () => assert.ok(calls.includes(name), name + ' called') });
  try {
    new Function('mock', 'runCode', 'assertThat', 'assertApi', s.lines.join('\n'))(mock, runCode, assertThat, assertApi);
    console.log('PASS ' + s.name);
  } catch (e) {
    failed++;
    console.log('FAIL ' + s.name + ': ' + e.message.split('\n')[0]);
  }
  if (trace) for (const l of log) console.log('    ' + l);
}
console.log(`${scenarios.length - failed}/${scenarios.length} scenarios passed`);
process.exit(failed ? 1 : 0);
