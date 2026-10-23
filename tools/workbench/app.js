'use strict';
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has('token')) { sessionStorage.setItem('fomt-session', fragment.get('token')); history.replaceState(null, '', location.pathname); }
const token = sessionStorage.getItem('fomt-session') || '';
const state = {offset: 0, total: 0, row: null, valid: false, dirty: false, saving: false, version: 0, listVersion: 0, selectionVersion: 0};
const labels = {translate: 'Cần dịch', qa: 'Chờ QA', blocked: 'Đang chặn', done: 'Hoàn tất'};
const number = value => new Intl.NumberFormat('vi-VN').format(value);
let validationTimer, searchTimer, glossaryTimer, glossaryVersion = 0;

async function api(path, body) {
  const response = await fetch(path, {headers: {Authorization: 'Bearer ' + token, ...(body ? {'Content-Type': 'application/json'} : {})}, ...(body ? {method: 'POST', body: JSON.stringify(body)} : {})});
  const data = await response.json();
  if (!response.ok) { const error = new Error(data.error || 'Không thực hiện được yêu cầu.'); error.status = response.status; error.data = data; throw error; }
  return data;
}
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; }
function clearToast() { $('toast').hidden = true; }
function params() {
  const p = new URLSearchParams();
  for (const id of ['bucket', 'context', 'speaker', 'batch']) if ($(id).value) p.set(id, $(id).value);
  if ($('search').value.trim()) p.set('q', $('search').value.trim());
  if ($('issues').checked) p.set('issues', '1');
  return p;
}
function dirty(value) { state.dirty = value; $('dirty').textContent = value ? 'Chưa lưu' : 'Đã đồng bộ với file'; updateSave(); }
function updateSave() { $('save').disabled = !(state.row?.editable && state.valid && state.dirty && !state.saving); }
function mayLeave() { return !state.dirty || window.confirm('Bản dịch đang sửa chưa được lưu. Bỏ thay đổi để chuyển bản ghi?'); }
function fillSelect(id, values) { for (const value of values) { const option = el('option', typeof value === 'string' ? value : value.label); option.value = typeof value === 'string' ? value : value.value; $(id).append(option); } }

async function loadRows() {
  const request = ++state.listVersion;
  const p = params(); p.set('offset', state.offset); p.set('limit', 50);
  try {
    const data = await api('/api/records?' + p);
    if (request !== state.listVersion) return;
    state.total = data.total; $('rows').replaceChildren();
    for (const row of data.records) {
      const tr = el('tr'); tr.dataset.id = row.id; tr.tabIndex = 0; tr.setAttribute('aria-selected', String(row.id === state.row?.id));
      if (row.id === state.row?.id) tr.classList.add('selected');
      const english = el('td'); english.append(el('span', row.id, 'id-label'), el('span', row.original_english.length > 150 ? row.original_english.slice(0, 150) + '…' : row.original_english));
      const vi = el('td', row.vietnamese_translation ? row.vietnamese_translation.slice(0, 150) : 'Chưa có bản dịch', row.vietnamese_translation ? '' : 'placeholder');
      const status = el('td'); status.append(el('span', labels[row.bucket], 'badge ' + row.bucket));
      tr.append(english, vi, status); tr.addEventListener('click', () => choose(row.id));
      tr.addEventListener('keydown', event => { if (event.key === 'Enter') choose(row.id); });
      $('rows').append(tr);
    }
    $('empty').hidden = data.total !== 0;
    $('results').textContent = data.total ? `${number(state.offset + 1)}–${number(Math.min(state.offset + 50, data.total))} / ${number(data.total)} bản ghi` : '0 bản ghi';
    $('page').textContent = String(Math.floor(state.offset / 50) + 1); $('prev').disabled = !state.offset; $('next').disabled = state.offset + 50 >= data.total;
  } catch (error) { toast(error.message); }
}

function renderMarked(node, text) {
  node.replaceChildren();
  const parts = text.split(/(\{[^}]+\})/);
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    node.append(part.startsWith('{') ? el('span', part, 'token') : document.createTextNode(part));
    if (part === '{LF}' || part === '{PAGE}') node.append(el('br'));
  }
}
function termCard(term) {
  const card = el('div', undefined, 'term-card');
  card.append(el('strong', term.english + ' → '), el('span', term.vietnamese, 'term-vi'));
  card.append(el('p', [term.kind === 'proper_name' ? 'Tên riêng · giữ nguyên' : term.category || 'Thuật ngữ', term.status || '', term.source_id || ''].filter(Boolean).join(' · ')));
  return card;
}
function profileCard(profile) {
  const card = el('div', undefined, 'profile-card'); card.append(el('h3', profile.character));
  card.append(el('p', `Xưng: ${profile.self} · Gọi người chơi: ${profile.player}`), el('p', 'Phạm vi: ' + profile.scope), el('p', 'Nguồn: ' + profile.evidence));
  const details = el('details'); details.append(el('summary', `${profile.source_ids.length} ID trong phạm vi`), el('p', profile.source_ids.join(', '))); card.append(details); return card;
}
function provenance(row) {
  $('provenance').textContent = JSON.stringify({source: row.source, rom_address: row.rom_address, file: row.translation_file,
    context_status: row.context_status, language_review: row.language_review, layout_review: row.layout_review,
    renderer: row.renderer_check, playtest: row.playtest, qa_stale: row.qa_stale}, null, 2);
}
async function choose(id, force = false) {
  if (!force && state.row?.id === id) return;
  if (!mayLeave()) return;
  const selection = ++state.selectionVersion;
  try {
    const row = await api('/api/records/' + encodeURIComponent(id));
    if (selection !== state.selectionVersion) return;
    clearTimeout(validationTimer); state.version++; state.row = row; state.valid = false;
    $('choose').hidden = true; $('editor').hidden = false; $('record-id').textContent = row.id;
    $('record-meta').textContent = [row.context, row.speaker || 'Chưa xác định người nói', row.rom_address || ''].join(' · ');
    $('context-evidence').textContent = row.context_evidence ? 'Ngữ cảnh: ' + row.context_evidence : 'Nguồn: ' + row.source_reference;
    $('scoped-profile').textContent = row.profiles.length ? row.profiles.map(p => `${p.character}: ${p.self}/${p.player} · ${p.scope}`).join('\n') : 'Chưa có hồ sơ xưng hô riêng áp dụng cho ID này.';
    renderMarked($('english'), row.original_english);
    $('vietnamese').value = row.vietnamese_translation; $('vietnamese').disabled = !row.editable;
    $('save-status').textContent = ''; dirty(false); $('token-buttons').replaceChildren();
    for (const text of [...new Set(row.control_codes)]) {
      const button = el('button', '+ ' + text); button.disabled = !row.editable;
      button.addEventListener('click', () => { const input = $('vietnamese'); input.setRangeText(text, input.selectionStart, input.selectionEnd, 'end'); input.focus(); edited(); });
      $('token-buttons').append(button);
    }
    provenance(row);
    for (const tr of $('rows').children) { const selected = tr.dataset.id === id; tr.classList.toggle('selected', selected); tr.setAttribute('aria-selected', String(selected)); }
    await validate();
  } catch (error) { toast(error.message); }
}
function showValidation(data) {
  state.valid = data.valid; $('validation').replaceChildren();
  const notice = el('div', undefined, 'notice ' + (data.valid ? 'good' : 'error'));
  if (data.valid) notice.textContent = 'Token, bảng mã và giới hạn độ dài hợp lệ.';
  else { const list = el('ul'); for (const error of data.errors) list.append(el('li', error.message)); notice.append(list); }
  $('validation').append(notice);
  if (data.warnings.length) $('validation').append(el('div', data.warnings.join(' · '), 'notice warning'));
  const m = data.metrics; $('metrics').replaceChildren(el('span', `Dòng dài nhất: ${m.maximum_tiles ?? '—'} / ${m.max_columns} ô`), el('span', `Mã hóa: ${m.encoded_bytes ?? '—'} byte${m.max_encoded_bytes === null ? '' : ' / ' + m.max_encoded_bytes}`));
  if (m.dynamic_variable_reserve) $('metrics').append(el('span', 'Đã dự phòng biến động'));
  $('expected-tokens').textContent = data.expected_tokens.join(' ') || '(không có)'; $('actual-tokens').textContent = data.actual_tokens.join(' ') || '(không có)';
  $('suggestions').replaceChildren(...data.suggestions.map(termCard));
  if (!data.suggestions.length) $('suggestions').append(el('p', 'Chưa có thuật ngữ khớp trong glossary.', 'muted'));
  updateSave();
}
async function validate() {
  if (!state.row) return;
  const version = ++state.version, id = state.row.id, text = $('vietnamese').value;
  state.valid = false; updateSave();
  try { const result = await api('/api/validate', {id, text}); if (version === state.version && state.row?.id === id) showValidation(result); }
  catch (error) { if (version === state.version) toast(error.message); }
}
function edited() {
  clearToast(); state.version++; state.valid = false; dirty($('vietnamese').value !== state.row.vietnamese_translation); $('save-status').textContent = '';
  clearTimeout(validationTimer); validationTimer = setTimeout(validate, 220);
}
async function save() {
  if ($('save').disabled) return;
  const row = state.row, text = $('vietnamese').value;
  state.saving = true; updateSave(); $('save-status').textContent = 'Đang lưu…';
  try {
    const result = await api('/api/save', {id: row.id, text, revision: row.revision});
    // Do not erase keystrokes made while a request was in flight.
    if (state.row?.id === row.id) {
      state.row = result.record;
      provenance(result.record);
      if ($('vietnamese').value === text) $('vietnamese').value = result.record.vietnamese_translation;
      dirty($('vietnamese').value !== result.record.vietnamese_translation);
      $('save-status').textContent = result.changed ? 'Đã lưu nháp và sao lưu bản trước. QA cũ được kiểm lại theo hash.' : 'Bản ghi chưa thay đổi.';
      await validate();
    }
    await refreshMeta(false); await loadRows();
  } catch (error) {
    $('save-status').textContent = error.message;
    if (error.data?.validation) showValidation(error.data.validation);
    if (error.status === 409) { state.valid = false; updateSave(); }
    else updateSave();
  } finally { state.saving = false; updateSave(); }
}
async function glossary() {
  const version = ++glossaryVersion;
  try { const data = await api('/api/glossary?q=' + encodeURIComponent($('glossary-search').value)); if (version !== glossaryVersion) return; $('glossary-count').textContent = `${number(data.total)} kết quả${data.total > 100 ? ' · hiển thị 100, hãy thu hẹp tìm kiếm' : ''}`; $('glossary-results').replaceChildren(...data.terms.map(termCard)); }
  catch (error) { toast(error.message); }
}
async function refreshMeta(initial = true) {
  const data = await api('/api/meta'); $('total').textContent = number(data.total); $('drafts').textContent = number(data.drafts); $('to-translate').textContent = number(data.summary.translate); $('blocked').textContent = number(data.summary.blocked);
  if (initial) {
    fillSelect('context', data.contexts); fillSelect('speaker', data.speakers); fillSelect('batch', data.batches.map(b => ({value: b.id, label: b.id + ' (' + b.count + ')'})));
    $('profile-list').replaceChildren(...data.profiles.map(profileCard)); $('glossary-rules').replaceChildren(...data.glossary_rules.map(rule => el('li', rule)));
    $('connection').textContent = 'Dữ liệu cục bộ';
  }
}
for (const id of ['bucket', 'context', 'speaker', 'batch', 'issues']) $(id).addEventListener('change', () => { state.offset = 0; loadRows(); });
$('search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => {state.offset = 0; loadRows();}, 220); });
$('prev').addEventListener('click', () => {state.offset = Math.max(0, state.offset - 50); loadRows();});
$('next').addEventListener('click', () => {state.offset += 50; loadRows();});
$('vietnamese').addEventListener('input', edited); $('save').addEventListener('click', save);
$('reload').addEventListener('click', () => { if (state.row) choose(state.row.id, true); });
$('glossary-search').addEventListener('input', () => { clearTimeout(glossaryTimer); glossaryTimer = setTimeout(glossary, 200); });
for (const button of document.querySelectorAll('[data-tab]')) button.addEventListener('click', () => {
  for (const tab of document.querySelectorAll('[data-tab]')) { const selected = tab === button; tab.classList.toggle('active', selected); tab.setAttribute('aria-selected', String(selected)); $(tab.dataset.tab + '-tab').hidden = !selected; }
  if (button.dataset.tab === 'glossary') glossary();
});
$('export').addEventListener('click', async () => {
  try { const response = await fetch('/api/export.csv?' + params(), {headers:{Authorization:'Bearer ' + token}}); if (!response.ok) throw new Error('Không xuất được CSV.'); const url = URL.createObjectURL(await response.blob()); const a = el('a'); a.href = url; a.download = 'fomt-translations.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); } catch (error) {toast(error.message);}
});
window.addEventListener('beforeunload', event => {if (state.dirty) {event.preventDefault(); event.returnValue = '';}});
window.addEventListener('keydown', event => {if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {event.preventDefault(); save();}});
(async () => {try {await refreshMeta(); await loadRows();} catch (error) {$('connection').textContent = 'Chưa kết nối'; toast(error.message);}})();
