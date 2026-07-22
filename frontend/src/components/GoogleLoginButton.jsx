import { GoogleLogin } from '@react-oauth/google';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';

// same button works for both login and signup - the backend does
// get_or_create on the Google account's email, so there's no separate
// "register with Google" step
export function GoogleLoginButton() {
  const { loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  async function handleSuccess(credentialResponse) {
    setError('');
    try {
      await loginWithGoogle(credentialResponse.credential);
      navigate('/monitors');
    } catch {
      setError('Google sign-in failed.');
    }
  }

  return (
    <div className="google-login">
      <GoogleLogin onSuccess={handleSuccess} onError={() => setError('Google sign-in failed.')} />
      {error && <p className="error">{error}</p>}
    </div>
  );
}
