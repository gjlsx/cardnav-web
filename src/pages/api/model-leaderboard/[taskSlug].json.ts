/**
 * 文件说明: 提供模型排行榜首屏之后的行数据 JSON，供公开榜单页按需加载。
 */
import type { APIRoute } from 'astro';
import { isLocale } from '../../../i18n/config.js';
import { getMessages } from '../../../i18n/messages.js';
import { localizePath } from '../../../i18n/paths.js';
import { localizeModelLeaderboardGroups } from '../../../localized-display.js';
import { buildModelLeaderboardGroups, leaderboardRelatedPaths } from '../../../model-leaderboard.js';
import {
  publicReadApiCacheControl,
  publicReadApiCloudflareCacheControl,
} from '../../../public-data-cache.js';
import { formatBeijingRefreshTime, loadModelLeaderboardRowsForTask } from '../../../store.js';

export const GET: APIRoute = async ({ params, request }) => {
  const url = new URL(request.url);
  const offset = Math.max(0, Number(url.searchParams.get('offset') || '0') || 0);
  const rawLocale = url.searchParams.get('locale') || '';
  const locale = isLocale(rawLocale) ? rawLocale : 'zh';
  const messages = getMessages(locale);
  const taskSlug = params.taskSlug || '';
  const activeRows = await loadModelLeaderboardRowsForTask(taskSlug);
  const groups = localizeModelLeaderboardGroups(
    buildModelLeaderboardGroups(activeRows),
    messages,
    locale,
  );
  const currentGroup = groups.find(group => group.taskSlug === taskSlug);

  if (!currentGroup) {
    return new Response(JSON.stringify({ rows: [] }), {
      status: 404,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': publicReadApiCacheControl,
        'cloudflare-cdn-cache-control': publicReadApiCloudflareCacheControl,
      },
    });
  }

  return new Response(JSON.stringify({
    totalCount: currentGroup.rows.length,
    emptySample: messages.leaderboard.emptySample,
    rows: currentGroup.rows.slice(offset).map(row => {
      const related = leaderboardRelatedPaths(row.modelFamily);
      return {
        rank: row.rank,
        modelName: row.modelName,
        modelFamily: row.modelFamily,
        score: row.score,
        isSample: row.isSample,
        sourceName: row.localizedSourceName,
        sampledAt: row.sampledAt ? formatBeijingRefreshTime(row.sampledAt) : '',
        shopPath: related.shopPath ? localizePath(related.shopPath, locale) : '',
        gatewayPath: related.gatewayPath ? localizePath(related.gatewayPath, locale) : '',
        shopTip: messages.leaderboard.shopProductsTip,
        gatewayTip: messages.leaderboard.gatewayTip,
        relatedEmpty: messages.leaderboard.relatedEmpty,
        sampleBadge: messages.leaderboard.sampleBadge,
      };
    }),
  }), {
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': publicReadApiCacheControl,
      'cloudflare-cdn-cache-control': publicReadApiCloudflareCacheControl,
    },
  });
};
