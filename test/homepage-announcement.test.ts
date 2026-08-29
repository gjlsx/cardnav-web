/**
 * 文件说明: 锁定首页公告从公开快照读取、回退本地文案和 QQ 复制入口的边界。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const storeSource = fs.readFileSync(path.resolve('src/store.ts'), 'utf8');
const siteConfigSource = fs.readFileSync(path.resolve('scripts/collection/console_tabs/site_config_tab.py'), 'utf8');
const cliPath = path.resolve('scripts/collection/announce.py');

test('homepage announcement reads the dedicated public snapshot with a locale fallback', () => {
  assert.match(storeSource, /'homepage-announcement'/);
  assert.match(storeSource, /loadHomepageAnnouncement/);
  assert.match(storeSource, /fallbackMessage/);
});

test('local site configuration and a one-line CLI publish the announcement', () => {
  assert.match(siteConfigSource, /save_homepage_announcement/);
  assert.equal(fs.existsSync(cliPath), true);
  assert.match(fs.readFileSync(cliPath, 'utf8'), /--message/);
});
