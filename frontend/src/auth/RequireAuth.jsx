import { Navigate } from 'react-router-dom';

import { useAuth } from './AuthContext';

export function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
