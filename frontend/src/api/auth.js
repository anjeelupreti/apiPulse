import client from './client';

export function login(username, password) {
  return client.post('/auth/token/', { username, password }).then((res) => res.data);
}

export function register(username, email, password) {
  return client
    .post('/accounts/register/', { username, email, password })
    .then((res) => res.data);
}

// idToken is the credential Google's own JS hands back after sign-in -
// same shape response as /auth/token/, so AuthContext treats it identically
export function googleLogin(idToken) {
  return client.post('/auth/google/', { id_token: idToken }).then((res) => res.data);
}
