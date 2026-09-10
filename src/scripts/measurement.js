(() => {
  const consentKey = 'aigate-measurement-consent'; const sessionKey = 'aigate-measurement-session'; let sent = new WeakMap();
  const storage = (() => { try { sessionStorage.getItem(consentKey); return sessionStorage; } catch { return null; } })();
  const enabled = () => storage?.getItem(consentKey) === 'yes';
  const id = () => { if (!storage) return null; let value = storage.getItem(sessionKey); if (!value) { value = crypto.randomUUID(); storage.setItem(sessionKey, value); } return value; };
  const send = (name, pageKind, fields = {}) => { const sessionId = id(); if (!enabled() || !sessionId) return; const event = { eventId: crypto.randomUUID(), sessionId, name, pageKind, entityId: fields.entityId || null, sourceId: fields.sourceId || null, channel: 'direct-or-unknown', placement: fields.placement || 'unknown', targetKind: fields.targetKind || 'unknown' }; fetch('/api/measurement', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(event), keepalive: true }).catch(() => {}); };
  const control = document.querySelector('[data-measurement-consent]');
  if (control) control.addEventListener('click', () => { if (!storage) return; if (enabled()) { storage.removeItem(consentKey); storage.removeItem(sessionKey); control.textContent = 'Allow session analytics'; } else { storage.setItem(consentKey, 'yes'); control.textContent = 'Stop session analytics'; if (document.querySelector('[data-model-leaderboard]')) send('ranking_view', 'leaderboard'); } });
  if (enabled() && document.querySelector('[data-model-leaderboard]')) send('ranking_view', 'leaderboard');
  document.addEventListener('click', event => { const target = event.target instanceof Element ? event.target.closest('[data-measurement-name]') : null; if (!target || sent.has(target)) return; sent.set(target, true); send(target.dataset.measurementName, target.dataset.measurementPageKind || 'leaderboard', { entityId: target.dataset.measurementEntityId, sourceId: target.dataset.measurementSourceId, placement: target.dataset.measurementPlacement, targetKind: target.dataset.measurementTargetKind }); });
})();
