/**
 * 文件说明: MySQL 连接配置与幂等的公开站点表结构初始化。
 */
import mysql from 'mysql2/promise';

export type MySqlConnectionConfig = {
  host: string;
  port: number;
  user: string;
  password?: string;
  database: string;
};

const statements = [
  `CREATE TABLE IF NOT EXISTS public_snapshot_entries (
    \`key\` VARCHAR(100) NOT NULL PRIMARY KEY,
    payload JSON NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS reference_data_sources (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT '',
    source_page_url TEXT NOT NULL,
    sampled_at DATETIME NOT NULL,
    is_sample BOOLEAN NOT NULL DEFAULT TRUE,
    usage_note VARCHAR(500) NOT NULL DEFAULT '',
    KEY reference_data_sources_sampled_at (sampled_at)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS shop_sites (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    last_product_refresh_success_at DATETIME NULL,
    score DECIMAL(12,4) NOT NULL DEFAULT 0,
    sponsor BOOLEAN NOT NULL DEFAULT FALSE,
    product_count INT NOT NULL DEFAULT 0,
    in_stock_product_count INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'online',
    type VARCHAR(32) NOT NULL DEFAULT 'cardShop',
    family VARCHAR(100) NOT NULL DEFAULT '',
    UNIQUE KEY shop_sites_url_unique (url(255)),
    KEY shop_sites_public_order (status, type, sponsor, score)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS shop_products (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_id VARCHAR(64) NULL,
    category_name VARCHAR(255) NOT NULL DEFAULT '',
    name VARCHAR(500) NOT NULL DEFAULT '',
    price VARCHAR(255) NULL,
    price_number DECIMAL(18,6) NULL,
    price_unit VARCHAR(100) NULL,
    product_url TEXT NULL,
    stock INT NULL,
    in_stock BOOLEAN NOT NULL DEFAULT FALSE,
    refreshed_at DATETIME NULL,
    click_count INT NOT NULL DEFAULT 0,
    score DECIMAL(12,4) NOT NULL DEFAULT 0,
    KEY shop_products_site_id (site_id),
    KEY shop_products_public_order (score, refreshed_at)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS shop_search_terms (
    term VARCHAR(255) NOT NULL PRIMARY KEY,
    total_count INT NOT NULL DEFAULT 0,
    result_count INT NOT NULL DEFAULT 0,
    last_seen_at DATETIME NULL,
    KEY shop_search_terms_public_order (total_count, result_count, last_seen_at)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS gateway_sites (
    site_id VARCHAR(64) NOT NULL PRIMARY KEY,
    url TEXT NOT NULL,
    api_endpoint TEXT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'online',
    name VARCHAR(255) NOT NULL DEFAULT '',
    family VARCHAR(100) NULL,
    type VARCHAR(32) NOT NULL DEFAULT 'gateway',
    slug VARCHAR(255) NOT NULL,
    host VARCHAR(255) NOT NULL DEFAULT '',
    weight INT NOT NULL DEFAULT 0,
    summary TEXT NULL,
    invite_url TEXT NULL,
    sponsor BOOLEAN NOT NULL DEFAULT FALSE,
    score DECIMAL(12,4) NOT NULL DEFAULT 0,
    availability_percent DECIMAL(8,3) NOT NULL DEFAULT 0,
    avg_success_latency_ms INT NULL,
    model_types JSON NULL,
    payment_methods JSON NULL,
    created_at DATETIME NULL,
    UNIQUE KEY gateway_sites_url_unique (url(255)),
    UNIQUE KEY gateway_sites_slug_unique (slug),
    KEY gateway_sites_public_order (status, type, sponsor, score)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS gateway_model_prices (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_id VARCHAR(64) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    model_family VARCHAR(255) NOT NULL DEFAULT '',
    unit VARCHAR(100) NOT NULL DEFAULT '',
    input_price DECIMAL(18,8) NULL,
    output_price DECIMAL(18,8) NULL,
    cache_input_price DECIMAL(18,8) NULL,
    cache_output_price DECIMAL(18,8) NULL,
    fetched_at DATETIME NULL,
    KEY gateway_model_prices_site_id (site_id),
    KEY gateway_model_prices_model_id (model_id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS official_prices (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    app_slug VARCHAR(255) NOT NULL,
    plan_slug VARCHAR(255) NOT NULL,
    app_name VARCHAR(255) NOT NULL DEFAULT '',
    plan_name VARCHAR(255) NOT NULL DEFAULT '',
    display_name VARCHAR(255) NOT NULL DEFAULT '',
    url_slug VARCHAR(255) NOT NULL DEFAULT '',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    display_order INT NOT NULL DEFAULT 0,
    country_code VARCHAR(32) NOT NULL DEFAULT '',
    country_label VARCHAR(255) NOT NULL DEFAULT '',
    currency_code VARCHAR(32) NOT NULL DEFAULT '',
    price_text VARCHAR(255) NOT NULL DEFAULT '',
    price_value DECIMAL(18,6) NOT NULL DEFAULT 0,
    cny_price DECIMAL(18,6) NOT NULL DEFAULT 0,
    usd_price DECIMAL(18,6) NOT NULL DEFAULT 0,
    rub_price DECIMAL(18,6) NOT NULL DEFAULT 0,
    fetched_at DATETIME NULL,
    KEY official_prices_catalog (app_slug, plan_slug, display_order),
    KEY official_prices_url_slug (url_slug)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  `CREATE TABLE IF NOT EXISTS model_leaderboards (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    task_slug VARCHAR(255) NOT NULL,
    source_name VARCHAR(255) NOT NULL DEFAULT '',
    source_url TEXT NOT NULL,
    source_group_slug VARCHAR(255) NOT NULL DEFAULT '',
    source_board_slug VARCHAR(255) NOT NULL DEFAULT '',
    rank INT NOT NULL,
    model_name VARCHAR(255) NOT NULL DEFAULT '',
    score DECIMAL(18,6) NOT NULL DEFAULT 0,
    fetched_at DATETIME NULL,
    KEY model_leaderboards_task_rank (task_slug, rank)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
];

const shopProductColumns = [
  ['source_id', 'VARCHAR(64) NULL'],
  ['standard_product', "VARCHAR(255) NOT NULL DEFAULT ''"],
  ['platform', "VARCHAR(100) NOT NULL DEFAULT ''"],
  ['product_type', "VARCHAR(100) NOT NULL DEFAULT ''"],
  ['currency_code', "VARCHAR(32) NOT NULL DEFAULT ''"],
  ['channel_count', 'INT NULL'],
  ['available_channel_count', 'INT NULL'],
  ['out_of_stock_channel_count', 'INT NULL'],
  ['sampled_at', 'DATETIME NULL'],
  ['is_sample', 'BOOLEAN NOT NULL DEFAULT FALSE'],
] as const;

async function ensureShopProductColumns(connection: mysql.Connection) {
  for (const [name, definition] of shopProductColumns) {
    const [rows] = await connection.query<mysql.RowDataPacket[]>(
      `SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'shop_products' AND column_name = ? LIMIT 1`,
      [name],
    );
    if (rows.length === 0) await connection.query(`ALTER TABLE shop_products ADD COLUMN \`${name}\` ${definition}`);
  }
}

export async function initializeMySqlSchema(config: MySqlConnectionConfig) {
  const connection = await mysql.createConnection(config);
  try {
    for (const statement of statements) await connection.query(statement);
    await ensureShopProductColumns(connection);
  } finally {
    await connection.end();
  }
}
