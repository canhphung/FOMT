#!/usr/bin/env node
// Optional Chromium/CDP replay. Writes only a disposable data copy and build/.
// Requires Node 22+ (built-in WebSocket), Chromium, and Python; no npm packages.
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const out = path.join(root, 'build/workbench-browser');
const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'fomt-editor-'));
const copy = path.join(temporary, 'project');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const hash = data => createHash('sha256').update(data).digest('hex');
let server, browser, socket, allowedDialog = false, sequence = 0;
const pending = new Map(), exceptions = [], checks = [], images = [];
let browserLog = '', serverLog = '';

async function hashes(directory) {
  const result = {};
  async function walk(dir) {
    for (const item of await fs.readdir(dir, {withFileTypes:true})) {
      const file = path.join(dir, item.name);
      if (item.isDirectory()) await walk(file);
      else if (item.name.endsWith('.json')) result[path.relative(directory, file)] = hash(await fs.readFile(file));
    }
  }
  await walk(directory); return result;
}
async function waitFor(check, label, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { try { const result = await check(); if (result) return result; } catch {} await sleep(75); }
  throw new Error('Timed out: ' + label);
}
function cdp(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => {pending.delete(id); reject(new Error('CDP timeout: ' + method));}, 20000);
    pending.set(id, {resolve, reject, timeout}); socket.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const result = await cdp('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text + ': ' + JSON.stringify(result.exceptionDetails.exception));
  return result.result.value;
}
const visible = expression => waitFor(() => evaluate(expression), expression);
async function input(id, value) {await evaluate(`document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(value)};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event('input',{bubbles:true}));`);}
async function screenshot(name) {
  const {data} = await cdp('Page.captureScreenshot', {format:'png', captureBeyondViewport:false});
  const content = Buffer.from(data, 'base64'); await fs.writeFile(path.join(out, name), content);
  images.push({path:'build/workbench-browser/' + name, sha256:hash(content)});
}
async function selectRecord(id, bucket) {
  await evaluate(`document.getElementById('bucket').value=${JSON.stringify(bucket)};document.getElementById('bucket').dispatchEvent(new Event('change'));`);
  await input('search', id);
  await visible(`document.querySelectorAll('#rows tr').length===1&&!!document.querySelector('tr[data-id="${id}"]')`);
  await evaluate(`document.querySelector('tr[data-id="${id}"]').click()`);
  await visible(`document.getElementById('record-id').textContent===${JSON.stringify(id)}`);
  await visible(`document.getElementById('validation').textContent.length>0`);
}

try {
  await fs.mkdir(out, {recursive:true});
  // Replace an old green report before doing any work.
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({status:'running'}));
  const before = await hashes(path.join(root, 'localization'));
  await fs.cp(path.join(root, 'localization'), path.join(copy, 'localization'), {recursive:true});
  server = spawn(process.env.FOMT_PYTHON || path.join(root, '.venv/bin/python'),
    [path.join(root, 'tools/translation_workbench.py'), '--project-root', copy, '--port', '0'], {cwd:root});
  server.stdout.on('data', data => {serverLog += data;}); server.stderr.on('data', data => {serverLog += data;});
  const session = await waitFor(() => serverLog.match(/http:\/\/127\.0\.0\.1:\d+\/#token=[\w-]+/)?.[0], 'local editor startup');
  browser = spawn(process.env.CHROMIUM || 'chromium', ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
    '--disable-background-networking', '--disable-component-update', '--disable-sync', '--disable-extensions',
    '--no-first-run', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
    '--user-data-dir=' + path.join(temporary, 'chromium'), 'about:blank']);
  browser.stderr.on('data', data => {browserLog += data;});
  const port = await waitFor(async () => (await fs.readFile(path.join(temporary, 'chromium/DevToolsActivePort'), 'utf8')).split('\n')[0], 'Chromium startup');
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {socket.addEventListener('open', resolve, {once:true}); socket.addEventListener('error', reject, {once:true});});
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const request = pending.get(message.id); pending.delete(message.id); clearTimeout(request.timeout);
      if (message.error) request.reject(new Error(JSON.stringify(message.error))); else request.resolve(message.result);
    } else if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
    else if (message.method === 'Page.javascriptDialogOpening') {
      if (!allowedDialog) exceptions.push({unexpectedDialog:message.params.message});
      cdp('Page.handleJavaScriptDialog', {accept:true}).catch(() => {});
    }
  });
  await cdp('Runtime.enable'); await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride', {width:1440, height:1100, deviceScaleFactor:1, mobile:false});
  await cdp('Page.navigate', {url:session});
  await visible(`document.getElementById('connection').textContent==='Dữ liệu cục bộ'&&document.querySelectorAll('#rows tr').length>0`);
  checks.push('Real catalog loaded and table paginated in Chromium.');
  const identifier = 'item.tool.000.description';
  await selectRecord(identifier, 'qa');
  const original = await evaluate(`document.getElementById('vietnamese').value`);
  await visible(`document.getElementById('validation').textContent.includes('hợp lệ')`);
  await screenshot('workbench.png');
  await input('vietnamese', original.replace('{CR}', ''));
  await visible(`document.getElementById('validation').textContent.includes('Thiếu, thừa')&&document.getElementById('save').disabled`);
  await screenshot('token-error.png'); checks.push('Removing a CR token reports an error and blocks Save.');
  await input('vietnamese', 'x'.repeat(90) + original);
  await visible(`document.getElementById('validation').textContent.includes('Dòng dài nhất')&&document.getElementById('save').disabled`);
  checks.push('Width overflow is reported with Save blocked.');
  await input('vietnamese', original + '😀');
  await visible(`document.getElementById('validation').textContent.includes('unsupported character')`);
  checks.push('Unsupported glyph is rejected by the real encoder.');
  const changed = original.replace('Liềm', 'Liềm ');
  if (changed === original) throw new Error('Expected the verified sickle description in the catalog.');
  await input('vietnamese', changed); await visible(`!document.getElementById('save').disabled`);
  await evaluate(`document.getElementById('save').click()`);
  await visible(`document.getElementById('save-status').textContent.startsWith('Đã lưu nháp')&&document.getElementById('dirty').textContent==='Đã đồng bộ với file'`);
  const owner = path.join(copy, 'localization/vi/item_descriptions_tools.json');
  const saved = JSON.parse(await fs.readFile(owner, 'utf8'));
  if (saved.records.find(row => row.id === identifier).vietnamese_translation !== changed) throw new Error('Save did not reach the expected JSON file.');
  if (!(await fs.readdir(path.join(copy, 'local-data/workbench/backups'))).length) throw new Error('Missing backup.');
  if (!(await evaluate(`document.getElementById('provenance').textContent.includes('"qa_stale": true')`))) throw new Error('QA stale status not refreshed.');
  checks.push('Save writes the original owner file, creates a backup, and displays stale QA.');
  saved.records.find(row => row.id === identifier).vietnamese_translation = original.replace('Liềm', 'Liềm  ');
  await fs.writeFile(owner, JSON.stringify(saved));
  const unsaved = original.replace('Liềm', 'Liềm   ');
  await input('vietnamese', unsaved); await visible(`!document.getElementById('save').disabled`);
  await evaluate(`document.getElementById('save').click()`);
  await visible(`document.getElementById('save-status').textContent.includes('đã đổi ở nơi khác')`);
  if (await evaluate(`document.getElementById('vietnamese').value`) !== unsaved) throw new Error('Conflict erased the unsaved text.');
  checks.push('An external edit causes HTTP 409; the textarea keeps the unsaved draft.');
  allowedDialog = true;
  await evaluate(`document.getElementById('reload').click()`);
  await visible(`document.getElementById('dirty').textContent==='Đã đồng bộ với file'`);
  allowedDialog = false;
  await evaluate(`document.querySelector('[data-tab="glossary"]').click()`);
  await input('glossary-search', 'liem');
  await visible(`document.getElementById('glossary-results').textContent.includes('Sickle')`);
  checks.push('Accent-insensitive glossary lookup finds Sickle → Liềm.');
  await evaluate(`document.querySelector('[data-tab="profiles"]').click()`);
  await visible(`document.getElementById('profile-list').textContent.includes('Thomas')&&document.getElementById('profile-list').textContent.includes('bác')`);
  checks.push('Speaker profiles expose scene scope and exact source IDs.');
  await evaluate(`document.querySelector('[data-tab="editor"]').click()`);
  await selectRecord('item.food.066.name', 'blocked');
  await visible(`document.getElementById('vietnamese').disabled&&document.getElementById('save').disabled`);
  checks.push('The unresolved Flower record remains read-only.');
  await cdp('Browser.setDownloadBehavior', {behavior:'allow', downloadPath:path.join(out, 'downloads')});
  await evaluate(`document.getElementById('export').click()`);
  const csv = await waitFor(async () => {const file = path.join(out, 'downloads/fomt-translations.csv');const data = await fs.readFile(file);return data.includes(Buffer.from('item.food.066.name')) && data;}, 'filtered CSV download');
  if (!csv.subarray(0, 3).equals(Buffer.from([239,187,191]))) throw new Error('CSV has no UTF-8 BOM.');
  checks.push('CSV export follows active filters and preserves UTF-8.');
  await cdp('Emulation.setDeviceMetricsOverride', {width:390, height:844, deviceScaleFactor:1, mobile:false});
  if (await evaluate(`document.documentElement.scrollWidth>innerWidth`)) throw new Error('Mobile layout overflows horizontally.');
  checks.push('390 px viewport has no horizontal document overflow.');
  const after = await hashes(path.join(root, 'localization'));
  if (JSON.stringify(before) !== JSON.stringify(after)) throw new Error('Original localization data changed during the browser test.');
  if (exceptions.length) throw new Error('Browser exceptions: ' + JSON.stringify(exceptions));
  const report = {status:'passed', timestamp:new Date().toISOString(), checks, screenshots:images,
    browser: await cdp('Browser.getVersion'), source_json_files_unchanged:Object.keys(before).length,
    source_snapshot_sha256:hash(JSON.stringify(before)),
    scope:'Chromium UI and HTTP writes in a disposable copy of the actual extracted catalog; original translations unchanged.',
    limitations:['No emulator or ROM build invoked by this browser test.', 'Glossary and speaker profiles are lookup-only; review approvals are not edited.']};
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({status:report.status, checks:checks.length, screenshots:images.length, source_json_files_unchanged:report.source_json_files_unchanged}));
} catch (error) {
  await fs.mkdir(out, {recursive:true});
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({status:'failed', error:String(error), checks, exceptions}, null, 2));
  console.error(String(error)); process.exitCode = 1;
} finally {
  if (socket) socket.close();
  for (const item of pending.values()) {clearTimeout(item.timeout); item.reject(new Error('Browser test finished.'));}
  browser?.kill(); server?.kill();
  // Chromium may still be shutting down; retry removing its temporary profile.
  await sleep(300); await fs.rm(temporary, {recursive:true, force:true, maxRetries:5, retryDelay:100});
}
