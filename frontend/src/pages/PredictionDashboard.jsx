import { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Area, ComposedChart,
} from "recharts";
import { T } from "../styles/theme";
import { getPrediction } from "../services/predictionService";
import PageShell from "../components/PageShell";
import Button from "../components/Button";
import StatCard from "../components/StatCard";

const DISTRICTS = [
  "", "Bengaluru North", "Bengaluru South", "Mysuru",
  "Hubballi-Dharwad", "Mangaluru", "Belagavi",
  "Kalaburagi", "Shivamogga",
];

const SEASON_EMOJIS = { Winter: "\u2744\ufe0f", Summer: "\u2600\ufe0f", Monsoon: "\ud83c\udf27", Autumn: "\ud83c\udf42" };
const TREND_COLORS = { rising: "#EF4444", stable: "#F59E0B", declining: "#22C55E" };

function TrendBadge({ trend }) {
  const color = TREND_COLORS[trend] || "#94A3B8";
  const icon = trend === "rising" ? "\u2191" : trend === "declining" ? "\u2193" : "\u2192";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600,
      background: `${color}18`, color,
    }}>
      {icon} {trend}
    </span>
  );
}

function RiskBadge({ score }) {
  const color = score >= 70 ? "#EF4444" : score >= 40 ? "#F59E0B" : "#22C55E";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600,
      background: `${color}18`, color,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
      {score}
    </span>
  );
}

function PredictionDashboard({ user }) {
  const [monthsAhead, setMonthsAhead] = useState(3);
  const [district, setDistrict] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [filteredHotspots, setFilteredHotspots] = useState([]);
  const [trendFilter, setTrendFilter] = useState("all");

  const fetchPrediction = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getPrediction(monthsAhead, district || undefined);
      setData(result);
      setFilteredHotspots(result.hotspot_trends || []);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load prediction");
    }
    setLoading(false);
  }, [monthsAhead, district]);

  useEffect(() => { fetchPrediction(); }, [fetchPrediction]);

  useEffect(() => {
    if (!data?.hotspot_trends) return;
    if (trendFilter === "all") {
      setFilteredHotspots(data.hotspot_trends);
    } else {
      setFilteredHotspots(data.hotspot_trends.filter((h) => h.trend === trendFilter));
    }
  }, [trendFilter, data]);

  const totalPredicted = data?.total_predicted ?? 0;
  const confidence = data?.confidence ?? 0;
  const highestRisk = data?.hotspot_trends?.length
    ? data.hotspot_trends.reduce((a, b) => (a.risk_score > b.risk_score ? a : b), data.hotspot_trends[0])
    : null;
  const fastestGrowing = data?.hotspot_trends?.length
    ? data.hotspot_trends.filter((h) => h.trend === "rising").reduce(
        (a, b) => (a.risk_score > b.risk_score ? a : b),
        data.hotspot_trends.filter((h) => h.trend === "rising")[0] || null
      )
    : null;

  const chartData = (data?.predictions || []).map((p) => ({
    month: p.month,
    Historical: p.historical_count,
    Predicted: p.predicted_count,
    Upper: p.upper_bound,
    Lower: p.lower_bound,
  }));

  const selectStyle = {
    padding: "10px 14px", background: T.inputBg,
    border: `1px solid ${T.inputBorder}`, borderRadius: 10,
    color: T.textPrimary, fontSize: 14, outline: "none",
    width: "100%", boxSizing: "border-box",
    appearance: "none", cursor: "pointer",
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
    backgroundRepeat: "no-repeat", backgroundPosition: "right 12px center", paddingRight: 36,
  };

  const cardStyle = {
    background: T.card, border: `1px solid ${T.cardBorder}`,
    borderRadius: 16, padding: 24,
  };

  return (
    <PageShell title="Crime Forecast Dashboard" user={user}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
          <div>
            <h1 style={{ color: T.textPrimary, fontSize: 24, fontWeight: 700, margin: 0 }}>Crime Forecast</h1>
            <p style={{ color: T.textMuted, fontSize: 14, margin: "4px 0 0" }}>
              ML-powered crime predictions using Linear Regression on historical FIR data
            </p>
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
            <div>
              <div style={{ fontSize: 12, color: T.textMuted, marginBottom: 4, fontWeight: 500 }}>District</div>
              <select style={{ ...selectStyle, width: 180 }} value={district} onChange={(e) => setDistrict(e.target.value)}>
                {DISTRICTS.map((d) => (
                  <option key={d} value={d}>{d || "All Districts"}</option>
                ))}
              </select>
            </div>
            <div>
              <div style={{ fontSize: 12, color: T.textMuted, marginBottom: 4, fontWeight: 500 }}>
                Forecast: {monthsAhead} month{monthsAhead > 1 ? "s" : ""}
              </div>
              <input type="range" min={1} max={12} value={monthsAhead}
                onChange={(e) => setMonthsAhead(Number(e.target.value))}
                style={{ width: 140, accentColor: T.accent }} />
            </div>
            <Button onClick={fetchPrediction} disabled={loading} style={{ height: 40, padding: "0 20px" }}>
              {loading ? "Loading..." : "Refresh"}
            </Button>
          </div>
        </div>

        {error && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
            borderRadius: 12, padding: "14px 18px", marginBottom: 20, color: T.danger, fontSize: 14,
          }}>{error}</div>
        )}

        {loading && !data && (
          <div style={{ textAlign: "center", padding: 60, color: T.textMuted }}>
            <div style={{
              width: 32, height: 32, border: "3px solid rgba(91,127,255,0.2)",
              borderTopColor: T.accent, borderRadius: "50%",
              animation: "spin 0.6s linear infinite", margin: "0 auto 12px",
            }} />
            Generating forecast...
          </div>
        )}

        {data && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
              <StatCard title="Predicted Crimes (Next Month)" value={Math.round(totalPredicted).toLocaleString()}
                subtitle={district || "All Districts"} icon="📈" color={T.accent} />
              <StatCard title="Model Confidence" value={`${(confidence * 100).toFixed(1)}%`}
                subtitle="Linear Regression R²" icon="🎯" color="#22C55E" />
              <StatCard title="Highest Risk District" value={highestRisk?.district || "N/A"}
                subtitle={highestRisk ? `Score: ${highestRisk.risk_score}` : "No data"} icon="⚠️" color="#EF4444" />
              <StatCard title="Fastest Growing" value={fastestGrowing?.district || "N/A"}
                subtitle={fastestGrowing ? `Trend: ${fastestGrowing.trend}` : "No rising districts"} icon="🔥" color="#F59E0B" />
            </div>

            <div style={{ ...cardStyle, marginBottom: 24 }}>
              <h3 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>
                Crime Forecast — Historical & Predicted
              </h3>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={T.cardBorder} />
                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: T.textMuted }} />
                    <YAxis tick={{ fontSize: 12, fill: T.textMuted }} />
                    <Tooltip contentStyle={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 8, fontSize: 13, color: T.textPrimary }} />
                    <Legend />
                    <Area type="monotone" dataKey="Upper" fill={T.accent} fillOpacity={0.08} stroke="none" />
                    <Area type="monotone" dataKey="Lower" fill={T.bg} fillOpacity={0} stroke="none" />
                    <Line type="monotone" dataKey="Historical" stroke="#94A3B8" strokeWidth={2}
                      strokeDasharray="5 5" dot={{ r: 4, fill: "#94A3B8" }} name="Historical" />
                    <Line type="monotone" dataKey="Predicted" stroke={T.accent} strokeWidth={3}
                      dot={{ r: 5, fill: T.accent }} name="Predicted" />
                    <Line type="monotone" dataKey="Upper" stroke="#5B7FFF" strokeWidth={1}
                      strokeDasharray="3 3" dot={false} opacity={0.6} name="Upper Bound" />
                    <Line type="monotone" dataKey="Lower" stroke="#5B7FFF" strokeWidth={1}
                      strokeDasharray="3 3" dot={false} opacity={0.6} name="Lower Bound" />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ color: T.textMuted, textAlign: "center", padding: 40 }}>No prediction data available.</div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
              <div style={cardStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h3 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: 0 }}>🔥 Hotspot Trends</h3>
                  <select style={{ ...selectStyle, width: 130, padding: "6px 10px", fontSize: 12 }}
                    value={trendFilter} onChange={(e) => setTrendFilter(e.target.value)}>
                    <option value="all">All Trends</option>
                    <option value="rising">Rising</option>
                    <option value="stable">Stable</option>
                    <option value="declining">Declining</option>
                  </select>
                </div>
                {filteredHotspots.length > 0 ? (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderBottom: `1px solid ${T.cardBorder}`, color: T.textMuted, fontWeight: 500 }}>
                          <th style={{ textAlign: "left", padding: "8px 6px" }}>District</th>
                          <th style={{ textAlign: "right", padding: "8px 6px" }}>Current</th>
                          <th style={{ textAlign: "right", padding: "8px 6px" }}>Predicted</th>
                          <th style={{ textAlign: "center", padding: "8px 6px" }}>Trend</th>
                          <th style={{ textAlign: "center", padding: "8px 6px" }}>Risk</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredHotspots.map((h, i) => (
                          <tr key={i} style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                            <td style={{ padding: "10px 6px", color: T.textPrimary, fontWeight: 500 }}>{h.district}</td>
                            <td style={{ padding: "10px 6px", textAlign: "right", color: T.textSecondary }}>{h.current_count}</td>
                            <td style={{ padding: "10px 6px", textAlign: "right", color: T.textSecondary }}>{h.predicted_next_month}</td>
                            <td style={{ padding: "10px 6px", textAlign: "center" }}><TrendBadge trend={h.trend} /></td>
                            <td style={{ padding: "10px 6px", textAlign: "center" }}><RiskBadge score={h.risk_score} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ color: T.textMuted, textAlign: "center", padding: 30, fontSize: 13 }}>No hotspot trends available.</div>
                )}
              </div>

              <div style={cardStyle}>
                <h3 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>🌦 Seasonal Crime Patterns</h3>
                {(data?.seasonal_patterns || []).length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {data.seasonal_patterns.map((s, i) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", gap: 16,
                        padding: "14px 16px", borderRadius: 12, background: `${T.cardBorder}30`,
                      }}>
                        <div style={{ fontSize: 28 }}>{SEASON_EMOJIS[s.season] || "📅"}</div>
                        <div style={{ flex: 1 }}>
                          <div style={{ color: T.textPrimary, fontWeight: 600, fontSize: 14 }}>{s.season}</div>
                          <div style={{ color: T.textMuted, fontSize: 12 }}>Avg: {Math.round(s.average_crimes).toLocaleString()} crimes</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          {s.change_percent !== null && s.change_percent !== undefined ? (
                            <div style={{
                              fontSize: 15, fontWeight: 700,
                              color: s.change_percent > 0 ? "#EF4444" : s.change_percent < 0 ? "#22C55E" : T.textSecondary,
                            }}>
                              {s.change_percent > 0 ? "+" : ""}{s.change_percent}%
                            </div>
                          ) : (
                            <div style={{ color: T.textMuted, fontSize: 12 }}>Baseline</div>
                          )}
                          <div style={{ color: T.textMuted, fontSize: 11 }}>{s.change_percent !== null ? "vs prev season" : "First season"}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: T.textMuted, textAlign: "center", padding: 30, fontSize: 13 }}>Seasonal data not available.</div>
                )}
              </div>
            </div>

            <div style={{ color: T.textMuted, fontSize: 12, textAlign: "center", padding: "8px 0 24px" }}>
              Model: Linear Regression · Historical FIRs Analyzed: {data.total_historical?.toLocaleString() || 0} ·
              Generated: {data.generated_at ? new Date(data.generated_at).toLocaleString() : "—"}
            </div>
          </>
        )}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </PageShell>
  );
}

export default PredictionDashboard;
