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
      const evidence = row.evidence;
      return {
        rank: evidence.displayRank,
        modelName: row.modelName,
        modelFamily: row.modelFamily,
        score: evidence.displayScore,
        isSample: evidence.status === 'sample',
        sourceName: row.localizedSourceName,
        sourceUrl: evidence.sourceUrl,
        sampledAt: evidence.sampledAt ? formatBeijingRefreshTime(evidence.sampledAt) : '',
        sourceBoard: row.sourceBoardSlug,
        groupKey: evidence.groupKey,
        status: evidence.status,
        methodStatus: evidence.methodStatus,
        sourceLabel: messages.leaderboard.sourceLabel,
        sourceLinkLabel: messages.leaderboard.sourceLink,
        sampledAtLabel: messages.leaderboard.sampledAt,
        sourceBoardLabel: messages.leaderboard.sourceBoard,
        statusLabel: messages.leaderboard[evidence.status],
        methodNotice: messages.leaderboard.methodNotRecorded,
        notProvided: messages.leaderboard.notProvided,
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
