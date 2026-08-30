/**
 * 文件说明: 约束公开站品牌入口、空社群占位、赞助商展示和 MySQL 运行时依赖。
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const readSource = (relativePath: string) => fs.readFileSync(path.resolve(relativePath), 'utf8');
const siteSource = readSource('src/site.ts');
const publicPageSource = readSource('src/layouts/PublicPage.astro');
const sponsorsSource = readSource('src/components/Sponsors.astro');
const supportSource = readSource('src/components/SponsorSupport.astro');
const gatewaySource = readSource('src/pages/llm-gateway.astro');
const packageSource = readSource('package.json');

test('public runtime uses the approved sponsor, Telegram, and QQ community values', () => {
  assert.match(siteSource, /publicSiteUrl = process\.env\.PUBLIC_SITE_URL \|\| 'https:\/\/aigate\.live'/);
  assert.match(siteSource, /telegramGroupUrl = 'https:\/\/t\.me\/\+AX9TXrzMaS04OWI1'/);
  assert.match(siteSource, /sponsorUrl = 'https:\/\/buy\.stripe\.com\/cNi8wRgiq26I1Ese0V0Fi00'/);
  assert.match(siteSource, /qqGroupNumber = '1106704568'/);
  assert.match(siteSource, /gatewaySubmissionEmail = 'xiu\.juan2love@gmail\.com'/);
  assert.match(siteSource, /xProfileUrl = ''/);
  assert.doesNotMatch(siteSource, /cardnav\.xyz|t\.me\/cardnav_xyz_group|github\.com\/charleslee8266|x\.com\/CharlesLee8266/);
});

test('gateway submission imports the centralized public email instead of duplicating it', () => {
  assert.match(gatewaySource, /gatewaySubmissionEmail/);
  assert.doesNotMatch(gatewaySource, /const gatewaySubmissionEmail =/);
});

test('shared page shell removes the hero and GitHub while keeping empty community placeholders', () => {
  assert.doesNotMatch(publicPageSource, /githubRepoUrl/);
  assert.match(publicPageSource, /telegramGroupUrl/);
  assert.match(publicPageSource, /xProfileUrl/);
  assert.match(publicPageSource, /qqGroupNumber/);
  assert.doesNotMatch(publicPageSource, /shouldShowHero/);
  assert.match(publicPageSource, /loadHomepageAnnouncement\(t\.announcement\.message\)/);
});

test('sponsors render images only without outbound links or copy', () => {
  assert.doesNotMatch(sponsorsSource, /<a\s+href=|sponsor-name|sponsor-copy|sponsor-plan-title|sponsor-plan-grid/);
  assert.match(sponsorsSource, /<img src=\{sponsor\.image\.src\}/);
});

test('support panel is a Stripe-only support action and the logo is the local future mark', () => {
  assert.match(supportSource, /href=\{sponsorUrl\}/);
  assert.match(supportSource, /target="_blank"/);
  assert.match(publicPageSource, /\/lovemoney-mark\.svg/);
});

test('runtime dependencies use MySQL instead of PostgreSQL', () => {
  assert.match(packageSource, /"mysql2"/);
  assert.doesNotMatch(packageSource, /"pg"|"@types\/pg"/);
});
