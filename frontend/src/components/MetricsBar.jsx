// four stat tiles - the "clear metrics" a monitoring dashboard should
// lead with, computed from data the page already has (no extra endpoint
// beyond the ongoing-incidents count)
export function MetricsBar({ monitors, ongoingIncidents }) {
  const total = monitors.length;
  const up = monitors.filter((m) => m.current_status === 'up').length;
  const down = monitors.filter((m) => m.current_status === 'down').length;

  return (
    <div className="metrics-row">
      <div className="card stat-tile">
        <span className="stat-tile__label">Monitors</span>
        <span className="stat-tile__value">{total}</span>
      </div>
      <div className={`card stat-tile ${up > 0 ? 'stat-tile--good' : ''}`}>
        <span className="stat-tile__label">Up</span>
        <span className="stat-tile__value">{up}</span>
      </div>
      <div className={`card stat-tile ${down > 0 ? 'stat-tile--critical' : ''}`}>
        <span className="stat-tile__label">Down</span>
        <span className="stat-tile__value">{down}</span>
      </div>
      <div className={`card stat-tile ${ongoingIncidents > 0 ? 'stat-tile--critical' : ''}`}>
        <span className="stat-tile__label">Ongoing incidents</span>
        <span className="stat-tile__value">{ongoingIncidents}</span>
      </div>
    </div>
  );
}
