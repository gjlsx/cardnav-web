import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const source = fs.readFileSync('src/pages/api/measurement.ts', 'utf8');
test('measurement API remains closed by default and rejects cross-origin or oversized input before recording', () => {
  assert.match(source, /if \(!config\.enabled\) return new Response\(null, \{ status: 204/);
  assert.match(source, /origin !== site/);
  assert.match(source, /sec-fetch-site'\) !== 'same-origin'/);
  assert.match(source, /startsWith\('application\/json'\)/);
  assert.match(source, /size > config\.maxEventBytes/);
  assert.match(source, /status: 413/);
  assert.match(source, /status: 403/);
  assert.match(source, /cache-control': 'no-store/);
});
