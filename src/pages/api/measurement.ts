import type { APIRoute } from 'astro';
import { readMeasurementConfig } from '../../measurement-config.js';
import { recordMeasurementEvent, validateMeasurementEvent } from '../../measurement.js';

const headers = { 'cache-control': 'no-store' };
export const POST: APIRoute = async ({ request }) => {
  let config;
  try { config = readMeasurementConfig(); } catch { return new Response(null, { status: 503, headers }); }
  if (!config.enabled) return new Response(null, { status: 204, headers });
  const origin = request.headers.get('origin');
  const site = new URL(request.url).origin;
  if (origin !== site || (request.headers.get('sec-fetch-site') && request.headers.get('sec-fetch-site') !== 'same-origin')) return new Response(null, { status: 403, headers });
  const reader = request.body?.getReader(); let size = 0; const chunks: Uint8Array[] = [];
  if (!reader) return new Response(null, { status: 400, headers });
  try { for (;;) { const part = await reader.read(); if (part.done) break; size += part.value.byteLength; if (size > config.maxEventBytes) return new Response(null, { status: 413, headers }); chunks.push(part.value); } } catch { return new Response(null, { status: 400, headers }); }
  const raw = new TextDecoder().decode(Buffer.concat(chunks));
  let event; try { event = validateMeasurementEvent(JSON.parse(raw)); } catch { event = null; }
  if (!event) return new Response(null, { status: 400, headers });
  try { const result = await recordMeasurementEvent(event, new Date()); return new Response(null, { status: result === 'accepted' ? 202 : result === 'limited' ? 429 : 204, headers }); } catch { return new Response(null, { status: 503, headers }); }
};
