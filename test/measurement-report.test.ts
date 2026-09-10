import assert from 'node:assert/strict';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { MAX_EXTERNAL_REPORT_BYTES, readExternalMetrics } from '../scripts/measurement-report.js';
import { hongKongWeekWindow, reduceMeasurementReport, validateExternalMetrics } from '../src/measurement.js';

test('Hong Kong week windows are strict Monday UTC half-open ranges', () => {
  assert.deepEqual(hongKongWeekWindow('2026-09-07'), { start: '2026-09-06T16:00:00.000Z', end: '2026-09-13T16:00:00.000Z' });
  assert.throws(() => hongKongWeekWindow('2026-09-08'));
  assert.throws(() => hongKongWeekWindow('2026-02-30'));
});

test('report reduction counts only ordered comparison-interaction-outbound paths', () => {
  const result = reduceMeasurementReport([
    { sessionId: 'a', name: 'comparison_enter', channel: 'google', receivedAt: '2026-09-07T00:00:00.000Z' },
    { sessionId: 'a', name: 'comparison_interact', channel: 'google', receivedAt: '2026-09-07T00:01:00.000Z' },
    { sessionId: 'a', name: 'outbound_click', channel: 'google', receivedAt: '2026-09-07T00:02:00.000Z' },
    { sessionId: 'b', name: 'outbound_click', channel: 'telegram', receivedAt: '2026-09-07T00:00:00.000Z' },
    { sessionId: 'b', name: 'comparison_enter', channel: 'telegram', receivedAt: '2026-09-07T00:01:00.000Z' },
    { sessionId: 'b', name: 'comparison_interact', channel: 'telegram', receivedAt: '2026-09-07T00:02:00.000Z' },
  ]);
  assert.equal(result.observedSessions, 2);
  assert.equal(result.pathSessions, 1);
  assert.deepEqual(result.channelSummary, { google: 3, telegram: 3 });
});

test('external metrics accept only a small, deduplicated public schema', async () => {
  const valid = [{ platform: 'youtube', periodStart: '2026-09-07', periodEnd: '2026-09-13', timezone: 'Asia/Hong_Kong', metric: 'views', value: 3, sourceUrl: 'https://studio.youtube.com/report', exportedAt: '2026-09-14T00:00:00.000Z' }];
  assert.equal(validateExternalMetrics(valid)?.length, 1);
  assert.equal(validateExternalMetrics([...valid, valid[0]]), null);
  assert.equal(validateExternalMetrics([{ ...valid[0], sourceUrl: 'https://x.example/?token=secret' }]), null);

  const directory = await mkdtemp(join(tmpdir(), 'aigate-measurement-'));
  const file = join(directory, 'platform-summary.json');
  await writeFile(file, JSON.stringify(valid));
  assert.equal((await readExternalMetrics(file)).length, 1);
  const tooLarge = join(directory, 'too-large.json');
  await writeFile(tooLarge, ' '.repeat(MAX_EXTERNAL_REPORT_BYTES + 1));
  await assert.rejects(() => readExternalMetrics(tooLarge), /1 MiB/);
});
