import http from 'k6/http';
import { check } from 'k6';

// Generic load scenario. Override via env:
//   BASE_URL (default http://127.0.0.1:8005)
//   REQ_PATH (default /health)
//   METHOD   (default GET)
//   VUS      (target virtual users)
//   WARMUP_S (default 30)  ramp-up / warm-up duration
//   HOLD_S   (default 60)  sustained load duration

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8005';
const REQ_PATH = __ENV.REQ_PATH || '/health';
const METHOD = __ENV.METHOD || 'GET';
const VUS = Number(__ENV.VUS || 10);
const WARMUP_S = __ENV.WARMUP_S || '30s';
const HOLD_S = __ENV.HOLD_S || '60s';

export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  scenarios: {
    load: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: WARMUP_S, target: VUS },
        { duration: HOLD_S, target: VUS },
        { duration: '10s', target: 0 },
      ],
    },
  },
  thresholds: {},
};

export default function () {
  const res = http.request(METHOD, `${BASE_URL}${REQ_PATH}`);
  check(res, {
    'status 2xx/3xx': (r) => r.status >= 200 && r.status < 400,
  });
}
