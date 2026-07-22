import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getMonitor } from '../api/monitors';
import { CheckHistory } from '../components/CheckHistory';
import { IncidentHistory } from '../components/IncidentHistory';
import { StatusDot } from '../components/StatusDot';

export function MonitorDetailPage() {
  const { id } = useParams();
  const [monitor, setMonitor] = useState(null);

  useEffect(() => {
    getMonitor(id).then(setMonitor);
  }, [id]);

  if (!monitor) return <p>Loading...</p>;

  return (
    <div className="monitor-detail-page">
      <p>
        <Link to="/monitors">&larr; back to monitors</Link>
      </p>
      <h1>{monitor.name}</h1>
      <StatusDot status={monitor.current_status} />
      <dl>
        <dt>URL</dt>
        <dd>{monitor.url}</dd>
        <dt>Expected status</dt>
        <dd>{monitor.expected_status_code}</dd>
        <dt>Check interval</dt>
        <dd>{monitor.check_interval_seconds}s</dd>
        <dt>Last checked</dt>
        <dd>{monitor.last_checked_at ? new Date(monitor.last_checked_at).toLocaleString() : 'never'}</dd>
      </dl>

      <IncidentHistory monitorId={id} />
      <CheckHistory monitorId={id} />
    </div>
  );
}
