/**
 * 文件说明: 维护模型排行榜页的任务分组、排序、关联查询和独立 URL 规则。
 */
import { catalogProductSlugsForTarget } from './catalog.js';
import { evidenceGroupKey } from './leaderboard-evidence.js';
import type { PublicModelLeaderboardRow } from './store.js';

export type ModelLeaderboardGroup<Row extends PublicModelLeaderboardRow = PublicModelLeaderboardRow> = {
  taskSlug: string;
  displayName: string;
  pathname: string;
  rows: Row[];
};

export const MODEL_LEADERBOARD_TASK_SLUGS = [
  'coding',
  'creative-writing',
  'math',
  'text-to-image',
  'video-generation',
] as const;

const taskOrder = [...MODEL_LEADERBOARD_TASK_SLUGS];

function orderedIndex(values: string[], value: string) {
  const index = values.indexOf(value);
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}

export function modelLeaderboardPathname(taskSlug: string) {
  return `/model-leaderboard/${taskSlug}`;
}

/** Canonical task tabs always include video-generation, even with zero rows. */
export function mergeModelLeaderboardTaskSlugs(observed: Iterable<string> = []): string[] {
  const extras = [...new Set(
    [...observed]
      .map(slug => slug.trim().toLowerCase())
      .filter(Boolean)
      .filter(slug => !taskOrder.includes(slug as (typeof MODEL_LEADERBOARD_TASK_SLUGS)[number])),
  )].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN', { numeric: true }));
  return [...taskOrder, ...extras];
}

/**
 * Shop links require a declared catalog target. Gateway links use the stored
 * family as an explicit filter and never infer a family from the display name.
 */
export function leaderboardRelatedPaths(modelFamily: string): { shopPath: string; gatewayPath: string } {
  const family = modelFamily.trim().toLowerCase();
  if (!family) return { shopPath: '', gatewayPath: '' };
  return {
    shopPath: catalogProductSlugsForTarget(family).length > 0
      ? `/shops?target=${encodeURIComponent(family)}`
      : '',
    gatewayPath: `/llm-gateway?model=${encodeURIComponent(family)}`,
  };
}

function compareTaskSlug(a: string, b: string) {
  const orderDiff = orderedIndex(taskOrder, a) - orderedIndex(taskOrder, b);
  if (orderDiff !== 0) return orderDiff;
  return a.localeCompare(b, 'zh-Hans-CN', { numeric: true });
}

export function buildModelLeaderboardGroups(rows: PublicModelLeaderboardRow[]): ModelLeaderboardGroup[] {
  const groupMap = new Map<string, ModelLeaderboardGroup>();

  for (const row of rows) {
    const existing = groupMap.get(row.taskSlug);
    if (existing) {
      existing.rows.push(row);
      continue;
    }
    groupMap.set(row.taskSlug, {
      taskSlug: row.taskSlug,
      displayName: row.taskSlug,
      pathname: modelLeaderboardPathname(row.taskSlug),
      rows: [row],
    });
  }

  return Array.from(groupMap.values())
    .map(group => ({
      ...group,
      rows: group.rows.sort(compareLeaderboardRank),
    }))
    .sort((a, b) => compareTaskSlug(a.taskSlug, b.taskSlug));
}

export function buildModelLeaderboardGroupsFromSlugs(
  taskSlugs: readonly string[],
  rows: PublicModelLeaderboardRow[],
): ModelLeaderboardGroup[] {
  const byTask = new Map<string, PublicModelLeaderboardRow[]>();
  for (const row of rows) {
    const slug = row.taskSlug.trim().toLowerCase();
    byTask.set(slug, [...(byTask.get(slug) ?? []), row]);
  }
  return mergeModelLeaderboardTaskSlugs(taskSlugs).map(taskSlug => ({
    taskSlug,
    displayName: taskSlug,
    pathname: modelLeaderboardPathname(taskSlug),
    rows: (byTask.get(taskSlug) ?? []).slice().sort(compareLeaderboardRank),
  }));
}

export function buildModelLeaderboardGroupsForActiveTask(
  taskSlugs: readonly string[],
  activeRows: PublicModelLeaderboardRow[],
  activeTaskSlug: string,
): ModelLeaderboardGroup[] {
  const normalizedActiveTask = activeTaskSlug.trim().toLowerCase();
  return mergeModelLeaderboardTaskSlugs(taskSlugs)
    .map(taskSlug => ({
      taskSlug,
      displayName: taskSlug,
      pathname: modelLeaderboardPathname(taskSlug),
      rows: taskSlug === normalizedActiveTask
        ? activeRows.slice().sort(compareLeaderboardRank)
        : [],
    }));
}

function compareLeaderboardRank(a: PublicModelLeaderboardRow, b: PublicModelLeaderboardRow) {
  const groupDiff = evidenceGroupKey(a).localeCompare(evidenceGroupKey(b), 'zh-Hans-CN', { numeric: true });
  return groupDiff || (a.rank ?? Number.MAX_SAFE_INTEGER) - (b.rank ?? Number.MAX_SAFE_INTEGER);
}
