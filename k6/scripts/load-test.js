import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter, Gauge } from 'k6/metrics';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.4/index.js";

const db_master_role = new Counter('db_master_role');
const db_slave_role = new Counter('db_slave_role');

export function handleSummary(data) {
  return {
    "summary.html": htmlReport(data),
    stdout: textSummary(data, { indent: " ", enableColors: true })
  };

}
export const options = {
  stages: [
    { duration: '20s', target: 20 },  // Ramp-up
    { duration: '20s', target: 50 },  // Normal load
    { duration: '20s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<100'],  // 95% of requests <100ms
  },
};

export default function () {
  const res = http.get('http://nginx/');
  check(res, {
    'is status 200': (r) => r.status === 200,
    'response contains container info': (r) => 
      JSON.parse(r.body).container_info !== undefined,
    'response contains database info': (r) => 
      JSON.parse(r.body).database_info !== undefined,
  });

  if (res.status === 200) {
    const body = JSON.parse(res.body);
    if (body.database_info.role == "SLAVE")
      db_slave_role.add(1)
    if (body.database_info.role == "MASTER")
      db_master_role.add(1)
  }
  
  sleep(0.1);
}