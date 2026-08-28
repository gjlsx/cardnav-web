/**
 * 文件说明: 锁定模型排行任务分类、视频生成空态和已声明的内部关联路径。
 */
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  MODEL_LEADERBOARD_TASK_SLUGS,
  buildModelLeaderboardGroupsFromSlugs,
  leaderboardRelatedPaths,
  mergeModelLeaderboardTaskSlugs,
} from '../src/model-leaderboard.js';

test('canonical leaderboard tasks include video-generation even when no rows exist', () => {
  assert.deepEqual([...MODEL_LEADERBOARD_TASK_SLUGS], [
    'coding',
    'creative-writing',
    'math',
    'text-to-image',
    'video-generation',
  ]);
  assert.deepEqual(mergeModelLeaderboardTaskSlugs(['coding']), [...MODEL_LEADERBOARD_TASK_SLUGS]);

  const groups = buildModelLeaderboardGroupsFromSlugs(['coding'], [
    {
      taskSlug: 'coding',
      sourceName: 'CardNav 公开模型排行参考',
      sourceUrl: 'https://cardnav.xyz/model-leaderboard/coding',
      sourceGroupSlug: 'text',
      sourceBoardSlug: 'coding',
      rank: 1,
      modelName: 'gpt-4o',
      modelFamily: 'GPT',
      score: 1456.21,
      sourceId: 'reference-cardnav-leaderboard',
      sampledAt: '2026-08-27T22:55:00.000Z',
      isSample: true,
      fetchedAt: '2026-08-27T22:55:00.000Z',
    },
  ]);
  assert.equal(groups.length, 5);
  assert.equal(groups[0].taskSlug, 'coding');
  assert.equal(groups[0].rows.length, 1);
  const video = groups.find(group => group.taskSlug === 'video-generation');
  assert.ok(video);
  assert.equal(video.rows.length, 0);
});

test('leaderboard related paths use declared families only and do not invent shop mappings', () => {
  assert.deepEqual(leaderboardRelatedPaths('GPT'), {
    shopPath: '/shops?target=gpt',
    gatewayPath: '/llm-gateway?model=gpt',
  });
  assert.deepEqual(leaderboardRelatedPaths('DeepSeek'), {
    shopPath: '',
    gatewayPath: '/llm-gateway?model=deepseek',
  });
  assert.deepEqual(leaderboardRelatedPaths(''), {
    shopPath: '',
    gatewayPath: '',
  });
  assert.deepEqual(leaderboardRelatedPaths('not-a-declared-family'), {
    shopPath: '',
    gatewayPath: '/llm-gateway?model=not-a-declared-family',
  });
});
