// dot + text always together - status is never color-alone (a red/green
// dot by itself fails for colorblind users and isn't scannable at a
// glance either). null means "no data yet", not down - shown neutral.
// upLabel/downLabel let callers reuse the same up/down visual language
// for a different pair of words (e.g. incidents: resolved/ongoing).
export function StatusDot({ status, upLabel = 'up', downLabel = 'down' }) {
  if (status == null) {
    return (
      <span className="status-dot status-dot--unknown">
        <span className="status-dot__mark" />
        pending
      </span>
    );
  }

  const isUp = status === 'up';
  return (
    <span className={`status-dot ${isUp ? 'status-dot--up' : 'status-dot--down'}`}>
      <span className="status-dot__mark" />
      {isUp ? upLabel : downLabel}
    </span>
  );
}
