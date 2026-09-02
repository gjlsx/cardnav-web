import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const readSource = (relativePath: string) => fs.readFileSync(path.resolve(relativePath), 'utf8');
const publicPageSource = readSource('src/layouts/PublicPage.astro');
const publicShellSource = readSource('src/scripts/public-shell.js');

test('public pages provide a fixed back-to-top action that stays hidden before scrolling', () => {
  assert.match(publicPageSource, /data-back-to-top/);
  assert.match(publicPageSource, /fixed bottom-6 right-6/);
  assert.match(publicPageSource, /aria-label="回到顶部"/);
  assert.match(publicPageSource, /hidden/);
});

test('public shell shows the action after one viewport and scrolls smoothly to the top', () => {
  assert.match(publicShellSource, /function initBackToTop\(\)/);
  assert.match(publicShellSource, /window\.scrollY > window\.innerHeight/);
  assert.match(publicShellSource, /button\.classList\.toggle\('hidden', !shouldShow\)/);
  assert.match(publicShellSource, /window\.scrollTo\(\{ top: 0, behavior: 'smooth' \}\)/);
  assert.match(publicShellSource, /initBackToTop\(\);/);
});
