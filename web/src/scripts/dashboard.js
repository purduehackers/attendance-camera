const $ = id => document.getElementById(id);
let state, initialized = false, previewOn = true, previewURL, previewController;
const percentages = ['x_min','y_min','x_max','y_max','position','deadband'];
const errors = new Map();
function error(source, message = '') {
  if (message) errors.set(source, message); else errors.delete(source);
  $('error').textContent = [...new Set(errors.values())].join(' ');
  $('error').hidden = errors.size === 0;
}
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, headers: body ? {'Content-Type':'application/json'} : {}, body: body ? JSON.stringify(body) : undefined});
  if (response.status === 401) { location.assign('/login'); throw new Error('Your session has expired. Sign in again.'); }
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    const detail = result.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(x => x.msg).join('; ') : `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}
async function refresh() {
  try {
    state = await api('/api/status');
    error('status');
    $('connection').textContent = state.mode === 'demo' ? 'Synthetic demo' : state.fresh ? 'Camera connected' : state.detail || 'Camera unavailable';
    const session = state.session;
    $('occupancy').textContent = session ? session.occupancy : '—';
    $('incoming').textContent = session ? session.incoming : '—';
    $('outgoing').textContent = session ? session.outgoing : '—';
    $('session-state').textContent = session ? `Started ${new Date(session.started_at*1000).toLocaleString()}` : 'No active session';
    $('start').disabled = !!session || !state.fresh || !state.calibrated;
    $('end').disabled = $('reconcile').disabled = !session;
    const notices = [];
    if (state.mode === 'demo') notices.push('Demo data only — no camera is connected.');
    if (!state.calibrated) notices.push('Save the counting boundary before starting a session.');
    if (session && (!state.fresh || session.needs_reconciliation)) notices.push('Occupancy needs checking. Take a headcount and use Correct occupancy.');
    $('notice').textContent = notices.join(' '); $('notice').hidden = !notices.length;
    if (!initialized) {
      percentages.forEach(key => { $(key).value = state.calibration[key]*100; });
      $('axis').value = state.calibration.axis; $('inside').value = state.calibration.inside;
      initialized = true; $('calibration-fields').disabled = false;
    }
  } catch (err) { $('connection').textContent = 'Server unavailable'; $('start').disabled = true; error('status', err.message); }
}
async function sessions() {
  const rows = await api('/api/sessions'); $('sessions').replaceChildren();
  error('history');
  $('no-sessions').hidden = rows.length > 0;
  for (const row of rows) {
    const tr = document.createElement('tr');
    for (const text of [new Date(row.started_at*1000).toLocaleString(), row.ended_at ? 'Ended' : 'Active', row.incoming, row.outgoing]) {
      const td = document.createElement('td'); td.textContent = text; tr.append(td);
    }
    const td = document.createElement('td'), a = document.createElement('a');
    a.href = `/api/sessions/${encodeURIComponent(row.id)}/counts.csv`; a.textContent = 'Download CSV'; td.append(a); tr.append(td); $('sessions').append(tr);
  }
}
async function change(path, method, body) {
  error('action');
  try { await api(path, method, body); } catch (err) { error('action', err.message); return; }
  await refresh();
  await sessions().catch(err => error('history', err.message));
}
$('session-form').addEventListener('submit', event => { event.preventDefault(); change('/api/sessions','POST',{occupancy:Number($('headcount').value)}); });
$('reconcile').addEventListener('click', () => {
  const value = Number($('headcount').value);
  if (confirm(`Set estimated occupancy to the observed headcount of ${value}?`)) change('/api/session/reconcile','POST',{occupancy:value});
});
$('end').addEventListener('click', () => { if (confirm('End this attendance session? Its counts will be kept.')) change('/api/session/end','POST'); });
$('calibration-form').addEventListener('submit', event => {
  event.preventDefault();
  const value = {...state.calibration, axis:$('axis').value, inside:$('inside').value};
  percentages.forEach(key => { value[key] = Number($(key).value)/100; });
  change('/api/calibration','PUT',value);
});
$('preview-toggle').addEventListener('click', () => {
  previewOn = !previewOn; $('preview-wrap').hidden = !previewOn;
  $('preview-toggle').setAttribute('aria-expanded', String(previewOn));
  $('preview-toggle').textContent = previewOn ? 'Hide live preview' : 'Show live preview';
  if (!previewOn) { previewController?.abort(); clearPreview(); }
  else { previewMessage('Connecting to camera…'); void preview(); }
});
function clearPreview() {
  $('preview').removeAttribute('src'); $('preview').hidden = true;
  if (previewURL) URL.revokeObjectURL(previewURL);
  previewURL = undefined;
  $('preview-placeholder').hidden = false;
}
function previewMessage(message) {
  $('preview-status').textContent = message;
  $('preview-placeholder').textContent = message;
}
async function preview() {
  if (!previewOn || previewController || document.hidden) return;
  const controller = new AbortController();
  previewController = controller;
  const timeout = setTimeout(() => controller.abort(), 12000);
  let next;
  try {
    const response = await fetch('/api/preview.jpg', {signal: controller.signal, cache: 'no-store'});
    if (response.status === 401) { location.assign('/login'); throw new Error('Your session has expired. Sign in again.'); }
    if (!response.ok) throw new Error(`Camera preview unavailable (${response.status}). Reconnecting…`);
    if (!response.headers.get('Content-Type')?.startsWith('image/jpeg')) throw new Error('Camera returned an invalid image. Reconnecting…');
    next = URL.createObjectURL(await response.blob());
    const frame = new Image(); frame.src = next;
    await frame.decode().catch(() => { throw new Error('Camera returned an invalid image. Reconnecting…'); });
    if (controller.signal.aborted) throw controller.signal.reason;
    if (!previewOn || document.hidden) return;
    $('preview').src = next; $('preview').hidden = false;
    $('preview-placeholder').hidden = true;
    if (previewURL) URL.revokeObjectURL(previewURL);
    previewURL = next; next = undefined;
    previewMessage('Live camera preview');
  } catch (err) {
    clearPreview();
    if (previewOn && !document.hidden) previewMessage(err.name === 'AbortError' ? 'Camera preview timed out. Reconnecting…' : err.name === 'TypeError' ? 'Camera preview connection lost. Reconnecting…' : err.message);
  } finally {
    if (next) URL.revokeObjectURL(next);
    clearTimeout(timeout); previewController = undefined;
  }
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { previewController?.abort(); clearPreview(); }
  else if (previewOn) { previewMessage('Connecting to camera…'); void preview(); }
});
(async function poll() { if (!document.hidden) await refresh(); setTimeout(poll,1000); })();
(async function frames() { await preview(); setTimeout(frames,1000); })();
(async function history() { if (!document.hidden) await sessions().catch(err => error('history', err.message)); setTimeout(history,10000); })();
