/**
 * 文件说明: 维护 CardNav 公开站点运行时常量，供 Astro 页面、布局和 API 复用。
 */
import 'dotenv/config';

export const publicSiteUrl = process.env.PUBLIC_SITE_URL || 'https://ai.lovemoney.live';
export const defaultSeoImagePath = '/og-cardnav.webp';
export const indexNowKey = process.env.INDEXNOW_KEY || 'ailovemoneyindexnow2026';
export const telegramGroupUrl = '';
export const xProfileUrl = '';
export const qqGroupUrl = '';

export const headerAdTagEnabled = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.HEADER_AD_TAG_ENABLED || '').trim().toLowerCase(),
);
