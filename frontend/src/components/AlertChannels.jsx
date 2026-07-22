import { useEffect, useState } from 'react';

import { listAlertChannels, createAlertChannel, deleteAlertChannel } from '../api/alerts';

const TARGET_PLACEHOLDERS = {
  EMAIL: 'you@example.com',
  SLACK: 'https://hooks.slack.com/services/...',
  WEBHOOK: 'https://example.com/my-webhook',
};

const emptyForm = { channel_type: 'EMAIL', target: '' };

export function AlertChannels({ monitorId }) {
  const [channels, setChannels] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState('');

  function refresh() {
    return listAlertChannels(monitorId).then(setChannels);
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorId]);

  async function handleCreate(e) {
    e.preventDefault();
    setError('');
    try {
      await createAlertChannel({ monitor: monitorId, ...form });
      setForm(emptyForm);
      await refresh();
    } catch {
      setError('Could not add that channel - check the target is valid.');
    }
  }

  async function handleDelete(id) {
    await deleteAlertChannel(id);
    await refresh();
  }

  return (
    <section>
      <h2>Alerts</h2>
      <form onSubmit={handleCreate} className="monitor-form">
        <select
          value={form.channel_type}
          onChange={(e) => setForm({ ...form, channel_type: e.target.value })}
        >
          <option value="EMAIL">Email</option>
          <option value="SLACK">Slack</option>
          <option value="WEBHOOK">Webhook</option>
        </select>
        <input
          placeholder={TARGET_PLACEHOLDERS[form.channel_type]}
          value={form.target}
          onChange={(e) => setForm({ ...form, target: e.target.value })}
          required
        />
        <button type="submit">Add alert channel</button>
      </form>
      {error && <p className="error">{error}</p>}

      {channels.length === 0 ? (
        <p>No alert channels yet - add one above to get notified when this monitor goes down.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Target</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {channels.map((c) => (
              <tr key={c.id}>
                <td>{c.channel_type}</td>
                <td>{c.target}</td>
                <td>
                  <button onClick={() => handleDelete(c.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
