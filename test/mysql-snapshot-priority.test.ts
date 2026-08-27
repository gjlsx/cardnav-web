/**
 * 文件说明: 防止 MySQL 迁移后快照被运行时表读取意外绕过，或重新引入 PostgreSQL SQL。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const source = fs.readFileSync('src/store.ts', 'utf8');

test('MySQL store keeps every migrated snapshot on its public read path', () => {
  for (const key of [
    'shop-products',
    'shop-products-packed',
    'popular-search-terms',
    'gateway-sites',
    'gateway-models',
    'official-price-catalog',
    'official-prices',
    'model-leaderboard-task-slugs',
    'model-leaderboards',
  ]) {
    assert.match(source, new RegExp(`loadPublicSnapshot(?:<[^>]+>)?\\('${key}'\\)`));
  }
});

test('MySQL store contains no PostgreSQL-only query syntax or type-check bypass', () => {
  assert.doesNotMatch(source, /@ts-nocheck|ARRAY_AGG|jsonb_|DISTINCT ON|\bctid\b|ON CONFLICT|\bRETURNING\b|\$[0-9]+/i);
  assert.match(source, /ER_NO_SUCH_TABLE/);
});
