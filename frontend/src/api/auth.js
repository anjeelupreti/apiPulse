import client from './client';

export function login(username, password) {
  return client.post('/auth/token/', { username, password }).then((res) => res.data);
}

export function register(username, email, password) {
  return client
    .post('/accounts/register/', { username, email, password })
    .then((res) => res.data);
}
