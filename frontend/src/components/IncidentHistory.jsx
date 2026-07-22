import { useEffect, useState } from 'react';

import { listIncidents } from '../api/incidents';
import { StatusDot } from './StatusDot';

const POLL_MS = 10000;

export function IncidentHistory({ monitorId }) {
  const [filters, setFilters] = useState({ resolved: '', since: '', until: '' });
  const [results, setResults] = useState([]);

  function activeFilters() {
    const f = {};
    if (filters.resolved) f.resolved = filters.resolved;
    if (filters.since) f.since = new Date(filters.since).toISOString();
    if (filters.until) f.until = new Date(filters.until).toISOString();
    return f;
  }

  function load() {
    listIncidents(monitorId, activeFilters()).then((data) => setResults(data.results));
  }

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorId, filters]);

  return (
    <section>
      <h2>Incidents</h2>
      <div className="filters">
        <select
          value={filters.resolved}
          onChange={(e) => setFilters({ ...filters, resolved: e.target.value })}
        >
          <option value="">All</option>
          <option value="false">Ongoing only</option>
          <option value="true">Resolved only</option>
        </select>
        <label>
          From <input type="date" value={filters.since} onChange={(e) => setFilters({ ...filters, since: e.target.value })} />
        </label>
        <label>
          To <input type="date" value={filters.until} onChange={(e) => setFilters({ ...filters, until: e.target.value })} />
        </label>
      </div>

      {results.length === 0 ? (
        <p>No incidents - either healthy the whole time, or no data yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Started</th>
              <th>Resolved</th>
              <th>Cause</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {results.map((i) => (
              <tr key={i.id}>
                <td>{new Date(i.started_at).toLocaleString()}</td>
                <td>{i.resolved_at ? new Date(i.resolved_at).toLocaleString() : '-'}</td>
                <td>{i.cause || '-'}</td>
                <td>
                  <StatusDot
                    status={i.is_ongoing ? 'down' : 'up'}
                    upLabel="resolved"
                    downLabel="ongoing"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
