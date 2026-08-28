/**
 * 文件说明: 验证本地 MySQL 初始化会创建公开站点运行所需的数据表。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import mysql, { type RowDataPacket } from 'mysql2/promise';
import { initializeMySqlSchema } from '../src/database.js';

const config = {
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD || 'gj',
  database: process.env.MYSQL_DATABASE || 'ailovemoney',
};

test('MySQL schema creates every public runtime table', async () => {
  await initializeMySqlSchema(config);
  const connection = await mysql.createConnection(config);
  try {
    const [rows] = await connection.query<RowDataPacket[]>('SHOW TABLES');
    const tables = new Set(rows.map(row => Object.values(row)[0]));
    for (const table of [
      'public_snapshot_entries', 'shop_sites', 'shop_products', 'shop_search_terms',
      'gateway_sites', 'gateway_model_prices', 'official_prices', 'model_leaderboards', 'reference_data_sources',
      'catalog_products', 'catalog_plan_models', 'shop_site_model_coverage', 'catalog_unknown_aliases',
    ]) {
      assert.ok(tables.has(table), `missing ${table}`);
    }
  } finally {
    await connection.end();
  }
});

test('MySQL schema keeps source priority separate from site display score and declares canonical catalog tables', async () => {
  const connection = await mysql.createConnection(config);
  try {
    await initializeMySqlSchema(config);
    const [sourceRows] = await connection.query<RowDataPacket[]>('SHOW COLUMNS FROM reference_data_sources');
    assert.ok(sourceRows.some(row => row.Field === 'priority'));
    const [catalogRows] = await connection.query<RowDataPacket[]>('SHOW COLUMNS FROM catalog_products');
    assert.ok(catalogRows.some(row => row.Field === 'target_kind'));
    const [indexRows] = await connection.query<RowDataPacket[]>('SHOW INDEX FROM shop_products');
    assert.ok(indexRows.some(row => row.Key_name === 'shop_products_source_standard_site'));
  } finally {
    await connection.end();
  }
});

test('MySQL natural-key migration removes deterministic legacy duplicates before adding its unique index', async () => {
  const source = await fs.promises.readFile(path.resolve('src/database.ts'), 'utf8');
  const migration = source.match(/async function ensureShopProductNaturalKey[\s\S]+?^}/m)?.[0] ?? '';
  assert.match(migration, /DELETE duplicate FROM shop_products AS duplicate/);
  assert.match(migration, /duplicate\.source_id IS NOT NULL/);
  assert.match(migration, /CREATE UNIQUE INDEX shop_products_source_standard_site/);
});

test('MySQL schema keeps reference sample provenance columns on shop products', async () => {
  await initializeMySqlSchema(config);
  const connection = await mysql.createConnection(config);
  try {
    const [rows] = await connection.query<RowDataPacket[]>('SHOW COLUMNS FROM shop_products');
    const columns = new Set(rows.map(row => String(row.Field)));
    for (const column of ['source_id', 'standard_product', 'platform', 'product_type', 'currency_code', 'channel_count', 'available_channel_count', 'out_of_stock_channel_count', 'sampled_at', 'is_sample']) {
      assert.ok(columns.has(column), `missing ${column}`);
    }
  } finally {
    await connection.end();
  }
});
