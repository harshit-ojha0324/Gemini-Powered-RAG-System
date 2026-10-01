// The browser calls the backend directly (CORS allows :5173), which works the
// same for local runs and docker-compose, where 8000 is published on the host.
const BASE_URL = 'http://localhost:8000';

// fetch() that resolves to the parsed JSON body and rejects on non-2xx, with
// the backend's FastAPI `detail` message on `error.detail` when there is one.
export default async function api(path, options) {
  const res = await fetch(BASE_URL + path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(`HTTP ${res.status}`), { detail: data.detail });
  return data;
}
