// just localStorage, wrapped so the rest of the app never touches the key
// names directly. not worried about XSS-vs-localStorage tradeoffs yet -
// something to revisit before this is a real production app.

const ACCESS_KEY = 'pulsewatch_access';
const REFRESH_KEY = 'pulsewatch_refresh';

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens({ access, refresh }) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh);
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
