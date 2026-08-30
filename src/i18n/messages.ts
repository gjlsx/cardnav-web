/**
 * 文件说明: 聚合公开站点多语言文案，并提供按 locale 获取文案的统一入口。
 */
import type { Locale } from './config.js';
import { enMessages } from './en.js';
import { ruMessages } from './ru.js';
import { zhMessages, type Messages } from './zh.js';

const messagesByLocale: Record<Locale, Messages> = {
  zh: zhMessages,
  en: enMessages,
  ru: ruMessages,
};

export function getMessages(locale: Locale): Messages {
  // Keep historic source text untouched while making every user-facing message
  // use the current public brand.
  return JSON.parse(JSON.stringify(messagesByLocale[locale] ?? zhMessages)
    .replaceAll('AI LoveMoney', 'AIGATE')
    .replaceAll('ai.lovemoney.live', 'aigate.live')) as Messages;
}
