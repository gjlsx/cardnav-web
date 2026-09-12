/**
 * 文件说明: 提供中转站首页首屏之后的站点排行 JSON 数据。
 */
import type { APIRoute } from 'astro';
import {
  publicReadApiCacheControl,
  publicReadApiCloudflareCacheControl,
} from '../../../public-data-cache.js';
import { splitGatewaySiteRanking } from '../../../gateway-ranking.js';
import { loadGatewaySites } from '../../../store.js';

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  const offset = Math.max(0, Number(url.searchParams.get('offset') || '0') || 0);
  const data = await loadGatewaySites({ modelFamily: url.searchParams.get('model') || '' });
  const ranking = splitGatewaySiteRanking(data.sites);
  return new Response(JSON.stringify({
    offset,
    totalCount: ranking.natural.length,
    items: ranking.natural.slice(offset),
    sponsored: ranking.sponsored,
  }), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': publicReadApiCacheControl,
      'cloudflare-cdn-cache-control': publicReadApiCloudflareCacheControl,
    },
  });
};
