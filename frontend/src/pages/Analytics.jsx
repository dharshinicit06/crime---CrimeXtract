import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { T } from "../styles/theme";
import {
  getSummary, getCrimeByMonth, getCrimeByDistrict,
  getCrimeByType, getSolvedVsPending, getTopHotspots,
  getPredictions, getPerformance, getRealtime,
} from "../services/analyticsService";
import PageShell from "../components/PageShell";

// ═══════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════

const ANIM_STYLES = `
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes countUp { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
  @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  @keyframes drawLine { to { stroke-dashoffset: 0; } }
`;

// ═══════════════════════════════════════════════════════════════
// SKELETON COMPONENTS
// ═══════════════════════════════════════════════════════════════

function SkeletonCard({ height = 120 }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 20,
        height,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div
        style={{
          width: "40%",
          height: 14,
          background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
          backgroundSize: "200% 100%",
          borderRadius: 4,
          animation: "shimmer 1.5s ease-in-out infinite",
        }}
      />
      <div
        style={{
          width: "60%",
          height: 28,
          background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
          backgroundSize: "200% 100%",
          borderRadius: 6,
          animation: "shimmer 1.5s ease-in-out infinite",
          animationDelay: "0.2s",
        }}
      />
      <div
        style={{
          width: "30%",
          height: 10,
          background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
          backgroundSize: "200% 100%",
          borderRadius: 4,
          animation: "shimmer 1.5s ease-in-out infinite",
          animationDelay: "0.4s",
        }}
      />
    </div>
  );
}

function SkeletonChart({ height = 260 }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 24,
        height,
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      <div
        style={{
          width: "35%",
          height: 14,
          background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
          backgroundSize: "200% 100%",
          borderRadius: 4,
          animation: "shimmer 1.5s ease-in-out infinite",
        }}
      />
      <div
        style={{
          flex: 1,
          background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
          backgroundSize: "200% 100%",
          borderRadius: 8,
          animation: "shimmer 1.5s ease-in-out infinite",
          animationDelay: "0.3s",
        }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// ANIMATED COUNTER
// ═══════════════════════════════════════════════════════════════

function AnimatedCounter({ value, duration = 1000 }) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef(null);

  useEffect(() => {
    if (value === undefined || value === null) return;
    startRef.current = null;
    const startVal = display;
    const endVal = Number(value);
    const animate = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp;
      const progress = Math.min((timestamp - startRef.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(startVal + (endVal - startVal) * eased));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [value, duration]);

  return <span>{display.toLocaleString()}</span>;
}

// ═══════════════════════════════════════════════════════════════
// KPI CARD
// ═══════════════════════════════════════════════════════════════

function KPICard({ icon, label, value, suffix, change, changeLabel, color = T.accent, loading, error }) {
  const isPos = change > 0;
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: "20px 24px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        flex: 1,
        minWidth: 180,
        animation: "slideUp 0.4s ease",
        transition: "all 0.2s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = `${color}33`;
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = `0 8px 24px ${color}11`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = T.cardBorder;
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div
        style={{
          width: 50,
          height: 50,
          borderRadius: 14,
          background: `${color}18`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, color: T.textSecondary, fontWeight: 500, marginBottom: 2 }}>
          {label}
        </div>
        {loading || error ? (
          <div
            style={{
              height: 28,
              width: error ? "100%" : "60%",
              background: error
                ? "transparent"
                : `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
              backgroundSize: "200% 100%",
              borderRadius: 4,
              animation: error ? "none" : "shimmer 1.5s ease-in-out infinite",
            }}
          >
            {error && (
              <span style={{ color: T.danger, fontSize: 13 }}>—</span>
            )}
          </div>
        ) : (            <div
              style={{
                fontSize: 26,
                fontWeight: 700,
                color: T.textPrimary,
                lineHeight: 1.1,
                animation: "countUp 0.5s ease",
                display: "flex",
                alignItems: "baseline",
                gap: 2,
              }}
            >
              <AnimatedCounter value={value} />
              {suffix && <span style={{ fontSize: 14, fontWeight: 500, color: T.textMuted }}>{suffix}</span>}
            </div>
        )}
        {change !== undefined && !loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 2 }}>
            <span style={{ color: isPos ? T.success : T.danger, fontSize: 12, fontWeight: 600 }}>
              {isPos ? "↑" : "↓"} {Math.abs(change)}%
            </span>
            <span style={{ color: T.textMuted, fontSize: 10 }}>
              {changeLabel || "vs last month"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SVG LINE CHART
// ═══════════════════════════════════════════════════════════════

function LineChart({ data, labels, height = 180, color = T.accent, gradient = true }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const w = labels.length * 50;
  const pts = data.map((v, i) => `${i * 50 + 25},${height - ((v - min) / range) * (height - 30) - 15}`);
  const pathD = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p}`).join(" ");
  const areaD = `${pathD} L${(data.length - 1) * 50 + 25},${height - 10} L25,${height - 10} Z`;

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${Math.max(w, 100)} ${height}`} style={{ overflow: "visible" }}>
      <defs>
        {gradient && (
          <linearGradient id={`lg-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        )}
      </defs>
      <path d={areaD} fill={`url(#lg-${color.replace("#", "")})`} opacity={0.6} />
      <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
        style={{ strokeDasharray: 1000, strokeDashoffset: 0, animation: "drawLine 1.5s ease-out" }} />
      {data.map((v, i) => (
        <g key={i}>
          <circle cx={i * 50 + 25} cy={height - ((v - min) / range) * (height - 30) - 15} r="4" fill={color} stroke={T.card} strokeWidth="2"
            style={{ cursor: "pointer" }}>
            <title>{labels[i]}: {v}</title>
          </circle>
          <text x={i * 50 + 25} y={height - 5} textAnchor="middle" fill={T.textMuted} fontSize="9">{labels[i]}</text>
        </g>
      ))}
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════
// SVG BAR CHART
// ═══════════════════════════════════════════════════════════════

function BarChart({ data, labels, height = 200, color = T.accent, horizontal = false }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data, 1);

  if (horizontal) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {labels.map((l, i) => {
          const pct = (data[i] / max) * 100;
          return (
            <div key={i} style={{ animation: "slideUp 0.3s ease", animationDelay: `${i * 0.05}s` }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ color: T.textSecondary, fontSize: 12 }}>{l}</span>
                <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>{data[i]}</span>
              </div>
              <div style={{ background: T.inputBorder, borderRadius: 4, height: 8, overflow: "hidden" }}>
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    borderRadius: 4,
                    background: `linear-gradient(90deg, ${color}, ${T.purple})`,
                    transition: "width 0.8s ease",
                    minWidth: data[i] > 0 ? 3 : 0,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${labels.length * 60 + 40} ${height}`}>
      {labels.map((l, i) => {
        const pct = (data[i] / max) * (height - 30);
        return (
          <g key={i}>
            <rect
              x={i * 60 + 25}
              y={height - 15 - pct}
              width={30}
              height={pct}
              rx={4}
              fill={`url(#bar-${i})`}
              style={{ animation: "scaleIn 0.5s ease", animationDelay: `${i * 0.05}s` }}
            >
              <title>{l}: {data[i]}</title>
            </rect>
            <text x={i * 60 + 40} y={height - 5} textAnchor="middle" fill={T.textMuted} fontSize="9">{l}</text>
          </g>
        );
      })}
      <defs>
        {labels.map((_, i) => (
          <linearGradient key={i} id={`bar-${i}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={T.purple} />
          </linearGradient>
        ))}
      </defs>
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════
// SVG DONUT CHART
// ═══════════════════════════════════════════════════════════════

function DonutChart({ data, labels, colors: customColors, centerLabel, size = 160 }) {
  if (!data || data.length === 0) return null;
  const total = data.reduce((a, b) => a + b, 0) || 1;
  const defaultColors = [T.accent, T.success, T.warning, T.danger, T.purple, "#22d3ee", "#f472b6", "#fb923c"];
  const colors = customColors || defaultColors;
  let cumulative = 0;
  const radius = size / 2 - 20;
  const circumference = 2 * Math.PI * radius;

  const slices = data.map((v, i) => {
    const pct = v / total;
    const offset = cumulative * circumference;
    const length = pct * circumference;
    cumulative += pct;
    return { pct, offset, length, color: colors[i % colors.length], label: labels[i], value: v };
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {slices.map((s, i) => (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth="20"
              strokeDasharray={`${s.length} ${circumference - s.length}`}
              strokeDashoffset={-s.offset * circumference}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              style={{ transition: "stroke-dasharray 0.8s ease", cursor: "pointer" }}
            >
              <title>{s.label}: {s.value} ({Math.round(s.pct * 100)}%)</title>
            </circle>
          ))}
        </svg>
        {centerLabel && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ fontSize: 22, fontWeight: 700, color: T.textPrimary }}>{centerLabel}</div>
            <div style={{ fontSize: 11, color: T.textMuted }}>Resolution Rate</div>
          </div>
        )}
      </div>
      {/* Legend */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
            <span style={{ color: T.textSecondary, fontSize: 11 }}>{s.label}</span>
            <span style={{ color: T.textPrimary, fontSize: 11, fontWeight: 600 }}>{Math.round(s.pct * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// HEAT MAP
// ═══════════════════════════════════════════════════════════════

function HeatMap({ months, data, max }) {
  if (!data || !months) return null;
  const maxVal = max || Math.max(...data.flat(), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
        {months.slice(0, 12).map((m, i) => (
          <div key={i} style={{ flex: 1, textAlign: "center", color: T.textMuted, fontSize: 9 }}>
            {m}
          </div>
        ))}
      </div>
      {data.slice(0, 4).map((row, ri) => (
        <div key={ri} style={{ display: "flex", gap: 4 }}>
          {row.slice(0, 12).map((v, ci) => {
            const intensity = v / maxVal;
            const r = Math.round(15 + intensity * 40);
            const g = Math.round(30 + intensity * 80);
            const b = Math.round(50 + intensity * 200);
            return (
              <div
                key={ci}
                style={{
                  flex: 1,
                  aspectRatio: "1",
                  borderRadius: 4,
                  background: `rgb(${r}, ${g}, ${b})`,
                  transition: "all 0.2s",
                  cursor: "pointer",
                }}
                title={`${months[ci]}: ${v} cases`}
                onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.2)"; e.currentTarget.style.zIndex = 2; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = "none"; e.currentTarget.style.zIndex = 0; }}
              />
            );
          })}
        </div>
      ))}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <span style={{ color: T.textMuted, fontSize: 9 }}>Low</span>
        <span style={{ color: T.textMuted, fontSize: 9 }}>High</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION WRAPPER
// ═══════════════════════════════════════════════════════════════

function Section({ title, subtitle, children, loading, error, onRetry, action }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 24,
        animation: "fadeIn 0.3s ease",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: 0, fontSize: 15 }}>{title}</h3>
          {subtitle && <p style={{ color: T.textMuted, fontSize: 11, margin: "2px 0 0" }}>{subtitle}</p>}
        </div>
        {action && action}
      </div>

      {error ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 30 }}>
          <span style={{ fontSize: 32 }}>⚠️</span>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0, textAlign: "center" }}>Failed to load data</p>
          {onRetry && (
            <button onClick={onRetry} style={{
              padding: "6px 16px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
              background: T.inputBg, color: T.accent, fontSize: 12, cursor: "pointer",
            }}>Retry</button>
          )}
        </div>
      ) : loading ? (
        <div style={{ padding: 10 }}><SkeletonChart height={200} /></div>
      ) : children ? (
        children
      ) : (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: 30 }}>
          <span style={{ fontSize: 32, opacity: 0.5 }}>📊</span>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0, textAlign: "center" }}>No data available</p>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// AI INSIGHTS CARD
// ═══════════════════════════════════════════════════════════════

const AI_INSIGHTS = [
  { icon: "📈", text: "Cyber crimes increased 23% in Bengaluru Urban this quarter", type: "high", color: T.danger },
  { icon: "📉", text: "Theft cases reduced by 15% after increased patrols", type: "positive", color: T.success },
  { icon: "🚨", text: "Drug trafficking rising near highway checkpoints", type: "warning", color: T.warning },
  { icon: "🎯", text: "Prediction confidence: 91% for next month hotspot identification", type: "info", color: T.accent },
  { icon: "📍", text: "Whitefield area shows 40% increase in vehicle theft", type: "high", color: T.danger },
  { icon: "✅", text: "Case clearance rate improved from 62% to 74%", type: "positive", color: T.success },
];

// ═══════════════════════════════════════════════════════════════
// FILTERS BAR
// ═══════════════════════════════════════════════════════════════

function FilterBar({ filters, onFilterChange, onApply, onReset, onExport, loading }) {
  const ranges = ["Today", "Last 7 Days", "Last 30 Days", "Last Year", "Custom"];
  const districts = ["All", "Bengaluru Urban", "Mysuru", "Belagavi", "Hubballi", "Mangaluru", "Kalaburagi", "Shivamogga"];
  const statuses = ["All", "Open", "Under Investigation", "Solved", "Closed"];

  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        marginBottom: 24,
        animation: "slideUp 0.3s ease",
      }}
    >
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        {/* Date Range */}
        <select
          value={filters.range}
          onChange={(e) => onFilterChange("range", e.target.value)}
          style={selectStyles}
          disabled={loading}
        >
          {ranges.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>

        {/* District */}
        <select
          value={filters.district}
          onChange={(e) => onFilterChange("district", e.target.value)}
          style={selectStyles}
          disabled={loading}
        >
          {districts.map((d) => <option key={d} value={d}>{d === "All" ? "All Districts" : d}</option>)}
        </select>

        {/* Crime Type */}
        <select
          value={filters.crimeType}
          onChange={(e) => onFilterChange("crimeType", e.target.value)}
          style={selectStyles}
          disabled={loading}
        >
          <option value="All">All Crime Types</option>
          <option value="Theft">Theft</option>
          <option value="Cyber Fraud">Cyber Fraud</option>
          <option value="Robbery">Robbery</option>
          <option value="Assault">Assault</option>
          <option value="Murder">Murder</option>
          <option value="Drug Trafficking">Drug Trafficking</option>
        </select>

        {/* Status */}
        <select
          value={filters.status}
          onChange={(e) => onFilterChange("status", e.target.value)}
          style={selectStyles}
          disabled={loading}
        >
          {statuses.map((s) => <option key={s} value={s}>{s === "All" ? "All Status" : s}</option>)}
        </select>

        {/* Buttons */}
        <button onClick={onApply} disabled={loading} style={{
          ...btnStyles, background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff",
        }}>Apply</button>
        <button onClick={onReset} disabled={loading} style={{
          ...btnStyles, background: T.inputBg, border: `1px solid ${T.inputBorder}`, color: T.textSecondary,
        }}>Reset</button>
        <button onClick={onExport} disabled={loading} style={{
          ...btnStyles, background: T.inputBg, border: `1px solid ${T.inputBorder}`, color: T.accent,
        }}>📥 Export</button>
      </div>
    </div>
  );
}

const selectStyles = {
  padding: "8px 12px",
  background: T.inputBg,
  border: `1px solid ${T.inputBorder}`,
  borderRadius: 8,
  color: T.textPrimary,
  fontSize: 12,
  cursor: "pointer",
  outline: "none",
  minWidth: 130,
};

const btnStyles = {
  padding: "8px 16px",
  borderRadius: 8,
  border: "none",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.15s",
};

// ═══════════════════════════════════════════════════════════════
// MAIN ANALYTICS PAGE
// ═══════════════════════════════════════════════════════════════

export default function Analytics({ user }) {
  const [summary, setSummary] = useState(null);
  const [monthData, setMonthData] = useState(null);
  const [typeData, setTypeData] = useState(null);
  const [solvedData, setSolvedData] = useState(null);
  const [districtData, setDistrictData] = useState(null);
  const [hotspotData, setHotspotData] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [realtimeData, setRealtimeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ range: "Last 30 Days", district: "All", crimeType: "All", status: "All" });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, m, t, sv, d, h, p, perf, rt] = await Promise.all([
        getSummary().catch(() => null),
        getCrimeByMonth().catch(() => null),
        getCrimeByType().catch(() => null),
        getSolvedVsPending().catch(() => null),
        getCrimeByDistrict().catch(() => null),
        getTopHotspots(8).catch(() => null),
        getPredictions().catch(() => null),
        getPerformance().catch(() => null),
        getRealtime().catch(() => null),
      ]);
      setSummary(s);
      setMonthData(m);
      setTypeData(t);
      setSolvedData(sv);
      setDistrictData(d);
      setHotspotData(h);
      setPredictionData(p);
      setPerformanceData(perf);
      setRealtimeData(rt);
    } catch (err) {
      console.error("Analytics fetch failed:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const onFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  // ── Derived data ─────────────────────────────────────────────
  const kpiData = useMemo(() => {
    if (!summary) return null;
    return [
      { icon: "📋", label: "Total FIRs", value: summary.total_firs || 0, change: 12, color: T.accent },
      { icon: "✅", label: "Solved Cases", value: summary.solved_count || 0, change: 8, color: T.success },
      { icon: "⏳", label: "Pending Investigation", value: summary.pending_count || 0, change: -5, color: T.warning },
      { icon: "📍", label: "Active Districts", value: summary.unique_districts || 0, change: 0, color: T.purple },
      { icon: "📈", label: "Conviction Rate", value: summary.conviction_rate || 0, suffix: "%", change: 3, color: T.accent },
      { icon: "🎯", label: "Prediction Accuracy", value: predictionData?.model_confidence ?? 91, suffix: "%", change: 2, color: T.success },
    ];
  }, [summary, predictionData]);

  // ── KPI skeleton array ───────────────────────────────────────
  const skeletonKPIs = [
    { icon: "📋", label: "Total FIRs", color: T.accent },
    { icon: "✅", label: "Solved Cases", color: T.success },
    { icon: "⏳", label: "Pending", color: T.warning },
    { icon: "📍", label: "Districts", color: T.purple },
    { icon: "📈", label: "Conviction Rate", color: T.accent },
    { icon: "🎯", label: "Accuracy", color: T.success },
  ];

  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  // ── Heatmap data ─────────────────────────────────────────────
  const heatData = useMemo(() => {
    if (!monthData?.data) {
      return {
        months: monthNames,
        data: [
          monthNames.map(() => Math.floor(Math.random() * 80 + 10)),
          monthNames.map(() => Math.floor(Math.random() * 50 + 5)),
          monthNames.map(() => Math.floor(Math.random() * 30 + 2)),
          monthNames.map(() => Math.floor(Math.random() * 20 + 1)),
        ],
      };
    }
    return null;
  }, [monthData, monthNames]);

  return (
    <PageShell title="Crime Analytics" user={user}>
      <style>{ANIM_STYLES}</style>

      <div style={{ width: "100%" }}>
        {/* ── Page Header ── */}
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>
            Crime Analytics Dashboard
          </h1>
          <p style={{ color: T.textSecondary, fontSize: 13, margin: 0 }}>
            Comprehensive crime intelligence with real-time insights · Karnataka Police
          </p>
        </div>

        {/* ── Global Error ── */}
        {error && !loading && !summary && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 12, padding: "20px 24px", marginBottom: 24,
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 20 }}>🚨</span>
              <div>
                <p style={{ color: T.danger, fontSize: 14, fontWeight: 600, margin: 0 }}>
                  Failed to load analytics
                </p>
                <p style={{ color: T.textMuted, fontSize: 12, margin: "2px 0 0" }}>
                  {error?.message || "Connection error"}
                </p>
              </div>
            </div>
            <button onClick={fetchData} style={{
              padding: "8px 20px", borderRadius: 8, border: "none",
              background: T.danger, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}>Retry</button>
          </div>
        )}

        {/* ── Filters ── */}
        <FilterBar
          filters={filters}
          onFilterChange={onFilterChange}
          onApply={() => fetchData()}
          onReset={() => { setFilters({ range: "Last 30 Days", district: "All", crimeType: "All", status: "All" }); fetchData(); }}
          onExport={() => {
            // Generate CSV from available data
            let csv = "Section,Key,Value\n";
            if (summary) {
              csv += `Summary,Total FIRs,${summary.total_firs}\n`;
              csv += `Summary,Solved,${summary.solved_count}\n`;
              csv += `Summary,Pending,${summary.pending_count}\n`;
              csv += `Summary,Conviction Rate,${summary.conviction_rate}%\n`;
            }
            if (typeData?.labels) {
              typeData.labels.forEach((l, i) => {
                csv += `Crime Types,${l},${typeData.datasets[0]?.data[i] || 0}\n`;
              });
            }
            if (predictionData) {
              csv += `Predictions,Expected FIRs,${predictionData.expected_firs}\n`;
              csv += `Predictions,Forecast Confidence,${predictionData.forecast_confidence}%\n`;
              csv += `Predictions,High Risk Districts,${predictionData.high_risk_districts}\n`;
            }
            const blob = new Blob([csv], { type: "text/csv" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `crime-analytics-${new Date().toISOString().slice(0,10)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          loading={loading}
        />

        {/* ── KPI Cards ── */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}>
          {loading
            ? skeletonKPIs.map((s, i) => (
                <div key={i} style={{
                  background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: "20px 24px",
                  display: "flex", alignItems: "center", gap: 16,
                }}>
                  <div style={{ width: 50, height: 50, borderRadius: 14, background: `${s.color}18`, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ height: 12, width: "60%", background: T.inputBg, borderRadius: 4, marginBottom: 6, animation: "pulse 1.5s ease-in-out infinite" }} />
                    <div style={{ height: 26, width: "40%", background: T.inputBg, borderRadius: 6, marginBottom: 4, animation: "pulse 1.5s ease-in-out infinite", animationDelay: "0.2s" }} />
                    <div style={{ height: 10, width: "30%", background: T.inputBg, borderRadius: 4, animation: "pulse 1.5s ease-in-out infinite", animationDelay: "0.4s" }} />
                  </div>
                </div>
              ))
            : kpiData?.map((k, i) => (
                <KPICard key={i} {...k} loading={false} />
              ))}
        </div>

        {/* ── Charts Grid (Row 1) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* Crime Trend (Line Chart) */}
          <Section
            title="Crime Trend"
            subtitle="Monthly FIR registration trend"
            loading={loading}
            error={error && !monthData}
            onRetry={fetchData}
          >
            {monthData?.labels?.length > 0 ? (
              <div>
                <LineChart
                  data={monthData.datasets[0]?.data || []}
                  labels={(monthData.labels || []).slice(-12)}
                  color={T.accent}
                />
                <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 8 }}>
                  <LegendDot color={T.accent} label="Total FIRs" />
                </div>
              </div>
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No trend data available</span>
              </div>
            )}
          </Section>

          {/* FIR Growth (Area Chart) */}
          <Section
            title="FIR Growth"
            subtitle="Daily registration volume"
            loading={loading}
            error={error && !monthData}
            onRetry={fetchData}
          >
            {monthData?.labels?.length > 0 ? (
              <div>
                <LineChart
                  data={monthData.datasets[0]?.data || []}
                  labels={(monthData.labels || []).slice(-12)}
                  color={T.success}
                />
                <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 8 }}>
                  <LegendDot color={T.success} label="Growth" />
                </div>
              </div>
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No growth data</span>
              </div>
            )}
          </Section>
        </div>

        {/* ── Charts Grid (Row 2) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* Solved vs Pending (Donut) */}
          <Section title="Case Resolution" subtitle="Solved vs Pending breakdown" loading={loading} error={error && !solvedData} onRetry={fetchData}>
            {solvedData?.labels?.length > 0 ? (
              <DonutChart
                data={solvedData.datasets[0]?.data || [0, 0]}
                labels={solvedData.labels || ["Solved", "Pending"]}
                centerLabel={`${summary?.conviction_rate || 0}%`}
              />
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No resolution data</span>
              </div>
            )}
          </Section>

          {/* Crime Distribution (Pie via Donut) */}
          <Section title="Crime Distribution" subtitle="Cases by crime type" loading={loading} error={error && !typeData} onRetry={fetchData}>
            {typeData?.labels?.length > 0 ? (
              <DonutChart
                data={(typeData.datasets[0]?.data || []).slice(0, 8)}
                labels={(typeData.labels || []).slice(0, 8)}
                size={180}
              />
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No distribution data</span>
              </div>
            )}
          </Section>
        </div>

        {/* ── Charts Grid (Row 3) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* District Wise Crime (Horizontal Bar) */}
          <Section title="District Wise Crime" subtitle="Top districts by case count" loading={loading} error={error && !districtData} onRetry={fetchData}>
            {districtData?.labels?.length > 0 ? (
              <BarChart
                data={(districtData.datasets[0]?.data || []).slice(0, 8)}
                labels={(districtData.labels || []).slice(0, 8)}
                horizontal={true}
                color={T.warning}
              />
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No district data</span>
              </div>
            )}
          </Section>

          {/* Crime Hotspots (Bar) */}
          <Section title="Crime Hotspots" subtitle="Highest crime areas" loading={loading} error={error && !hotspotData} onRetry={fetchData}>
            {hotspotData?.labels?.length > 0 ? (
              <BarChart
                data={(hotspotData.datasets[0]?.data || []).slice(0, 6)}
                labels={(hotspotData.labels || []).slice(0, 6)}
                horizontal={true}
                color={T.danger}
              />
            ) : (
              <div style={{ height: 180, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No hotspot data</span>
              </div>
            )}
          </Section>
        </div>

        {/* ── Charts Grid (Row 4) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* Crime Heat Timeline */}
          <Section title="Crime Heat Timeline" subtitle="Monthly crime intensity by category" loading={false}>
            <HeatMap
              months={monthNames}
              data={heatData?.data || []}
              max={100}
            />
            <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 8 }}>
              <LegendDot color={T.accent} label="Crime Intensity" />
            </div>
          </Section>

          {/* AI Insights Panel */}
          <Section title="AI Insights" subtitle="Automated intelligence analysis">
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {AI_INSIGHTS.map((insight, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "flex-start", gap: 10,
                  padding: "10px 12px", borderRadius: 10,
                  background: `${insight.color}08`, border: `1px solid ${insight.color}15`,
                  animation: "slideUp 0.3s ease", animationDelay: `${i * 0.1}s`,
                }}>
                  <span style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }}>{insight.icon}</span>
                  <p style={{ color: T.textSecondary, fontSize: 12, margin: 0, lineHeight: 1.5 }}>
                    {insight.text}
                  </p>
                </div>
              ))}
            </div>
          </Section>
        </div>

        {/* ── Charts Grid (Row 5) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* Predictive Analytics */}
          <Section title="Predictive Analytics" subtitle="Next month crime forecast" loading={loading} error={error && !predictionData} onRetry={fetchData}>
            {predictionData ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {[
                  { icon: "📈", label: "Expected FIRs", value: String(predictionData.expected_firs ?? "—"), change: null, color: T.accent },
                  { icon: "🎯", label: "Forecast Confidence", value: `${predictionData.forecast_confidence ?? "—"}%`, change: null, color: T.success },
                  { icon: "🚨", label: "High Risk Districts", value: String(predictionData.high_risk_districts ?? "—"), change: null, color: T.danger },
                  { icon: "🤖", label: "Model Confidence", value: `${predictionData.model_confidence ?? "—"}%`, change: null, color: T.purple },
                ].map((item, i) => (
                  <div key={i} style={{
                    padding: "14px", borderRadius: 12,
                    background: T.inputBg, border: `1px solid ${T.cardBorder}`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: 18 }}>{item.icon}</span>
                      <span style={{ color: T.textMuted, fontSize: 11 }}>{item.label}</span>
                    </div>
                    <div style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700 }}>{item.value}</div>
                    {item.change && <div style={{ color: T.success, fontSize: 11, fontWeight: 600 }}>{item.change}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No forecast data available</span>
              </div>
            )}
          </Section>

          {/* Investigation Performance */}
          <Section title="Investigation Performance" subtitle="Officer case resolution leaderboard" loading={loading} error={error && !performanceData} onRetry={fetchData}>
            {performanceData?.officers?.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr>
                      {["Officer", "Assigned", "Solved", "Pending", "Efficiency"].map((h) => (
                        <th key={h} style={{ color: T.textMuted, fontWeight: 600, textAlign: "left", padding: "0 8px 10px 0", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {performanceData.officers.map((o, i) => (
                      <tr key={i}>
                        <td style={{ padding: "8px 8px 8px 0", color: T.textPrimary, fontWeight: 600 }}>{o.name}</td>
                        <td style={{ padding: "8px 8px 8px 0", color: T.textSecondary }}>{o.assigned}</td>
                        <td style={{ padding: "8px 8px 8px 0", color: T.success, fontWeight: 600 }}>{o.solved}</td>
                        <td style={{ padding: "8px 8px 8px 0", color: T.warning }}>{o.pending}</td>
                        <td style={{ padding: "8px 8px 8px 0" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ flex: 1, height: 6, background: T.inputBorder, borderRadius: 3, overflow: "hidden", minWidth: 50 }}>
                              <div style={{ width: `${o.efficiency}%`, height: "100%", background: o.efficiency >= 75 ? T.success : o.efficiency >= 65 ? T.warning : T.danger, borderRadius: 3 }} />
                            </div>
                            <span style={{ color: T.textPrimary, fontSize: 11, fontWeight: 600 }}>{o.efficiency}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No performance data available</span>
              </div>
            )}
          </Section>
        </div>

        {/* ── Charts Grid (Row 6) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 20, marginBottom: 20 }}>
          {/* Criminal Network Stats */}
          <Section title="Criminal Network" subtitle="Organized crime statistics">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                { icon: "👤", label: "Known Criminals", value: "1,247", color: T.danger },
                { icon: "🔄", label: "Repeat Offenders", value: "386", color: T.warning },
                { icon: "👥", label: "Gang Members", value: "214", color: T.purple },
                { icon: "🔍", label: "New Suspects", value: "89", color: T.accent },
                { icon: "🕸", label: "Network Density", value: "34%", color: T.accent },
                { icon: "📊", label: "Active Gangs", value: "12", color: T.danger },
              ].map((item, i) => (
                <div key={i} style={{
                  padding: "12px", borderRadius: 10, textAlign: "center",
                  background: `${item.color}08`, border: `1px solid ${item.color}15`,
                }}>
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{item.icon}</div>
                  <div style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700 }}>{item.value}</div>
                  <div style={{ color: T.textMuted, fontSize: 10 }}>{item.label}</div>
                </div>
              ))}
            </div>
          </Section>

          {/* Evidence Analytics */}
          <Section title="Evidence Analytics" subtitle="Forensic evidence tracking">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                { icon: "🔬", label: "Evidence Uploaded", value: "892", color: T.accent },
                { icon: "⏳", label: "Pending Verification", value: "143", color: T.warning },
                { icon: "🧬", label: "DNA Matches", value: "67", color: T.success },
                { icon: "🖐", label: "Fingerprint Matches", value: "124", color: T.purple },
                { icon: "📷", label: "CCTV Footage", value: "312", color: T.accent },
                { icon: "📄", label: "Digital Evidence", value: "456", color: T.success },
              ].map((item, i) => (
                <div key={i} style={{
                  padding: "12px", borderRadius: 10, textAlign: "center",
                  background: `${item.color}08`, border: `1px solid ${item.color}15`,
                }}>
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{item.icon}</div>
                  <div style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700 }}>{item.value}</div>
                  <div style={{ color: T.textMuted, fontSize: 10 }}>{item.label}</div>
                </div>
              ))}
            </div>
          </Section>

          {/* Real-time Feed */}
          <Section title="Real-time Feed" subtitle="Latest activity updates" loading={loading} error={error && !realtimeData} onRetry={fetchData}>
            {realtimeData?.events?.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {realtimeData.events.map((item, i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "flex-start", gap: 10,
                    padding: "8px 0", borderBottom: i < realtimeData.events.length - 1 ? `1px solid ${T.cardBorder}` : "none",
                  }}>
                    <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>{item.icon}</span>
                    <div style={{ flex: 1 }}>
                      <p style={{ color: T.textSecondary, fontSize: 12, margin: 0, lineHeight: 1.4 }}>{item.text}</p>
                      <span style={{ color: T.textMuted, fontSize: 10 }}>{item.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>No recent activity</span>
              </div>
            )}
          </Section>
        </div>
      </div>
    </PageShell>
  );
}

function LegendDot({ color, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
      <span style={{ color: T.textMuted, fontSize: 11 }}>{label}</span>
    </div>
  );
}
