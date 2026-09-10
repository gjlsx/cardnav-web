import 'dotenv/config';
import { readFile, stat } from 'node:fs/promises';
import { initializeMeasurementSchema, type MySqlConnectionConfig } from '../src/database.js';
import { hongKongDay, hongKongWeekWindow, reduceMeasurementReport, validateExternalMetrics } from '../src/measurement.js';
import { readMeasurementConfig } from '../src/measurement-config.js';
import { cleanupMeasurementData, loadMeasurementDailyLimits, loadMeasurementEvents } from '../src/store.js';

export const MAX_EXTERNAL_REPORT_BYTES = 1024 * 1024;

const config = readMeasurementConfig();
const db: MySqlConnectionConfig = {
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE || 'ailovemoney',
};
const localTarget = ['127.0.0.1', 'localhost', '::1'].includes(db.host);

function flagValue(args: string[], flag: string): string | undefined {
  const index = args.indexOf(flag);
  if (index === -1) return undefined;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error(`${flag} requires a value`);
  return value;
}

function selectedEnvironment(value: string) {
  if (value !== 'local-test' && value !== 'production') throw new Error('invalid environment');
  return value;
}

function requireLocalTarget() {
  if (!localTarget) throw new Error('measurement commands require a local MySQL target');
}

export async function readExternalMetrics(filePath: string) {
  const info = await stat(filePath);
  if (info.size > MAX_EXTERNAL_REPORT_BYTES) throw new Error('external report exceeds 1 MiB');
  const parsed = JSON.parse(await readFile(filePath, 'utf8'));
  const metrics = validateExternalMetrics(parsed);
  if (!metrics) throw new Error('external report has an invalid or duplicate metric row');
  return metrics;
}

async function report(args: string[]) {
  requireLocalTarget();
  const weekStart = flagValue(args, '--week-start');
  if (!weekStart) throw new Error('--week-start is required');
  const environment = selectedEnvironment(flagValue(args, '--environment') || config.environment);
  const window = hongKongWeekWindow(weekStart);
  const [events, dailyLimits] = await Promise.all([
    loadMeasurementEvents(window.start, window.end, environment),
    loadMeasurementDailyLimits(weekStart, hongKongDay(new Date(window.end)), environment),
  ]);
  const externalFile = flagValue(args, '--external-file');
  const externalMetrics = externalFile ? await readExternalMetrics(externalFile) : [];
  const summary = reduceMeasurementReport(events);
  console.log(JSON.stringify({
    weekStart,
    timezone: 'Asia/Hong_Kong',
    environment,
    ...summary,
    coverage: {
      receivedEvents: events.length,
      earliestReceivedAt: events[0]?.receivedAt || null,
      latestReceivedAt: events.at(-1)?.receivedAt || null,
      limitedEvents: dailyLimits.reduce((total, row) => total + row.limitedCount, 0),
      status: environment === 'local-test' ? 'synthetic-or-local-test' : 'unknown',
      totalVisitors: 'unknown',
      blockedOrOptedOut: 'unknown',
    },
    externalMetrics: externalMetrics.map(metric => ({ ...metric, verification: 'user-provided-unverified' })),
    northStar: null,
    northStarReason: 'No real operating baseline is established.',
  }));
}

async function cleanup(args: string[]) {
  requireLocalTarget();
  const environment = selectedEnvironment(flagValue(args, '--environment') || config.environment);
  const apply = args.includes('--apply');
  if (apply && args.includes('--dry-run')) throw new Error('choose either --dry-run or --apply');
  const cutoff = new Date(Date.now() - config.retentionDays * 86400_000);
  const result = await cleanupMeasurementData(cutoff.toISOString(), hongKongDay(cutoff), environment, apply);
  console.log(JSON.stringify({ environment, cutoff: cutoff.toISOString(), mode: apply ? 'apply' : 'dry-run', ...result }));
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--check-config')) {
    console.log(JSON.stringify({ enabled: config.enabled, environment: config.environment, retentionDays: config.retentionDays, maxEventBytes: config.maxEventBytes, maxEventsPerDay: config.maxEventsPerDay, localTarget }));
  } else if (args.includes('--init-schema')) {
    requireLocalTarget();
    await initializeMeasurementSchema(db);
    console.log('measurement schema initialized');
  } else if (args.includes('--cleanup')) {
    await cleanup(args);
  } else if (args.includes('--week-start')) {
    await report(args);
  } else {
    throw new Error('use --check-config, --init-schema, --week-start, or --cleanup');
  }
}

if (process.argv[1]?.replace(/\\/g, '/').endsWith('/measurement-report.ts')) void main();
