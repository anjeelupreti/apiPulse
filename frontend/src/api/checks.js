import client from './client';

// filters: { since, until, is_up } - all optional, matches the backend's
// query params exactly (see checks/views.py)
export function listChecks(monitorId, filters = {}) {
  const params = { monitor: monitorId, ...filters };
  return client.get('/checks/', { params }).then((res) => res.data);
}

// DRF's pagination "next" is a full URL already, not a page number - so
// this just follows it directly instead of re-deriving params
export function fetchPage(url) {
  return client.get(url).then((res) => res.data);
}
