import { Navigate, Route, Routes } from 'react-router-dom';

import './App.css';
import { RequireAuth } from './auth/RequireAuth';
import { RequireStaff } from './auth/RequireStaff';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { MonitorsPage } from './pages/MonitorsPage';
import { MonitorDetailPage } from './pages/MonitorDetailPage';
import { AdminPage } from './pages/AdminPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/monitors" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/monitors"
        element={
          <RequireAuth>
            <MonitorsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/monitors/:id"
        element={
          <RequireAuth>
            <MonitorDetailPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <RequireStaff>
              <AdminPage />
            </RequireStaff>
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default App;
