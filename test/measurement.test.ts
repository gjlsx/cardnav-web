import assert from 'node:assert/strict';
import test from 'node:test';
import { readMeasurementConfig } from '../src/measurement-config.js';
import { hongKongDay, validateMeasurementEvent } from '../src/measurement.js';

const uuid = 'f0c7d42f-72a9-4f96-bd6d-5dbe934d4b72';

test('measurement is disabled by default and validates explicit finite limits', () => {
  assert.equal(readMeasurementConfig({}).enabled, false);
  assert.deepEqual(readMeasurementConfig({ MEASUREMENT_ENABLED: 'true', MEASUREMENT_ENVIRONMENT: 'local-test' }), {
    enabled: true, environment: 'local-test', retentionDays: 14, maxEventBytes: 2048, maxEventsPerDay: 10000,
  });
  assert.throws(() => readMeasurementConfig({ MEASUREMENT_ENABLED: 'yes' }));
  assert.throws(() => readMeasurementConfig({ MEASUREMENT_RETENTION_DAYS: '0' }));
});

test('measurement events have a strict allowlist and never accept URLs or identity fields', () => {
  const valid = validateMeasurementEvent({ eventId: uuid, sessionId: uuid, name: 'outbound_click', pageKind: 'leaderboard', entityId: 'gpt-5', sourceId: null, channel: 'google', placement: 'natural', targetKind: 'official' });
  assert.equal(valid?.name, 'outbound_click');
  assert.equal(validateMeasurementEvent({ name: 'purchase', email: 'x' }), null);
  assert.equal(validateMeasurementEvent({ eventId: uuid, sessionId: uuid, name: 'outbound_click', pageKind: 'leaderboard', url: 'https://x/?token=y' }), null);
  assert.equal(validateMeasurementEvent({ eventId: uuid, sessionId: uuid, name: 'outbound_click', pageKind: 'leaderboard', unknown: true }), null);
});

test('daily quotas use the Hong Kong calendar day rather than UTC', () => {
  assert.equal(hongKongDay(new Date('2026-09-06T16:30:00.000Z')), '2026-09-07');
});
