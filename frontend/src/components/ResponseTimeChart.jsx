import { useState } from 'react';

// hand-rolled SVG line chart - one series (response time), so no legend
// needed per the dataviz skill's rule ("a single series needs no legend
// box, the title already says what's plotted"). No charting library -
// this project doesn't reach for a dependency it can write in ~80 lines.

const WIDTH = 640;
const HEIGHT = 160;
const PAD = { top: 10, right: 12, bottom: 24, left: 44 };
const MAX_POINTS = 30;

export function ResponseTimeChart({ checks }) {
  const [hoverIndex, setHoverIndex] = useState(null);

  // checks arrive newest-first (that's how the API/table wants them);
  // a time series reads left-to-right oldest-to-newest, so slice the
  // most recent MAX_POINTS then reverse just for the chart
  const points = checks
    .filter((c) => c.response_time_ms != null)
    .slice(0, MAX_POINTS)
    .slice()
    .reverse();

  if (points.length < 2) {
    return <p className="chart-empty">Not enough data yet for a chart.</p>;
  }

  const maxValue = Math.max(...points.map((p) => p.response_time_ms));
  // round the axis top up to a clean step so the tick labels are round
  // numbers, not "217ms" - matches the skill's "clean numbers" tick rule
  const axisMax = Math.ceil((maxValue * 1.1) / 50) * 50 || 50;

  const plotW = WIDTH - PAD.left - PAD.right;
  const plotH = HEIGHT - PAD.top - PAD.bottom;

  const x = (i) => PAD.left + (i / (points.length - 1)) * plotW;
  const y = (v) => PAD.top + plotH - (v / axisMax) * plotH;

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(p.response_time_ms)}`)
    .join(' ');
  const areaPath = `${linePath} L ${x(points.length - 1)} ${PAD.top + plotH} L ${x(0)} ${PAD.top + plotH} Z`;

  const ticks = [0, 0.5, 1].map((f) => Math.round(axisMax * f));

  function nearestIndexForClientX(clientX, rect) {
    const relX = ((clientX - rect.left) / rect.width) * WIDTH;
    let nearest = 0;
    let nearestDist = Infinity;
    points.forEach((_, i) => {
      const dist = Math.abs(x(i) - relX);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    });
    return nearest;
  }

  function handleMove(e) {
    setHoverIndex(nearestIndexForClientX(e.clientX, e.currentTarget.getBoundingClientRect()));
  }

  function handleKeyDown(e) {
    if (e.key === 'ArrowLeft') {
      setHoverIndex((i) => Math.max(0, (i ?? points.length) - 1));
    } else if (e.key === 'ArrowRight') {
      setHoverIndex((i) => Math.min(points.length - 1, (i ?? -1) + 1));
    }
  }

  const hovered = hoverIndex != null ? points[hoverIndex] : null;

  return (
    <div className="chart">
      <h3 className="chart__title">Response time</h3>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="Response time in milliseconds over the recent checks shown in the table below"
        tabIndex={0}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverIndex(null)}
        onFocus={() => setHoverIndex(points.length - 1)}
        onBlur={() => setHoverIndex(null)}
        onKeyDown={handleKeyDown}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(t)} y2={y(t)} className="chart__gridline" />
            <text x={PAD.left - 8} y={y(t)} className="chart__tick" textAnchor="end" dominantBaseline="middle">
              {t}ms
            </text>
          </g>
        ))}
        <path d={areaPath} className="chart__area" />
        <path d={linePath} className="chart__line" fill="none" />
        {hoverIndex != null && (
          <>
            <line
              x1={x(hoverIndex)}
              x2={x(hoverIndex)}
              y1={PAD.top}
              y2={PAD.top + plotH}
              className="chart__crosshair"
            />
            <circle cx={x(hoverIndex)} cy={y(hovered.response_time_ms)} r="4" className="chart__dot" />
          </>
        )}
      </svg>
      {hovered && (
        <div className="chart__tooltip">
          <strong>{hovered.response_time_ms} ms</strong>
          <span>{new Date(hovered.checked_at).toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
