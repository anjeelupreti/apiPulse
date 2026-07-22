import client from './client';

export function listAlertChannels(monitorId) {
  return client.get('/alert-channels/', { params: { monitor: monitorId } }).then((res) => res.data.results);
}

export function createAlertChannel(data) {
  return client.post('/alert-channels/', data).then((res) => res.data);
}

export function deleteAlertChannel(id) {
  return client.delete(`/alert-channels/${id}/`);
}
