import 'dotenv/config';
import { initializeMeasurementSchema, type MySqlConnectionConfig } from '../src/database.js';
import { readMeasurementConfig } from '../src/measurement-config.js';
const config = readMeasurementConfig();
const db: MySqlConnectionConfig = { host: process.env.MYSQL_HOST || '127.0.0.1', port: Number(process.env.MYSQL_PORT || 3306), user: process.env.MYSQL_USER || 'root', password: process.env.MYSQL_PASSWORD, database: process.env.MYSQL_DATABASE || 'ailovemoney' };
const local = ['127.0.0.1', 'localhost', '::1'].includes(db.host);
if (process.argv.includes('--check-config')) console.log(JSON.stringify({ enabled: config.enabled, environment: config.environment, retentionDays: config.retentionDays, maxEventBytes: config.maxEventBytes, maxEventsPerDay: config.maxEventsPerDay, localTarget: local }));
else if (process.argv.includes('--init-schema')) { if (!local) throw new Error('measurement schema initialization requires a local MySQL target'); await initializeMeasurementSchema(db); console.log('measurement schema initialized'); }
else throw new Error('use --check-config or --init-schema');
