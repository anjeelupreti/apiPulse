import { createContext, useContext, useEffect, useState } from 'react';

import * as authApi from '../api/auth';
import { getAccessToken, setTokens, clearTokens } from './tokens';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // just "do I have an access token right now" - not decoding/validating
  // the JWT client-side, the API is the source of truth on whether it's
  // actually still valid (a stale token just gets a 401 on first use)
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(getAccessToken()));
  // the profile (username/email/is_staff) - fetched separately from the
  // JWT itself, same reasoning as flags: don't decode the token
  // client-side, ask the API who I actually am
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      authApi.getMe().then(setUser);
    } else {
      setUser(null);
    }
  }, [isAuthenticated]);

  async function login(username, password) {
    const data = await authApi.login(username, password);
    setTokens(data);
    setIsAuthenticated(true);
  }

  async function register(username, email, password) {
    await authApi.register(username, email, password);
    await login(username, password);
  }

  async function loginWithGoogle(idToken) {
    const data = await authApi.googleLogin(idToken);
    setTokens(data);
    setIsAuthenticated(true);
  }

  function logout() {
    clearTokens();
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, register, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
