/**
 * 文件说明: 提供单个模型支持中转站列表首屏之后的 JSON 数据。
 */
import type { APIRoute } from 'astro';
import {
  publicReadApiCacheControl,
  publicReadApiCloudflareCacheControl,
} from '../../../../public-data-cache.js';
import { paginateGatewayRanking } from '../../../../gateway-ranking.js';
import { loadGatewayModelDetail } from '../../../../store.js';

export const GET: APIRoute = async ({ params, request }) => {
  const url = new URL(request.url);
  const offset = Math.max(0, Number(url.searchParams.get('offset') || '0') || 0);
  const detail = await loadGatewayModelDetail(params.modelId || '');

  if (!detail) {
    return new Response(JSON.stringify({ offset, totalCount: 0, items: [], sponsored: [] }), {
      status: 404,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': publicReadApiCacheControl,
        'cloudflare-cdn-cache-control': publicReadApiCloudflareCacheControl,
      },
    });
  }

  const ranking = paginateGatewayRanking(detail.sites, offset);
  return new Response(JSON.stringify({
    offset: ranking.offset,
    totalCount: detail.model.supportSiteCount,
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
