import client from './client';

// filters: { since, until, resolved } - matches incidents/views.py
export function listIncidents(monitorId, filters = {}) {
  const params = { monitor: monitorId, ...filters };
  return client.get('/incidents/', { params }).then((res) => res.data);
}
