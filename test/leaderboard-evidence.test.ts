import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildReferenceEvidence,
  evidenceGroupKey,
  parseReferenceScore,
  safeEvidenceUrl,
} from '../src/leaderboard-evidence.js';

test('unknown score is not zero while a real zero is preserved', () => {
  for (const value of [null, undefined, '', ' ', true, {}, NaN, Infinity]) {
    assert.equal(parseReferenceScore(value), null);
  }
  assert.equal(parseReferenceScore(0), 0);
  assert.equal(parseReferenceScore('0'), 0);
  assert.equal(parseReferenceScore('12.5'), 12.5);
});

test('evidence URLs accept public HTTP(S) only', () => {
  assert.equal(safeEvidenceUrl('https://example.com/board'), 'https://example.com/board');
  for (const value of [
    'javascript:alert(1)', 'data:text/plain,x', 'file:///etc/passwd', 'https://user:pass@example.com',
    'http://localhost:3101/', 'http://127.0.0.1/', 'http://10.0.0.1/', 'http://[::1]/', 'not a URL',
  ]) assert.equal(safeEvidenceUrl(value), null);
});

test('evidence group keys preserve source and snapshot identity', () => {
  const base = {
    sourceId: 'source-a', sourceUrl: 'https://example.com/one', sourceGroupSlug: 'text',
    sourceBoardSlug: 'coding', taskSlug: 'coding', sampledAt: '2026-09-01T00:00:00.000Z',
  };
  assert.notEqual(evidenceGroupKey(base), evidenceGroupKey({ ...base, sampledAt: '2026-09-02T00:00:00.000Z' }));
  assert.notEqual(evidenceGroupKey(base), evidenceGroupKey({ ...base, sourceUrl: 'https://example.com/two' }));
});

test('sample is distinct and unknown sources do not disclose a score or rank', () => {
  const sample = buildReferenceEvidence({
    taskSlug: 'coding', sourceName: 'CardNav', sourceUrl: 'https://cardnav.xyz/model-leaderboard/coding',
    sourceGroupSlug: 'text', sourceBoardSlug: 'coding', rank: 1, modelName: 'model-a', modelFamily: 'A',
    score: 0, sourceId: 'reference-cardnav-leaderboard', sampledAt: '2026-08-27T14:55:00.000Z', isSample: true, fetchedAt: '',
  });
  assert.equal(sample.status, 'sample');
  assert.equal(sample.displayScore, 0);
  assert.equal(sample.displayRank, 1);
  const unknown = buildReferenceEvidence({ ...sample.row, sourceId: 'unknown', isSample: false, score: 99, rank: 1 });
  assert.equal(unknown.status, 'unverified');
  assert.equal(unknown.displayScore, null);
  assert.equal(unknown.displayRank, null);
});
