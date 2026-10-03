const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = {dashboardContent: {innerHTML: 'old'}, refreshDashboard: {}, refreshStatus: {}};
let pending;
const context = vm.createContext({
    document: {getElementById: id => elements[id], addEventListener() {}},
    AbortController, setTimeout, clearTimeout, Date,
    fetch: async () => ({ok: true, text: async () => '<p>Updated</p>'})
});
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname, '../static/js/main.js'), 'utf8'), context);
(async () => {
    await context.autoRefreshDashboard();
    assert.equal(elements.dashboardContent.innerHTML, '<p>Updated</p>');
    assert.match(elements.refreshStatus.textContent, /refreshed at/);
    context.fetch = async () => ({ok: false});
    await context.autoRefreshDashboard();
    assert.equal(elements.dashboardContent.innerHTML, '<p>Updated</p>');
    assert.match(elements.refreshStatus.textContent, /Cannot refresh/);
    assert.equal(elements.refreshDashboard.disabled, false);
    let calls = 0;
    context.fetch = () => { calls++; return new Promise(resolve => {pending = resolve;}); };
    const first = context.autoRefreshDashboard();
    await context.autoRefreshDashboard();
    assert.equal(calls, 1);
    pending({ok: true, text: async () => 'latest'});
    await first;
    assert.equal(elements.dashboardContent.innerHTML, 'latest');
    console.log('PASS: refresh updates, failure preserves readings, overlapping requests prevented');
})().catch(error => {console.error(error); process.exitCode = 1;});
