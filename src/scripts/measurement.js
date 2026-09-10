(() => {
  const moduleKey = '__aigateMeasurementLoaded';
  if (window[moduleKey]) return;
  window[moduleKey] = true;

  const consentKey = 'aigate-measurement-consent';
  const sessionKey = 'aigate-measurement-session';
  const channelKey = 'aigate-measurement-channel';
  const storage = (() => {
    try {
      sessionStorage.getItem(consentKey);
      return sessionStorage;
    } catch {
      return null;
    }
  })();

  const allowed = () => storage?.getItem(consentKey) === 'yes';
  const uuid = () => crypto.randomUUID();
  const sessionId = () => {
    if (!storage) return null;
    let value = storage.getItem(sessionKey);
    if (!value) {
      value = uuid();
      storage.setItem(sessionKey, value);
    }
    return value;
  };
  const recognizedChannels = new Set(['google', 'qq', 'telegram', 'xiaohongshu', 'x', 'bilibili', 'substack', 'youtube']);
  const channelFromReferrer = () => {
    try {
      const source = new URL(location.href).searchParams.get('utm_source')?.toLowerCase();
      if (source && recognizedChannels.has(source)) return source;
      const host = new URL(document.referrer).hostname.toLowerCase();
      if (host.includes('google.')) return 'google';
      if (host === 't.me' || host.endsWith('.telegram.me')) return 'telegram';
      if (host.includes('xiaohongshu.com')) return 'xiaohongshu';
      if (host === 'x.com' || host.endsWith('.x.com') || host === 'twitter.com' || host.endsWith('.twitter.com')) return 'x';
      if (host.includes('bilibili.com')) return 'bilibili';
      if (host.includes('substack.com')) return 'substack';
      if (host.includes('qq.com')) return 'qq';
    } catch {
      // Referrer and URL parsing are optional; no fallback identifier is created.
    }
    return 'direct-or-unknown';
  };
  const channel = () => {
    if (!storage) return 'direct-or-unknown';
    const saved = storage.getItem(channelKey);
    if (saved && recognizedChannels.has(saved)) return saved;
    const value = channelFromReferrer();
    storage.setItem(channelKey, value);
    return value;
  };
  const send = (name, pageKind, fields = {}) => {
    const currentSession = sessionId();
    if (!allowed() || !currentSession) return;
    const event = {
      eventId: uuid(),
      sessionId: currentSession,
      name,
      pageKind,
      entityId: fields.entityId || null,
      sourceId: fields.sourceId || null,
      channel: channel(),
      placement: fields.placement || 'unknown',
      targetKind: fields.targetKind || 'unknown',
    };
    fetch('/api/measurement', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(event),
      keepalive: true,
    }).catch(() => {});
  };
  const labels = control => ({
    allow: control.dataset.measurementAllowLabel || 'Allow session analytics',
    stop: control.dataset.measurementStopLabel || 'Stop session analytics',
  });
  const pageEntry = () => {
    if (document.querySelector('[data-model-leaderboard]')) send('ranking_view', 'leaderboard');
    const comparison = document.querySelector('[data-measurement-entry]');
    if (comparison) {
      send('comparison_enter', comparison.dataset.measurementEntry, {
        entityId: comparison.dataset.measurementEntityId,
      });
    }
  };
  const comparisonPageKind = () => document.querySelector('[data-measurement-entry]')?.dataset.measurementEntry || 'gateway-list';
  const control = document.querySelector('[data-measurement-consent]');
  if (control) {
    const text = labels(control);
    control.textContent = allowed() ? text.stop : text.allow;
    control.addEventListener('click', () => {
      if (!storage) return;
      if (allowed()) {
        storage.removeItem(consentKey);
        storage.removeItem(sessionKey);
        storage.removeItem(channelKey);
        control.textContent = text.allow;
      } else {
        storage.setItem(consentKey, 'yes');
        control.textContent = text.stop;
        pageEntry();
      }
    });
  }
  if (allowed()) pageEntry();

  const handledEvents = new WeakSet();
  document.addEventListener('click', event => {
    if (handledEvents.has(event)) return;
    handledEvents.add(event);
    const element = event.target instanceof Element ? event.target : null;
    const target = element?.closest('[data-measurement-name]');
    if (target) {
      send(target.dataset.measurementName, target.dataset.measurementPageKind || 'leaderboard', {
        entityId: target.dataset.measurementEntityId,
        sourceId: target.dataset.measurementSourceId,
        placement: target.dataset.measurementPlacement,
        targetKind: target.dataset.measurementTargetKind,
      });
    }
    const sort = element?.closest('.data-table-sort-button');
    if (sort) send('comparison_interact', comparisonPageKind());
  });
  document.addEventListener('change', event => {
    const element = event.target instanceof Element ? event.target : null;
    if (element?.matches('.gateway-filter-grid input, .gateway-filter-grid select')) {
      send('comparison_interact', comparisonPageKind());
    }
  });
})();
