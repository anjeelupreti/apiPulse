import { createContext, useContext, useEffect, useState } from 'react';

import { getMyFlags } from '../api/flags';
import { useAuth } from '../auth/AuthContext';

const FlagsContext = createContext({ flags: {} });

// fetches once per login, not polled - flags don't need to be real-time,
// and re-fetching on every render would just be extra requests for
// something that basically never changes mid-session
export function FlagsProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [flags, setFlags] = useState({});

  useEffect(() => {
    if (isAuthenticated) {
      getMyFlags().then(setFlags);
    } else {
      setFlags({});
    }
  }, [isAuthenticated]);

  return <FlagsContext.Provider value={{ flags }}>{children}</FlagsContext.Provider>;
}

export function useFlags() {
  return useContext(FlagsContext);
}
