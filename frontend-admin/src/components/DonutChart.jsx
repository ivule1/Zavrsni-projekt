import { CHART_PALETTE } from "../chartPalette";

// Namjerno bez vanjske biblioteke za grafove (nema instaliranog dataviz
// paketa u projektu) - jednostavan "donut" graf iscrtan cistim SVG-om,
// stroke-dasharray tehnikom (svaki segment je jedan krug s dijelom obruba
// obojenim). Dovoljno za prikaz udjela po kandidatu/regiji na Nadzor tabu.
export default function DonutChart({ data, size = 150, thickness = 24, centerLabel }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = size / 2;
  const ringRadius = radius - thickness / 2;
  const circumference = 2 * Math.PI * ringRadius;

  // Segmenti se racunaju bez mutacije izvana - svaki segment zna svoj
  // pocetni offset jer je to zbroj duljina svih PRETHODNIH segmenata
  // (nema vanjske "let" varijable koja bi se mijenjala izmedju rendera).
  const segments = data
    .filter((d) => d.value > 0)
    .reduce((acc, d, i) => {
      const previousOffset = acc.length > 0 ? acc[acc.length - 1].offset + acc[acc.length - 1].dash : 0;
      const dash = (d.value / total) * circumference;
      acc.push({ ...d, dash, offset: previousOffset, color: d.color || CHART_PALETTE[i % CHART_PALETTE.length] });
      return acc;
    }, []);

  return (
    <div className="donut-chart-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Grafički prikaz udjela">
        {total === 0 ? (
          <circle cx={radius} cy={radius} r={ringRadius} fill="none" stroke="#e1e4e8" strokeWidth={thickness} />
        ) : (
          <g transform={`rotate(-90 ${radius} ${radius})`}>
            {segments.map((s) => (
              <circle
                key={s.label}
                cx={radius}
                cy={radius}
                r={ringRadius}
                fill="none"
                stroke={s.color}
                strokeWidth={thickness}
                strokeDasharray={`${s.dash} ${circumference - s.dash}`}
                strokeDashoffset={-s.offset}
              />
            ))}
          </g>
        )}
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={size * 0.16}
          fontWeight="700"
          fill="var(--admin-text)"
        >
          {centerLabel ?? total}
        </text>
      </svg>
      <ul className="donut-legend">
        {data.map((d, i) => (
          <li key={d.label}>
            <span className="donut-swatch" style={{ backgroundColor: d.color || CHART_PALETTE[i % CHART_PALETTE.length] }} />
            <span className="donut-legend-label">{d.label}</span>
            <span className="donut-legend-value">
              {d.value}
              {total > 0 && <span className="text-muted"> ({((d.value / total) * 100).toFixed(1)}%)</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
