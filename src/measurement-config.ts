export type MeasurementConfig = { enabled: boolean; environment: 'local-test' | 'production'; retentionDays: number; maxEventBytes: number; maxEventsPerDay: number };

function positiveInteger(env: Record<string, string | undefined>, key: string, fallback: number) {
  const value = env[key];
  if (value === undefined || value === '') return fallback;
  if (!/^\d+$/.test(value) || Number(value) < 1 || !Number.isSafeInteger(Number(value))) throw new Error(`${key} must be a positive integer`);
  return Number(value);
}

export function readMeasurementConfig(env: Record<string, string | undefined> = process.env): MeasurementConfig {
  const enabledValue = env.MEASUREMENT_ENABLED;
  if (enabledValue !== undefined && enabledValue !== '' && enabledValue !== 'true' && enabledValue !== 'false') throw new Error('MEASUREMENT_ENABLED must be true or false');
  const environment = env.MEASUREMENT_ENVIRONMENT || 'local-test';
  if (environment !== 'local-test' && environment !== 'production') throw new Error('MEASUREMENT_ENVIRONMENT must be local-test or production');
  return { enabled: enabledValue === 'true', environment, retentionDays: positiveInteger(env, 'MEASUREMENT_RETENTION_DAYS', 14), maxEventBytes: positiveInteger(env, 'MEASUREMENT_MAX_EVENT_BYTES', 2048), maxEventsPerDay: positiveInteger(env, 'MEASUREMENT_MAX_EVENTS_PER_DAY', 10000) };
}
