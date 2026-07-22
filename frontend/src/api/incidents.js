import client from './client';

// filters: { since, until, resolved } - matches incidents/views.py.
// monitorId is optional - omit it to query across all of my monitors
// (used for the dashboard's "ongoing incidents" count)
export function listIncidents(monitorId, filters = {}) {
  const params = { ...filters };
  if (monitorId != null) params.monitor = monitorId;
  return client.get('/incidents/', { params }).then((res) => res.data);
}
