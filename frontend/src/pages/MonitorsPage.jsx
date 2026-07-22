import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listMonitors, createMonitor, deleteMonitor } from '../api/monitors';
import { listIncidents } from '../api/incidents';
import { useAuth } from '../auth/AuthContext';
import { MetricsBar } from '../components/MetricsBar';
import { StatusDot } from '../components/StatusDot';

const emptyForm = {
  name: '',
  url: '',
  expected_status_code: 200,
  auth_type: 'NONE',
  auth_header_name: '',
  auth_credential: '',
};

export function MonitorsPage() {
  const { logout } = useAuth();
  const [monitors, setMonitors] = useState([]);
  const [ongoingIncidents, setOngoingIncidents] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  function refresh() {
    return Promise.all([
      listMonitors().then(setMonitors),
      listIncidents(null, { resolved: 'false' }).then((data) => setOngoingIncidents(data.count)),
    ]);
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await createMonitor(form);
      setForm(emptyForm);
      await refresh();
    } catch {
      setError('Could not create monitor - check the URL is valid.');
    }
  }

  async function handleDelete(id) {
    await deleteMonitor(id);
    await refresh();
  }

  return (
    <div className="monitors-page">
      <header>
        <h1>Monitors</h1>
        <button onClick={logout}>Log out</button>
      </header>

      {!loading && <MetricsBar monitors={monitors} ongoingIncidents={ongoingIncidents} />}

      <form onSubmit={handleCreate} className="monitor-form">
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="https://api.example.com/health"
          value={form.url}
          onChange={(e) => setForm({ ...form, url: e.target.value })}
          required
        />
        <input
          type="number"
          title="Expected status code"
          value={form.expected_status_code}
          onChange={(e) => setForm({ ...form, expected_status_code: Number(e.target.value) })}
        />

        <details className="auth-fields">
          <summary>Protected endpoint? (optional)</summary>
          <div className="auth-fields__body">
            <select
              value={form.auth_type}
              onChange={(e) => setForm({ ...form, auth_type: e.target.value })}
            >
              <option value="NONE">No auth</option>
              <option value="BASIC">HTTP Basic (username:password)</option>
              <option value="BEARER">Bearer token</option>
              <option value="API_KEY">API key header</option>
            </select>
            {form.auth_type === 'API_KEY' && (
              <input
                placeholder="Header name, e.g. X-API-Key"
                value={form.auth_header_name}
                onChange={(e) => setForm({ ...form, auth_header_name: e.target.value })}
              />
            )}
            {form.auth_type !== 'NONE' && (
              <input
                type="password"
                placeholder={form.auth_type === 'BASIC' ? 'username:password' : 'token / key value'}
                value={form.auth_credential}
                onChange={(e) => setForm({ ...form, auth_credential: e.target.value })}
              />
            )}
          </div>
        </details>

        <button type="submit">Add monitor</button>
      </form>
      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : monitors.length === 0 ? (
        <p>No monitors yet - add one above.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>URL</th>
              <th>Expected status</th>
              <th>Last checked</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {monitors.map((m) => (
              <tr key={m.id}>
                <td>
                  <Link to={`/monitors/${m.id}`}>{m.name}</Link>
                </td>
                <td>
                  <StatusDot status={m.current_status} />
                </td>
                <td>{m.url}</td>
                <td>{m.expected_status_code}</td>
                <td>{m.last_checked_at ? new Date(m.last_checked_at).toLocaleString() : 'never'}</td>
                <td>
                  <button onClick={() => handleDelete(m.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
