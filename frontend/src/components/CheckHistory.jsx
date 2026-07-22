import { useEffect, useState } from 'react';

import { listChecks, fetchPage } from '../api/checks';
import { useFlags } from '../flags/FlagsContext';
import { ResponseTimeChart } from './ResponseTimeChart';
import { StatusDot } from './StatusDot';

const POLL_MS = 10000;

function SslBadge({ sslValid, sslExpiresAt }) {
  if (sslValid == null) {
    return <span className="ssl-badge ssl-badge--na">n/a</span>;
  }
  if (!sslValid) {
    return <span className="ssl-badge ssl-badge--invalid">invalid</span>;
  }
  return (
    <span className="ssl-badge ssl-badge--valid">
      valid{sslExpiresAt ? ` · expires ${new Date(sslExpiresAt).toLocaleDateString()}` : ''}
    </span>
  );
}

export function CheckHistory({ monitorId }) {
  const { flags } = useFlags();
  const [filters, setFilters] = useState({ is_up: '', since: '', until: '' });
  const [results, setResults] = useState([]);
  const [next, setNext] = useState(null);
  // once you've paged past "recent", auto-refresh would yank you back to
  // page 1 every 10s - pause it instead until you go back to recent
  const [viewingMore, setViewingMore] = useState(false);

  function activeFilters() {
    const f = {};
    if (filters.is_up) f.is_up = filters.is_up;
    if (filters.since) f.since = new Date(filters.since).toISOString();
    if (filters.until) f.until = new Date(filters.until).toISOString();
    return f;
  }

  function loadRecent() {
    listChecks(monitorId, activeFilters()).then((data) => {
      setResults(data.results);
      setNext(data.next);
      setViewingMore(false);
    });
  }

  useEffect(() => {
    loadRecent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorId, filters]);

  useEffect(() => {
    if (viewingMore) return; // paused
    const id = setInterval(loadRecent, POLL_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewingMore, monitorId, filters]);

  function loadMore() {
    fetchPage(next).then((data) => {
      setResults((prev) => [...prev, ...data.results]);
      setNext(data.next);
      setViewingMore(true);
    });
  }

  return (
    <section>
      <h2>Checks</h2>
      <div className="filters">
        <select
          value={filters.is_up}
          onChange={(e) => setFilters({ ...filters, is_up: e.target.value })}
        >
          <option value="">All</option>
          <option value="true">Up only</option>
          <option value="false">Down only</option>
        </select>
        <label>
          From <input type="date" value={filters.since} onChange={(e) => setFilters({ ...filters, since: e.target.value })} />
        </label>
        <label>
          To <input type="date" value={filters.until} onChange={(e) => setFilters({ ...filters, until: e.target.value })} />
        </label>
        {viewingMore && <button onClick={loadRecent}>Back to recent</button>}
      </div>

      {results.length > 0 && flags['response-time-chart'] && <ResponseTimeChart checks={results} />}

      {results.length === 0 ? (
        <p>No checks yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Status</th>
              <th>HTTP code</th>
              <th>Response time</th>
              <th>SSL</th>
              <th>Failure reason</th>
            </tr>
          </thead>
          <tbody>
            {results.map((c) => (
              <tr key={c.id}>
                <td>{new Date(c.checked_at).toLocaleString()}</td>
                <td>
                  <StatusDot status={c.is_up ? 'up' : 'down'} />
                </td>
                <td>{c.status_code ?? '-'}</td>
                <td>{c.response_time_ms != null ? `${c.response_time_ms} ms` : '-'}</td>
                <td>
                  <SslBadge sslValid={c.ssl_valid} sslExpiresAt={c.ssl_expires_at} />
                </td>
                <td>{c.failure_reason || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {next && <button onClick={loadMore}>Load more</button>}
    </section>
  );
}
