/**
 * 文件说明: 固定模型榜单来源可展示的使用边界；未知来源默认只允许安全链接，不公开其数值。
 */

export type LeaderboardReferenceUsageStatus = 'reference' | 'link-only' | 'sample';

export type LeaderboardReferencePolicy = {
  sourceId: string;
  sourceUrl: string;
  usageStatus: LeaderboardReferenceUsageStatus;
  evidenceQaPath: string;
};

const cardNavSamplePaths = ['coding', 'creative-writing', 'math', 'text-to-image'];

export const leaderboardReferencePolicies: readonly LeaderboardReferencePolicy[] = cardNavSamplePaths.map(sourceBoardSlug => ({
  sourceId: 'reference-cardnav-leaderboard',
  sourceUrl: `https://cardnav.xyz/model-leaderboard/${sourceBoardSlug}`,
  usageStatus: 'sample',
  evidenceQaPath: 'docs/qa/p1_codex_t09100118.p001.md',
}));

export function findLeaderboardReferencePolicy(sourceId: string, sourceUrl: string): LeaderboardReferencePolicy | null {
  return leaderboardReferencePolicies.find(policy => policy.sourceId === sourceId && policy.sourceUrl === sourceUrl) ?? null;
}
