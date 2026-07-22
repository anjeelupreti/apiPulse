import { Navigate } from 'react-router-dom';

import { useAuth } from './AuthContext';

export function RequireStaff({ children }) {
  const { user } = useAuth();
  // user is null until the /me/ fetch resolves - don't redirect a real
  // staff member away just because that hasn't landed yet on first paint
  if (user === null) {
    return <p>Loading...</p>;
  }
  if (!user.is_staff) {
    return <Navigate to="/monitors" replace />;
  }
  return children;
}
