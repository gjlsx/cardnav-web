import { readMeasurementConfig } from './measurement-config.js';
import { withMeasurementTransaction } from './store.js';

export const measurementNames = ['ranking_view', 'evidence_open', 'comparison_enter', 'comparison_interact', 'outbound_click'] as const;
export const measurementChannels = ['google', 'qq', 'telegram', 'xiaohongshu', 'x', 'bilibili', 'substack', 'youtube', 'direct-or-unknown'] as const;
const pageKinds = new Set(['leaderboard', 'gateway-list', 'gateway-model', 'gateway-detail']);
const placements = new Set(['natural', 'sponsored', 'unknown']);
const targetKinds = new Set(['official', 'third-party', 'owned', 'unknown']);
const names = new Set<string>(measurementNames);
const channels = new Set<string>(measurementChannels);
const fields = ['eventId', 'sessionId', 'name', 'pageKind', 'entityId', 'sourceId', 'channel', 'placement', 'targetKind'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type MeasurementEvent = {
  eventId: string;
  sessionId: string;
  name: string;
  pageKind: string;
  entityId: string | null;
  sourceId: string | null;
  channel: string | null;
  placement: string | null;
  targetKind: string | null;
};

export type MeasurementReportEvent = Pick<MeasurementEvent, 'sessionId' | 'name'> & {
  channel: string;
  receivedAt: string;
};

export type ExternalMetric = {
  platform: Exclude<(typeof measurementChannels)[number], 'direct-or-unknown'>;
  periodStart: string;
  periodEnd: string;
  timezone: string;
  metric: 'impressions' | 'views' | 'clicks' | 'reads';
  value: number;
  sourceUrl: string;
  exportedAt: string;
};

function optionalString(value: unknown, max = 128): string | null {
  return value === null || value === undefined ? null : typeof value === 'string' && value.length <= max ? value : null;
}

export function validateMeasurementEvent(input: unknown): MeasurementEvent | null {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
  const row = input as Record<string, unknown>;
  if (Object.keys(row).some(key => !fields.includes(key))) return null;
  if (
    typeof row.eventId !== 'string' || !uuid.test(row.eventId)
    || typeof row.sessionId !== 'string' || !uuid.test(row.sessionId)
    || typeof row.name !== 'string' || !names.has(row.name)
    || typeof row.pageKind !== 'string' || !pageKinds.has(row.pageKind)
  ) return null;

  const entityId = optionalString(row.entityId);
  const sourceId = optionalString(row.sourceId);
  const channel = optionalString(row.channel, 32);
  const placement = optionalString(row.placement, 16);
  const targetKind = optionalString(row.targetKind, 16);
  if (
    (row.entityId != null && entityId === null)
    || (row.sourceId != null && sourceId === null)
    || (row.channel != null && (!channel || !channels.has(channel)))
    || (row.placement != null && (!placement || !placements.has(placement)))
    || (row.targetKind != null && (!targetKind || !targetKinds.has(targetKind)))
  ) return null;

  return { eventId: row.eventId, sessionId: row.sessionId, name: row.name, pageKind: row.pageKind, entityId, sourceId, channel, placement, targetKind };
}

export function hongKongDay(date: Date): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Hong_Kong', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(date);
  const value = Object.fromEntries(parts.filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

function affectedRows(result: unknown): number {
  return result && typeof result === 'object' && 'affectedRows' in result
    ? Number((result as { affectedRows: unknown }).affectedRows)
    : 1;
}

export async function recordMeasurementEvent(event: MeasurementEvent, receivedAt: Date): Promise<'accepted' | 'duplicate' | 'limited'> {
  const config = readMeasurementConfig();
  const day = hongKongDay(receivedAt);
  return withMeasurementTransaction(async connection => {
    const [existing] = await connection.query('SELECT event_id FROM measurement_events WHERE event_id = ?', [event.eventId]);
    if (Array.isArray(existing) && existing.length) return 'duplicate';

    await connection.query(
      'INSERT INTO measurement_daily_limits (environment, day_key, accepted_count, limited_count) VALUES (?, ?, 0, 0) ON DUPLICATE KEY UPDATE accepted_count = accepted_count',
      [config.environment, day],
    );
    const [limits] = await connection.query(
      'SELECT accepted_count FROM measurement_daily_limits WHERE environment = ? AND day_key = ? FOR UPDATE',
      [config.environment, day],
    );
    const acceptedCount = Array.isArray(limits) && limits[0] && typeof limits[0] === 'object' && 'accepted_count' in limits[0]
      ? Number(limits[0].accepted_count)
      : 0;
    if (acceptedCount >= config.maxEventsPerDay) {
      await connection.query('UPDATE measurement_daily_limits SET limited_count = limited_count + 1 WHERE environment = ? AND day_key = ?', [config.environment, day]);
      return 'limited';
    }

    const [inserted] = await connection.query(
      'INSERT INTO measurement_events (event_id, session_id, environment, received_at, name, page_kind, entity_id, source_id, channel, placement, target_kind) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE event_id = event_id',
      [event.eventId, event.sessionId, config.environment, receivedAt, event.name, event.pageKind, event.entityId, event.sourceId, event.channel, event.placement, event.targetKind],
    );
    if (affectedRows(inserted) === 0) return 'duplicate';

    await connection.query('UPDATE measurement_daily_limits SET accepted_count = accepted_count + 1 WHERE environment = ? AND day_key = ?', [config.environment, day]);
    return 'accepted';
  });
}

export function hongKongWeekWindow(monday: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(monday)) throw new Error('week start must be an ISO date');
  const date = new Date(`${monday}T00:00:00.000+08:00`);
  if (Number.isNaN(date.getTime()) || date.getUTCDay() !== 0 || hongKongDay(date) !== monday) {
    throw new Error('week start must be a valid Hong Kong Monday');
  }
  return { start: date.toISOString(), end: new Date(date.getTime() + 7 * 86400_000).toISOString() };
}

export function reduceMeasurementReport(events: MeasurementReportEvent[]) {
  const ordered = events.slice().sort((left, right) => left.receivedAt.localeCompare(right.receivedAt));
  const eventsByName: Record<string, number> = {};
  const channelSummary: Record<string, number> = {};
  const sequences = new Map<string, string[]>();
  for (const event of ordered) {
    eventsByName[event.name] = (eventsByName[event.name] || 0) + 1;
    channelSummary[event.channel] = (channelSummary[event.channel] || 0) + 1;
    const sequence = sequences.get(event.sessionId) || [];
    sequence.push(event.name);
    sequences.set(event.sessionId, sequence);
  }
  const pathSessions = [...sequences.values()].filter(sequence => {
    const enter = sequence.indexOf('comparison_enter');
    const interact = sequence.indexOf('comparison_interact', enter + 1);
    return enter !== -1 && interact !== -1 && sequence.indexOf('outbound_click', interact + 1) !== -1;
  }).length;
  return { observedSessions: sequences.size, eventsByName, channelSummary, pathSessions };
}

function isIsoDate(value: unknown): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function validateExternalMetrics(input: unknown): ExternalMetric[] | null {
  if (!Array.isArray(input)) return null;
  const allowed = new Set(['platform', 'periodStart', 'periodEnd', 'timezone', 'metric', 'value', 'sourceUrl', 'exportedAt']);
  const seen = new Set<string>();
  const metrics = new Set(['impressions', 'views', 'clicks', 'reads']);
  const result: ExternalMetric[] = [];
  for (const row of input) {
    if (!row || typeof row !== 'object' || Array.isArray(row) || Object.keys(row).some(key => !allowed.has(key))) return null;
    const value = row as Record<string, unknown>;
    if (
      typeof value.platform !== 'string' || !channels.has(value.platform) || value.platform === 'direct-or-unknown'
      || !isIsoDate(value.periodStart) || !isIsoDate(value.periodEnd) || value.periodStart > value.periodEnd
      || typeof value.timezone !== 'string' || !value.timezone || value.timezone.length > 64
      || typeof value.metric !== 'string' || !metrics.has(value.metric)
      || typeof value.value !== 'number' || !Number.isFinite(value.value) || value.value < 0
      || typeof value.sourceUrl !== 'string' || typeof value.exportedAt !== 'string'
    ) return null;
    let sourceUrl: URL;
    const exportedAt = new Date(value.exportedAt);
    try { sourceUrl = new URL(value.sourceUrl); } catch { return null; }
    if (!['http:', 'https:'].includes(sourceUrl.protocol) || sourceUrl.username || sourceUrl.password || sourceUrl.search || sourceUrl.hash || Number.isNaN(exportedAt.getTime())) return null;
    const key = [value.platform, value.periodStart, value.periodEnd, value.metric, sourceUrl.toString()].join('|');
    if (seen.has(key)) return null;
    seen.add(key);
    result.push({ ...value, platform: value.platform as ExternalMetric['platform'], periodStart: value.periodStart, periodEnd: value.periodEnd, timezone: value.timezone, metric: value.metric as ExternalMetric['metric'], value: value.value, sourceUrl: sourceUrl.toString(), exportedAt: exportedAt.toISOString() });
  }
  return result;
}
