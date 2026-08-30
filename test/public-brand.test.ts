/**
 * 文件说明: 约束公开站点的品牌、社群占位和赞助商展示要求。
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
const middlewareSource = readSource('src/middleware.ts');
const chineseReadme = readSource('README.md');
const englishReadme = readSource('README.en.md');

test('public runtime uses the approved sponsor, Telegram, and QQ community values', () => {
  assert.match(siteSource, /publicSiteUrl = process\.env\.PUBLIC_SITE_URL \|\| 'https:\/\/aigate\.live'/);
  assert.match(siteSource, /telegramGroupUrl = 'https:\/\/t\.me\/\+AX9TXrzMaS04OWI1'/);
  assert.match(siteSource, /sponsorUrl = 'https:\/\/buy\.stripe\.com\/cNi8wRgiq26I1Ese0V0Fi00'/);
  assert.match(siteSource, /qqGroupNumber = '1106704568'/);
  assert.match(siteSource, /gatewaySubmissionEmail = 'xiu\.juan2love@gmail\.com'/);
  assert.match(siteSource, /xProfileUrl = ''/);
  assert.doesNotMatch(siteSource, /cardnav\.xyz|t\.me\/cardnav_xyz_group|github\.com\/charleslee8266|x\.com\/CharlesLee8266/);
});

test('gateway submission and README files use the centralized public contacts', () => {
  assert.match(gatewaySource, /import \{ gatewaySubmissionEmail, publicSiteUrl, telegramGroupUrl \} from '\.\.\/site\.js'/);
  assert.doesNotMatch(gatewaySource, /const gatewaySubmissionEmail =/);
  for (const readme of [chineseReadme, englishReadme]) {
    assert.match(readme, /https:\/\/t\.me\/\+AX9TXrzMaS04OWI1/);
    assert.match(readme, /https:\/\/buy\.stripe\.com\/cNi8wRgiq26I1Ese0V0Fi00/);
    assert.match(readme, /1106704568/);
    assert.match(readme, /xiu\.juan2love@gmail\.com/);
    assert.doesNotMatch(readme, /href=["']README\.ru\.md["']/);
  }
});

test('the public site does not support Russian', () => {
  assert.equal(fs.existsSync(path.resolve('README.ru.md')), false);
  assert.match(chineseReadme, /不支持俄语/);
  assert.match(englishReadme, /does not support Russian/i);
});

test('shared page shell renders the published announcement with a QQ copy entry', () => {
  assert.doesNotMatch(publicPageSource, /githubRepoUrl|shouldShowHero/);
  assert.match(publicPageSource, /telegramGroupUrl/);
  assert.match(publicPageSource, /xProfileUrl/);
  assert.match(publicPageSource, /qqGroupNumber/);
  assert.match(publicPageSource, /sponsorUrl/);
  assert.match(publicPageSource, /t\.actions\.sponsor/);
  assert.match(publicPageSource, /t\.actions\.supportAuthor/);
  assert.match(publicPageSource, /loadHomepageAnnouncement/);
  assert.match(publicPageSource, /data-announcement-qq-group/);
  assert.match(publicPageSource, /data-copy-text=\{qqGroupNumber\}/);
  assert.match(publicPageSource, /announcement\.message/);
});

test('support panel is a Stripe-only support action and the logo is the local future mark', () => {
  assert.match(supportSource, /href=\{sponsorUrl\}/);
  assert.match(supportSource, /target="_blank"/);
  assert.match(publicPageSource, /\/lovemoney-mark\.svg/);
});

test('sponsors render images only without outbound links or copy', () => {
  assert.doesNotMatch(sponsorsSource, /<a\s+href=|sponsor-name|sponsor-copy|sponsor-plan-title|sponsor-plan-grid/);
  assert.match(sponsorsSource, /<img src=\{sponsor\.image\.src\}/);
});

test('old domain stays available until the AIGATE domain is connected', () => {
  assert.doesNotMatch(middlewareSource, /url\.hostname === 'ai\.lovemoney\.live'/);
  assert.doesNotMatch(middlewareSource, /target\.hostname = 'aigate\.live'/);
});
