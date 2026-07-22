import client from './client';

export function getMyFlags() {
  return client.get('/flags/mine/').then((res) => res.data);
}
