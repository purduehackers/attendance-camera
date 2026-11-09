const $ = id => document.getElementById(id);
let state, initialized = false, previewOn = false, previewURL, previewBusy = false;
const percentages = ['x_min','y_min','x_max','y_max','position','deadband'];
function error(message = '') { $('error').textContent = message; $('error').hidden = !message; }
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, headers: body ? {'Content-Type':'application/json'} : {}, body: body ? JSON.stringify(body) : undefined});
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
      initialized = true;
    }
  } catch (err) { $('connection').textContent = 'Server unavailable'; $('start').disabled = true; error(err.message); }
}
async function sessions() {
  const rows = await api('/api/sessions'); $('sessions').replaceChildren();
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
  error();
  try { await api(path, method, body); await refresh(); await sessions(); } catch (err) { error(err.message); }
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
  $('preview-toggle').textContent = previewOn ? 'Hide live preview' : 'Show live preview';
  if (!previewOn) { $('preview').removeAttribute('src'); if (previewURL) URL.revokeObjectURL(previewURL); }
});
async function preview() {
  if (!previewOn || previewBusy || document.hidden) return;
  previewBusy = true;
  try {
    const response = await fetch('/api/preview.jpg');
    if (!response.ok) { $('preview').removeAttribute('src'); return; }
    const next = URL.createObjectURL(await response.blob());
    if (previewURL) URL.revokeObjectURL(previewURL);
    previewURL = next; $('preview').src = next;
  } finally { previewBusy = false; }
}
(async function poll() { await refresh(); await preview().catch(() => {}); setTimeout(poll,1000); })();
(async function history() { await sessions().catch(err => error(err.message)); setTimeout(history,10000); })();
