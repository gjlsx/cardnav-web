/**
 * 文件说明: 提供中转站首页首屏之后的站点排行 JSON 数据。
 */
import type { APIRoute } from 'astro';
import {
  publicReadApiCacheControl,
  publicReadApiCloudflareCacheControl,
} from '../../../public-data-cache.js';
import { paginateGatewayRanking } from '../../../gateway-ranking.js';
import { loadGatewaySites } from '../../../store.js';

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  const data = await loadGatewaySites({ modelFamily: url.searchParams.get('model') || '' });
  const ranking = paginateGatewayRanking(data.sites, Number(url.searchParams.get('offset') || '0'));
  return new Response(JSON.stringify({
    offset: ranking.offset,
    totalCount: ranking.natural.length,
    items: ranking.items,
    sponsored: ranking.sponsored,
  }), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': publicReadApiCacheControl,
      'cloudflare-cdn-cache-control': publicReadApiCloudflareCacheControl,
    },
  });
};
