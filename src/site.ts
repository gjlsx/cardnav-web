/**
 * 文件说明: 维护 CardNav 公开站点运行时常量，供 Astro 页面、布局和 API 复用。
 */
import 'dotenv/config';

export const publicSiteUrl = process.env.PUBLIC_SITE_URL || 'https://aigate.live';
export const defaultSeoImagePath = '/og-cardnav.webp';
export const indexNowKey = process.env.INDEXNOW_KEY || 'ailovemoneyindexnow2026';
export const telegramGroupUrl = 'https://t.me/+AX9TXrzMaS04OWI1';
export const sponsorUrl = 'https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00';
export const qqGroupNumber = '1106704568';
export const qqGroupJoinUrl = `https://qun.qq.com/join.html?gc=${qqGroupNumber}`;
export const gatewaySubmissionEmail = 'xiu.juan2love@gmail.com';
export const xProfileUrl = '';

export const headerAdTagEnabled = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.HEADER_AD_TAG_ENABLED || '').trim().toLowerCase(),
);
