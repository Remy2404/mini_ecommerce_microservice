import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    product_reads: {
      executor: 'constant-vus',
      vus: Number(__ENV.K6_PRODUCT_VUS || 5),
      duration: __ENV.K6_PRODUCT_DURATION || '30s',
      exec: 'productReads',
    },
    cart_and_orders: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.K6_ORDER_RATE || 2),
      timeUnit: '1s',
      duration: __ENV.K6_ORDER_DURATION || '30s',
      preAllocatedVUs: 10,
      exec: 'cartAndOrders',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<750'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.AUTH_TOKEN || '';
const USER_ID = __ENV.USER_ID || 'load-user';
const PRODUCT_ID = __ENV.PRODUCT_ID || '00000000-0000-0000-0000-000000000001';

function headers() {
  return TOKEN
    ? { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };
}

export function productReads() {
  const response = http.get(`${BASE_URL}/api/v1/products`, { headers: headers() });
  check(response, {
    'product listing is not a server error': (res) => res.status < 500,
  });
  sleep(1);
}

export function cartAndOrders() {
  const addItem = http.post(
    `${BASE_URL}/api/v1/cart/items`,
    JSON.stringify({
      user_id: USER_ID,
      product_id: PRODUCT_ID,
      quantity: 1,
    }),
    { headers: headers() },
  );
  check(addItem, {
    'cart add is accepted or validation-safe': (res) =>
      [200, 201, 400, 401, 403, 404, 422].includes(res.status),
  });

  const createOrder = http.post(
    `${BASE_URL}/api/v1/orders`,
    JSON.stringify({ user_id: USER_ID }),
    { headers: headers() },
  );
  check(createOrder, {
    'order create is accepted or validation-safe': (res) =>
      [200, 201, 400, 401, 403, 404, 422].includes(res.status),
  });
}
