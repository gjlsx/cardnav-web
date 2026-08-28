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
  for (const locale of ['zh', 'en', 'ru'] as const) {
    const messages = getMessages(locale);
    assert.notEqual(messages.actions.openGuide, '打开完整向导');
    assert.notEqual(messages.actions.openGuide, 'Open full guide');
    assert.notEqual(messages.actions.openGuide, 'Открыть полный гайд');
  }
});
