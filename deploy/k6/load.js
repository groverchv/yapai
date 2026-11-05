// Load test YAPAI — k6
// Uso:
//   k6 run deploy/k6/load.js                                  # local, escenario smoke
//   BASE_URL=https://api.yapai.com k6 run -e ESCENARIO=load deploy/k6/load.js
//   KIOSCO_TOKEN=<device_token> OWNER_EMAIL=... OWNER_PASSWORD=... para rutas autenticadas
//
// Qué cubre: health, landing de planes, login, endpoints de socio y el path
// caliente del kiosco (config → registro → giro). Los thresholds fallan el
// run si p95 > 800ms o errores > 2%.
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const API = `${BASE}/api/v1`;
const ESC = __ENV.ESCENARIO || 'smoke';
const KIOSCO = __ENV.KIOSCO_TOKEN || '';
const OWNER_EMAIL = __ENV.OWNER_EMAIL || 'owner@demo.com';
const OWNER_PASS = __ENV.OWNER_PASSWORD || 'Owner123!';

export const options = {
  scenarios: ESC === 'load' ? {
    mix: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 30 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 0 },
      ],
    },
  } : {
    smoke: { executor: 'constant-vus', vus: 2, duration: '30s' },
  },
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.02'],
    errors_negocio: ['rate<0.05'],
  },
};

const errores = new Rate('errors_negocio');
const latKiosco = new Trend('latencia_kiosco', true);

let token = null;
function login() {
  const r = http.post(`${API}/auth/login`, JSON.stringify({ email: OWNER_EMAIL, password: OWNER_PASS }),
    { headers: { 'Content-Type': 'application/json' } });
  if (r.status === 200 && r.json('tokens.access_token')) {
    token = r.json('tokens.access_token');
  }
}
const authHeaders = () => ({ headers: { Authorization: `Bearer ${token}` } });

export function setup() {
  login();
  return {};
}

export default function () {
  group('público', () => {
    check(http.get(`${BASE}/health`), { 'health 200': (r) => r.status === 200 });
    check(http.get(`${API}/auth/planes`), { 'planes 200': (r) => r.status === 200 });
  });

  if (!token) login();
  if (token) {
    group('socio', () => {
      const r = http.get(`${API}/socio/plan`, authHeaders());
      errores.add(r.status !== 200);
      const m = http.get(`${API}/socio/metricas`, authHeaders());
      errores.add(m.status !== 200);
    });
  }

  if (KIOSCO) {
    group('kiosco', () => {
      const cfg = http.get(`${API}/kiosco/${KIOSCO}/config`);
      errores.add(cfg.status !== 200 && cfg.status !== 403); // 403 = pantalla expirada (esperado)
      const ci = `${Math.floor(10000000 + Math.random() * 89999999)}`;
      const reg = http.post(`${API}/kiosco/${KIOSCO}/registro`, JSON.stringify({
        nombre: `Load ${ci}`, ci, telefono: `7${ci.slice(1)}`,
      }), { headers: { 'Content-Type': 'application/json' } });
      latKiosco.add(reg.timings.duration);
      // 201 = nuevo · 200 = ya existía · 403 = pantalla expirada · 409 = teléfono con otra CI
      errores.add(reg.status !== 201 && reg.status !== 200 && reg.status !== 403 && reg.status !== 409);
      const clienteId = reg.json('cliente_id');
      if (clienteId && reg.status !== 403) {
        const giro = http.post(`${API}/kiosco/${KIOSCO}/ruleta/girar`, JSON.stringify({
          cliente_id: clienteId,
        }), { headers: { 'Content-Type': 'application/json' } });
        latKiosco.add(giro.timings.duration);
        errores.add(giro.status !== 200 && giro.status !== 400 && giro.status !== 403);
      }
    });
  }
  sleep(0.5);
}
