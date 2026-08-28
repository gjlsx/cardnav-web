import test from 'node:test';
import assert from 'node:assert/strict';
import { getMessages } from '../src/i18n/messages.js';

test('public navigation uses the approved three-locale entry names', () => {
  const expected = {
    zh: { gateway: '中转网站', official: '官方网站', guide: '帮助' },
    en: { gateway: 'Gateway sites', official: 'Official sites', guide: 'Help' },
    ru: { gateway: 'Сайты-шлюзы', official: 'Официальные сайты', guide: 'Помощь' },
  } as const;

  for (const [locale, labels] of Object.entries(expected)) {
    const messages = getMessages(locale as keyof typeof expected);
    assert.equal(messages.nav.llmGateway, labels.gateway);
    assert.equal(messages.nav.officialPrice, labels.official);
    assert.equal(messages.nav.guide, labels.guide);
    assert.equal(messages.nav.mobileLlmGateway, labels.gateway);
    assert.equal(messages.nav.mobileOfficialPrice, labels.official);
    assert.equal(messages.nav.mobileGuide, labels.guide);
  }
});

test('home help entry does not retain the old guide wording', () => {
  const expected = {
    zh: { home: '不知道如何开始？点击进入帮助', ip: '什么是 IP 纯净度？查看帮助说明', docs: '帮助文档列表', eyebrow: '帮助指南' },
    en: { home: 'Not sure where to start? Open help', ip: 'What is IP purity? Read the help', docs: 'Help document list', eyebrow: 'Help' },
    ru: { home: 'Не знаете, с чего начать? Откройте раздел помощи', ip: 'Что такое чистота IP? Читать помощь', docs: 'Список документов помощи', eyebrow: 'Помощь' },
  } as const;

  for (const locale of ['zh', 'en', 'ru'] as const) {
    const messages = getMessages(locale);
    assert.equal(messages.home.guideTitle, expected[locale].home);
    assert.equal(messages.ipPurity.guideLink, expected[locale].ip);
    assert.equal(messages.guide.docListLabel, expected[locale].docs);
    assert.equal(messages.guide.eyebrow, expected[locale].eyebrow);
  }
});
