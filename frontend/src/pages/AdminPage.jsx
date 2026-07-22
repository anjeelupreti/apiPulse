import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getStats, listUsers, updateUser, listFlags, createFlag, updateFlag, deleteFlag } from '../api/admin';

const emptyFlagForm = { key: '', description: '' };

export function AdminPage() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [flags, setFlags] = useState([]);
  const [flagForm, setFlagForm] = useState(emptyFlagForm);
  const [error, setError] = useState('');

  function refresh() {
    return Promise.all([
      getStats().then(setStats),
      listUsers().then(setUsers),
      listFlags().then(setFlags),
    ]);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function toggleUserActive(user) {
    await updateUser(user.id, { is_active: !user.is_active });
    await refresh();
  }

  async function toggleFlagGlobal(flag) {
    await updateFlag(flag.id, { is_globally_enabled: !flag.is_globally_enabled });
    await refresh();
  }

  async function handleCreateFlag(e) {
    e.preventDefault();
    setError('');
    try {
      await createFlag(flagForm);
      setFlagForm(emptyFlagForm);
      await refresh();
    } catch {
      setError('Could not create that flag - key must be a unique slug.');
    }
  }

  async function handleDeleteFlag(id) {
    await deleteFlag(id);
    await refresh();
  }

  if (!stats) return <p>Loading...</p>;

  return (
    <div className="admin-page">
      <p>
        <Link to="/monitors">&larr; back to monitors</Link>
      </p>
      <h1>Admin</h1>

      <div className="metrics-row">
        <div className="card stat-tile">
          <span className="stat-tile__label">Users</span>
          <span className="stat-tile__value">{stats.total_users}</span>
        </div>
        <div className="card stat-tile">
          <span className="stat-tile__label">Monitors</span>
          <span className="stat-tile__value">{stats.total_monitors}</span>
        </div>
        <div className={`card stat-tile ${stats.total_ongoing_incidents > 0 ? 'stat-tile--critical' : ''}`}>
          <span className="stat-tile__label">Ongoing incidents</span>
          <span className="stat-tile__value">{stats.total_ongoing_incidents}</span>
        </div>
        <div className="card stat-tile">
          <span className="stat-tile__label">Feature flags</span>
          <span className="stat-tile__value">{stats.total_feature_flags}</span>
        </div>
      </div>

      <section>
        <h2>Users</h2>
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Monitors</th>
              <th>Staff</th>
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.username}</td>
                <td>{u.email}</td>
                <td>{u.monitor_count}</td>
                <td>{u.is_staff ? 'yes' : 'no'}</td>
                <td>{u.is_active ? 'yes' : 'no'}</td>
                <td>
                  <button onClick={() => toggleUserActive(u)}>
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Feature flags</h2>
        <form onSubmit={handleCreateFlag} className="monitor-form">
          <input
            placeholder="key (e.g. new-thing)"
            value={flagForm.key}
            onChange={(e) => setFlagForm({ ...flagForm, key: e.target.value })}
            required
          />
          <input
            placeholder="description"
            value={flagForm.description}
            onChange={(e) => setFlagForm({ ...flagForm, description: e.target.value })}
          />
          <button type="submit">Add flag</button>
        </form>
        {error && <p className="error">{error}</p>}

        <table>
          <thead>
            <tr>
              <th>Key</th>
              <th>Description</th>
              <th>Globally enabled</th>
              <th>Per-user grants</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {flags.map((f) => (
              <tr key={f.id}>
                <td>{f.key}</td>
                <td>{f.description || '-'}</td>
                <td>{f.is_globally_enabled ? 'yes' : 'no'}</td>
                <td>{f.enabled_for_users.length}</td>
                <td>
                  <button onClick={() => toggleFlagGlobal(f)}>
                    {f.is_globally_enabled ? 'Turn off' : 'Turn on'}
                  </button>
                  <button onClick={() => handleDeleteFlag(f.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="hint">
          Per-user grants (enabling a flag for one specific user while it's globally off) aren't
          editable here yet - use Django admin (/admin/) for that until this panel grows a picker.
        </p>
      </section>
    </div>
  );
}
