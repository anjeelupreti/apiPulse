import client from './client';

export function listMonitors() {
  return client.get('/monitors/').then((res) => res.data.results);
}

export function createMonitor(monitor) {
  return client.post('/monitors/', monitor).then((res) => res.data);
}

export function deleteMonitor(id) {
  return client.delete(`/monitors/${id}/`);
}
