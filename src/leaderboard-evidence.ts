/**
 * 文件说明: 规范模型榜单引用分数、公开证据链接和展示边界，不把来源数值解释为本站评分。
 */
import { isIP } from 'node:net';
import { findLeaderboardReferencePolicy } from './leaderboard-reference-policy.js';
import type { PublicModelLeaderboardRow } from './store.js';

export type LeaderboardEvidenceStatus = 'sample' | 'reference' | 'unverified';

export type LeaderboardEvidence = {
  row: PublicModelLeaderboardRow;
  sourceLabel: string;
  sourceUrl: string | null;
  score: number | null;
  rank: number | null;
  displayScore: number | null;
  displayRank: number | null;
  sampledAt: string;
  status: LeaderboardEvidenceStatus;
  groupKey: string;
  methodStatus: 'not-recorded';
  evidenceQaPath: string | null;
};

export function parseReferenceScore(value: unknown): number | null {
  if (typeof value !== 'number' && typeof value !== 'string') return null;
  if (typeof value === 'string' && !value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseReferenceRank(value: unknown): number | null {
  const parsed = parseReferenceScore(value);
  return parsed !== null && Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function isPrivateIp(hostname: string) {
  const normalized = hostname.toLowerCase().replace(/^\[|\]$/g, '');
  const ipVersion = isIP(normalized);
  if (ipVersion === 4) {
    const [first, second] = normalized.split('.').map(Number);
    return first === 10 || first === 127 || first === 0 || first === 169 && second === 254 || first === 172 && second >= 16 && second <= 31 || first === 192 && second === 168;
  }
  if (ipVersion === 6) return normalized === '::1' || normalized.startsWith('fc') || normalized.startsWith('fd') || normalized.startsWith('fe80:');
  return normalized === 'localhost' || normalized.endsWith('.localhost') || normalized.endsWith('.local');
}

export function safeEvidenceUrl(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value);
    if ((url.protocol !== 'http:' && url.protocol !== 'https:') || url.username || url.password || isPrivateIp(url.hostname)) return null;
    return url.toString();
  } catch {
    return null;
  }
}

export function evidenceGroupKey(row: Pick<PublicModelLeaderboardRow, 'sourceId' | 'sourceUrl' | 'sourceGroupSlug' | 'sourceBoardSlug' | 'taskSlug' | 'sampledAt'>): string {
  return JSON.stringify([row.sourceId, row.sourceUrl, row.sourceGroupSlug, row.sourceBoardSlug, row.taskSlug, row.sampledAt]);
}

export function buildReferenceEvidence(row: PublicModelLeaderboardRow): LeaderboardEvidence {
  const policy = findLeaderboardReferencePolicy(row.sourceId, row.sourceUrl);
  const status: LeaderboardEvidenceStatus = policy?.usageStatus === 'sample' && row.isSample
    ? 'sample'
    : policy?.usageStatus === 'reference' ? 'reference' : 'unverified';
  const score = parseReferenceScore(row.score);
  const rank = parseReferenceRank(row.rank);
  const mayDisplayNumbers = status === 'sample' || status === 'reference';
  return {
    row,
    sourceLabel: row.sourceName.trim() || row.sourceId || 'External reference',
    sourceUrl: safeEvidenceUrl(row.sourceUrl),
    score,
    rank,
    displayScore: mayDisplayNumbers ? score : null,
    displayRank: mayDisplayNumbers ? rank : null,
    sampledAt: row.sampledAt,
    status,
    groupKey: evidenceGroupKey(row),
    methodStatus: 'not-recorded',
    evidenceQaPath: policy?.evidenceQaPath ?? null,
  };
}
