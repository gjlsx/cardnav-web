import 'dotenv/config';
import { initializeMeasurementSchema, type MySqlConnectionConfig } from '../src/database.js';
import { readMeasurementConfig } from '../src/measurement-config.js';
import { hongKongWeekWindow } from '../src/measurement.js';
const config = readMeasurementConfig();
const db: MySqlConnectionConfig = { host: process.env.MYSQL_HOST || '127.0.0.1', port: Number(process.env.MYSQL_PORT || 3306), user: process.env.MYSQL_USER || 'root', password: process.env.MYSQL_PASSWORD, database: process.env.MYSQL_DATABASE || 'ailovemoney' };
const local = ['127.0.0.1', 'localhost', '::1'].includes(db.host);
if (process.argv.includes('--check-config')) console.log(JSON.stringify({ enabled: config.enabled, environment: config.environment, retentionDays: config.retentionDays, maxEventBytes: config.maxEventBytes, maxEventsPerDay: config.maxEventsPerDay, localTarget: local }));
else if (process.argv.includes('--init-schema')) { if (!local) throw new Error('measurement schema initialization requires a local MySQL target'); await initializeMeasurementSchema(db); console.log('measurement schema initialized'); }
else if (process.argv.includes('--week-start')) { const index = process.argv.indexOf('--week-start'); const weekStart = process.argv[index + 1]; const environment = process.argv.includes('--environment') ? process.argv[process.argv.indexOf('--environment') + 1] : config.environment; if (environment !== 'local-test' && environment !== 'production') throw new Error('invalid environment'); const window = hongKongWeekWindow(weekStart); console.log(JSON.stringify({ weekStart, timezone: 'Asia/Hong_Kong', environment, window, observedSessions: null, eventsByName: {}, channelSummary: {}, pathSessions: null, coverage: { status: 'unavailable-without-local-query' }, externalMetrics: [], northStar: null, northStarReason: 'No real operating baseline is established.' })); }
else throw new Error('use --check-config or --init-schema');
