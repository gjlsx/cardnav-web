import { readMeasurementConfig } from './measurement-config.js';
import { withMeasurementTransaction } from './store.js';

const names = new Set(['ranking_view', 'evidence_open', 'comparison_enter', 'comparison_interact', 'outbound_click']);
const pageKinds = new Set(['leaderboard', 'gateway-list', 'gateway-model', 'gateway-detail']);
const channels = new Set(['google', 'qq', 'telegram', 'xiaohongshu', 'x', 'bilibili', 'substack', 'youtube', 'direct-or-unknown']);
const placements = new Set(['natural', 'sponsored', 'unknown']);
const targetKinds = new Set(['official', 'third-party', 'owned', 'unknown']);
const fields = ['eventId', 'sessionId', 'name', 'pageKind', 'entityId', 'sourceId', 'channel', 'placement', 'targetKind'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export type MeasurementEvent = { eventId: string; sessionId: string; name: string; pageKind: string; entityId: string | null; sourceId: string | null; channel: string | null; placement: string | null; targetKind: string | null };

function optionalString(value: unknown, max = 128): string | null { return value === null || value === undefined ? null : typeof value === 'string' && value.length <= max ? value : null; }
export function validateMeasurementEvent(input: unknown): MeasurementEvent | null {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
  const row = input as Record<string, unknown>;
  if (Object.keys(row).some(key => !fields.includes(key))) return null;
  if (typeof row.eventId !== 'string' || !uuid.test(row.eventId) || typeof row.sessionId !== 'string' || !uuid.test(row.sessionId) || typeof row.name !== 'string' || !names.has(row.name) || typeof row.pageKind !== 'string' || !pageKinds.has(row.pageKind)) return null;
  const entityId = optionalString(row.entityId); const sourceId = optionalString(row.sourceId); const channel = optionalString(row.channel, 32); const placement = optionalString(row.placement, 16); const targetKind = optionalString(row.targetKind, 16);
  if ((row.entityId != null && entityId === null) || (row.sourceId != null && sourceId === null) || (row.channel != null && (!channel || !channels.has(channel))) || (row.placement != null && (!placement || !placements.has(placement))) || (row.targetKind != null && (!targetKind || !targetKinds.has(targetKind)))) return null;
  return { eventId: row.eventId, sessionId: row.sessionId, name: row.name, pageKind: row.pageKind, entityId, sourceId, channel, placement, targetKind };
}

export async function recordMeasurementEvent(event: MeasurementEvent, receivedAt: Date): Promise<'accepted' | 'duplicate' | 'limited'> {
  const config = readMeasurementConfig();
  const day = receivedAt.toISOString().slice(0, 10);
  return withMeasurementTransaction(async connection => {
    const [existing] = await connection.query('SELECT event_id FROM measurement_events WHERE event_id = ? FOR UPDATE', [event.eventId]);
    if (Array.isArray(existing) && existing.length) return 'duplicate';
    await connection.query('INSERT INTO measurement_daily_limits (environment, day_key, accepted_count, limited_count) VALUES (?, ?, 0, 0) ON DUPLICATE KEY UPDATE accepted_count = accepted_count', [config.environment, day]);
    const [limits] = await connection.query('SELECT accepted_count FROM measurement_daily_limits WHERE environment = ? AND day_key = ? FOR UPDATE', [config.environment, day]);
    const acceptedCount = Array.isArray(limits) && limits[0] && typeof limits[0] === 'object' && 'accepted_count' in limits[0] ? Number(limits[0].accepted_count) : 0;
    if (acceptedCount >= config.maxEventsPerDay) { await connection.query('UPDATE measurement_daily_limits SET limited_count = limited_count + 1 WHERE environment = ? AND day_key = ?', [config.environment, day]); return 'limited'; }
    await connection.query('INSERT INTO measurement_events (event_id, session_id, environment, received_at, name, page_kind, entity_id, source_id, channel, placement, target_kind) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [event.eventId, event.sessionId, config.environment, receivedAt, event.name, event.pageKind, event.entityId, event.sourceId, event.channel, event.placement, event.targetKind]);
    await connection.query('UPDATE measurement_daily_limits SET accepted_count = accepted_count + 1 WHERE environment = ? AND day_key = ?', [config.environment, day]);
    return 'accepted';
  });
}
