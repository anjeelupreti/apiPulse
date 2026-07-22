import axios from 'axios';

import { getAccessToken, getRefreshToken, setTokens, clearTokens } from '../auth/tokens';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const client = axios.create({ baseURL: BASE_URL });

// plain instance, no interceptors - used only for the refresh call itself,
// so it can't accidentally trigger the 401 handling below and loop forever
const refreshClient = axios.create({ baseURL: BASE_URL });

client.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// if a request comes back 401 (access token expired), try refreshing once
// and replaying the original request. if the refresh itself fails, the
// refresh token is dead too - clear everything and let the app redirect
// to /login (see RequireAuth).
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && getRefreshToken()) {
      original._retry = true;
      try {
        const { data } = await refreshClient.post('/auth/token/refresh/', {
          refresh: getRefreshToken(),
        });
        setTokens({ access: data.access });
        original.headers.Authorization = `Bearer ${data.access}`;
        return client(original);
      } catch {
        clearTokens();
      }
    }
    return Promise.reject(error);
  }
);

export default client;
