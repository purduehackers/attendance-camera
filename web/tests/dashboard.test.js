import {expect, test} from 'bun:test';
import {readFileSync} from 'node:fs';
import {createContext, runInContext} from 'node:vm';

const source = readFileSync(new URL('../src/scripts/dashboard.js', import.meta.url), 'utf8');
const settle = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };

function dashboard() {
  const elements = new Map(), listeners = new Map(), revoked = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      textContent: '', hidden: false, handlers: {},
      addEventListener(name, callback) { this.handlers[name] = callback; },
      setAttribute(name, value) { this[name] = value; },
      removeAttribute(name) { delete this[name]; },
      replaceChildren() {}, append() {},
    });
    return elements.get(id);
  };
  const status = {fresh: true, calibrated: true, calibration: {axis: 'y', inside: 'positive'}};
  const replies = {
    '/api/status': () => Response.json(status),
    '/api/sessions': () => Response.json([]),
    '/api/preview.jpg': () => new Response('jpeg', {headers: {'Content-Type': 'image/jpeg'}}),
  };
  let urlId = 0, decode = async () => {};
  const context = createContext({
    document: {hidden: false, getElementById: element, createElement: element,
      addEventListener: (name, callback) => listeners.set(name, callback)},
    fetch: async path => replies[path](),
    location: {assign: path => { context.redirect = path; }},
    Image: class { decode() { return decode(); } },
    URL: {createObjectURL: () => `blob:${++urlId}`, revokeObjectURL: url => revoked.push(url)},
    AbortController, setTimeout: () => 1, clearTimeout() {},
  });
  runInContext(source, context);
  return {context, element, replies, revoked, listeners, setDecode: callback => { decode = callback; }};
}

test('the preview starts without a click, reports a lost frame, then recovers', async () => {
  const {context, element, replies, revoked} = dashboard();
  await settle();
  expect(element('preview').src).toBe('blob:1');
  expect(element('preview').hidden).toBe(false);
  replies['/api/preview.jpg'] = () => new Response('', {status: 503});
  await context.preview();
  expect(element('preview').src).toBeUndefined();
  expect(element('preview').hidden).toBe(true);
  expect(element('preview-status').textContent).toContain('Reconnecting');
  expect(revoked).toContain('blob:1');
  replies['/api/preview.jpg'] = () => new Response('jpeg', {headers: {'Content-Type': 'image/jpeg'}});
  await context.preview();
  expect(element('preview').hidden).toBe(false);
  expect(element('preview-status').textContent).toBe('Live camera preview');
});

test('successful polling clears its own error without hiding a failed action', async () => {
  const {context, element, replies} = dashboard();
  await settle();
  const healthy = replies['/api/status'];
  replies['/api/status'] = () => Response.json({detail: 'Disconnected'}, {status: 503});
  await context.refresh();
  expect(element('error').textContent).toBe('Disconnected');
  replies['/api/action'] = () => Response.json({detail: 'Calibration rejected'}, {status: 422});
  await context.change('/api/action', 'PUT', {});
  replies['/api/status'] = healthy;
  await context.refresh();
  expect(element('connection').textContent).toBe('Camera connected');
  expect(element('error').textContent).toBe('Calibration rejected');
  replies['/api/action'] = () => Response.json({ok: true});
  await context.change('/api/action', 'PUT', {});
  expect(element('error').hidden).toBe(true);
});

test('hiding the preview while a frame decodes discards the pending frame', async () => {
  const {context, element, revoked, setDecode} = dashboard();
  await settle();
  let finish;
  setDecode(() => new Promise(resolve => { finish = resolve; }));
  const pending = context.preview();
  await settle();
  element('preview-toggle').handlers.click();
  finish(); await pending;
  expect(element('preview-wrap').hidden).toBe(true);
  expect(element('preview').src).toBeUndefined();
  expect(revoked).toEqual(['blob:1', 'blob:2']);
});

test('preview authentication expiry redirects to sign-in and clears the image', async () => {
  const {context, element, replies} = dashboard();
  await settle();
  replies['/api/preview.jpg'] = () => new Response('', {status: 401});
  await context.preview();
  expect(context.redirect).toBe('/login');
  expect(element('preview').src).toBeUndefined();
});
