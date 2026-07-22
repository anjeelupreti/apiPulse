import client from './client';

export function getStats() {
  return client.get('/admin/stats/').then((res) => res.data);
}

export function listUsers() {
  return client.get('/admin/users/').then((res) => res.data.results);
}

export function updateUser(id, data) {
  return client.patch(`/admin/users/${id}/`, data).then((res) => res.data);
}

export function listFlags() {
  return client.get('/admin/flags/').then((res) => res.data.results);
}

export function createFlag(data) {
  return client.post('/admin/flags/', data).then((res) => res.data);
}

export function updateFlag(id, data) {
  return client.patch(`/admin/flags/${id}/`, data).then((res) => res.data);
}

export function deleteFlag(id) {
  return client.delete(`/admin/flags/${id}/`);
}
