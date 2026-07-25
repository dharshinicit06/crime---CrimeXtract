import { useState, useEffect, useCallback, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { MapPin, AlertTriangle, Shield, TrendingUp, Search, Download, RefreshCw, X, Filter } from "lucide-react";
import PageShell from "../components/PageShell";
import { listHotspots, getHotspotDetail, getHotspotInsights } from "../services/hotspotService";
import { T } from "../styles/theme";

const RISK_COLORS = { High: "#EF4444", Medium: "#F59E0B", Low: "#22C55E" };
const PIE_COLORS = ["#4F8CFF", "#EF4444", "#22C55E", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"];
const TIME_OPTIONS = [
  { value: "all", label: "All Time" },
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
];

function SkeletonCard() {
  return (
    <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, animation: "pulse 2s infinite" }}>
      <div style={{ height: 14, width: "60%", background: T.inputBorder, borderRadius: 4, marginBottom: 12 }} />
      <div style={{ height: 28, width: "40%", background: T.inputBorder, borderRadius: 6 }} />
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon size={20} color={color} />
        </div>
        <span style={{ color: T.textMuted, fontSize: 13 }}>{label}</span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: T.textPrimary, marginBottom: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: T.textMuted }}>{sub}</div>}
    </div>
  );
}

function HotspotSkeleton() {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
        {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, height: 400 }} />
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, height: 400 }} />
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, padding: "12px 16px", boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }}>
      <p style={{ color: T.textPrimary, fontWeight: 600, margin: "0 0 4px", fontSize: 13 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0, fontSize: 12 }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
};

export default function CrimeHotspots({ user }) {
  const [hotspots, setHotspots] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [insights, setInsights] = useState([]);
  const [timeRange, setTimeRange] = useState("all");
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  const fetchHotspots = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { time_range: timeRange };
      if (search) params.search = search;
      if (priorityFilter) params.priority = priorityFilter;
      const data = await listHotspots(params);
      setHotspots(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load hotspot data");
      setHotspots(null);
    } finally {
      setLoading(false);
    }
  }, [timeRange, search, priorityFilter]);

  useEffect(() => { fetchHotspots(); }, [fetchHotspots]);

  useEffect(() => {
    getHotspotInsights()
      .then(d => setInsights(d.insights || []))
      .catch(() => {});
  }, []);

  const handleSelectDistrict = async (district) => {
    setDetailLoading(true);
    setDetail(null);
    try {
      const data = await getHotspotDetail(district);
      setDetail(data);
    } catch (e) {
      setDetail({ error: "Failed to load details" });
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!hotspots?.hotspots) return;
    const headers = "District,City,Area,Crime Count,Risk Score,Risk Level,Priority Cases,Pending Cases,Recent Cases,Last Incident\n";
    const rows = hotspots.hotspots.map(h =>
      `"${h.district}","${h.city}","${h.area}",${h.crime_count},${h.risk_score},${h.risk_level},${h.priority_count},${h.pending_count},${h.recent_count},"${h.last_incident || ""}"`
    ).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crime_hotspots_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const riskData = useMemo(() => {
    if (!hotspots?.hotspots) return [];
    const counts = { High: 0, Medium: 0, Low: 0 };
    hotspots.hotspots.forEach(h => { counts[h.risk_level] = (counts[h.risk_level] || 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [hotspots]);

  const topDistrictData = useMemo(() => {
    if (!hotspots?.hotspots) return [];
    return hotspots.hotspots.slice(0, 10).map(h => ({
      name: h.district,
      Crimes: h.crime_count,
      fill: RISK_COLORS[h.risk_level],
    }));
  }, [hotspots]);

  const trendData = useMemo(() => {
    if (!detail?.monthly_trend) return [];
    return detail.monthly_trend;
  }, [detail]);

  const crimeTypeData = useMemo(() => {
    if (!detail?.crime_types) return [];
    return detail.crime_types.slice(0, 8).map((ct, i) => ({
      name: ct.crime_type,
      value: ct.count,
      fill: PIE_COLORS[i % PIE_COLORS.length],
    }));
  }, [detail]);

  return (
    <PageShell title="Crime Hotspot Analysis" user={user}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        .hotspot-row { transition: all 0.15s ease; cursor: pointer; }
        .hotspot-row:hover { background: rgba(79, 140, 255, 0.08); }
      `}</style>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Crime Hotspot Analysis</h1>
          <p style={{ color: T.textMuted, fontSize: 13, marginTop: 4 }}>Dynamic crime concentration analysis from FIR data</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={fetchHotspots} style={{
            padding: "8px 16px", borderRadius: 10, border: `1px solid ${T.cardBorder}`,
            background: T.card, color: T.textSecondary, cursor: "pointer", fontSize: 13,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button onClick={handleExportCSV} style={{
            padding: "8px 16px", borderRadius: 10, border: `1px solid ${T.cardBorder}`,
            background: T.card, color: T.textSecondary, cursor: "pointer", fontSize: 13,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {loading && <HotspotSkeleton />}

      {error && !loading && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          minHeight: 300, textAlign: "center", background: T.card,
          border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 40,
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🗺</div>
          <p style={{ color: T.danger, fontSize: 15, marginBottom: 8 }}>{error}</p>
          <p style={{ color: T.textMuted, fontSize: 13, marginBottom: 20 }}>Unable to connect to the crime hotspot analysis service.</p>
          <button onClick={fetchHotspots} style={{
            padding: "10px 24px", borderRadius: 10, border: "none",
            background: T.accent, color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600,
          }}>Retry</button>
        </div>
      )}

      {!loading && !error && (!hotspots || hotspots.total_hotspots === 0) && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          minHeight: 400, textAlign: "center", background: T.card,
          border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 40,
        }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>🗺</div>
          <h3 style={{ color: T.textPrimary, fontSize: 18, margin: "0 0 8px" }}>No Hotspot Data Found</h3>
          <p style={{ color: T.textMuted, fontSize: 14, maxWidth: 400, lineHeight: 1.6 }}>
            Create FIR records with valid locations to generate hotspot analytics. Hotspot data is derived dynamically from FIR incidents and their associated locations.
          </p>
          <button onClick={fetchHotspots} style={{
            marginTop: 20, padding: "10px 24px", borderRadius: 10, border: `1px solid ${T.accent}`,
            background: "transparent", color: T.accent, cursor: "pointer", fontSize: 14, fontWeight: 600,
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <RefreshCw size={16} /> Refresh Data
          </button>
        </div>
      )}

      {!loading && !error && hotspots && hotspots.total_hotspots > 0 && (
        <div style={{ animation: "slideUp 0.3s ease" }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 16, marginBottom: 24,
          }}>
            <StatCard icon={MapPin} label="Total Hotspots" value={hotspots.total_hotspots} sub={`${hotspots.unique_districts} districts · ${hotspots.unique_cities} cities`} color="#4F8CFF" />
            <StatCard icon={AlertTriangle} label="High Risk Areas" value={hotspots.high_risk_count} sub="Require immediate attention" color="#EF4444" />
            <StatCard icon={Shield} label="Medium Risk" value={hotspots.medium_risk_count} sub="Under monitoring" color="#F59E0B" />
            <StatCard icon={TrendingUp} label="Low Risk" value={hotspots.low_risk_count} sub="Routine surveillance" color="#22C55E" />
          </div>

          <div style={{
            display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap",
            padding: 16, background: T.card, borderRadius: 12,
            border: `1px solid ${T.cardBorder}`, alignItems: "center",
          }}>
            <Filter size={16} color={T.textMuted} />
            <span style={{ color: T.textMuted, fontSize: 13, fontWeight: 600 }}>Filters:</span>
            <select value={timeRange} onChange={e => setTimeRange(e.target.value)}
              style={{
                padding: "6px 12px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
                background: T.inputBg, color: T.textPrimary, fontSize: 13,
              }}
            >
              {TIME_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}
              style={{
                padding: "6px 12px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
                background: T.inputBg, color: T.textPrimary, fontSize: 13,
              }}
            >
              <option value="">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <div style={{ flex: 1, minWidth: 200, position: "relative" }}>
              <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: T.textMuted }} />
              <input
                type="text"
                placeholder="Search district, city, area..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{
                  width: "100%", padding: "6px 12px 6px 32px", borderRadius: 8,
                  border: `1px solid ${T.cardBorder}`, background: T.inputBg,
                  color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box",
                }}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: detail ? "1.5fr 1fr" : "1fr", gap: 24, marginBottom: 24 }}>
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
              <div style={{ padding: "16px 20px", borderBottom: `1px solid ${T.cardBorder}` }}>
                <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>Top Crime Hotspots</h3>
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                      <th style={{ padding: "10px 16px", textAlign: "left", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>#</th>
                      <th style={{ padding: "10px 16px", textAlign: "left", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>District</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Crimes</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Risk Score</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Level</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Trend</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Pending</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Recent (30d)</th>
                      <th style={{ padding: "10px 16px", textAlign: "right", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Last Incident</th>
                    </tr>
                  </thead>
                  <tbody>{hotspots.hotspots.map((h, i) => {
                // Trend indicator: compare recent_count (30d) to expected monthly average
                const monthlyAvg = h.crime_count > 0 ? h.crime_count / 12 : 0;
                const trendRatio = monthlyAvg > 0 ? h.recent_count / monthlyAvg : 0;
                let trendIcon, trendColor, trendLabel;
                if (trendRatio >= 1.5) {
                  trendIcon = "↑"; trendColor = "#EF4444"; trendLabel = "Rising";
                } else if (trendRatio >= 0.5) {
                  trendIcon = "→"; trendColor = "#F59E0B"; trendLabel = "Active";
                } else {
                  trendIcon = "↓"; trendColor = "#22C55E"; trendLabel = "Stable";
                }
                return (
                      <tr
                        key={h.district + i}
                        className="hotspot-row"
                        onClick={() => handleSelectDistrict(h.district)}
                        style={{
                          borderBottom: `1px solid ${T.cardBorder}`,
                          background: detail?.district === h.district ? "rgba(79, 140, 255, 0.08)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "12px 16px", color: T.textMuted, fontSize: 12, fontWeight: 500, textAlign: "center" }}>{i + 1}</td>
                        <td style={{ padding: "12px 16px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <div style={{
                              width: 8, height: 8, borderRadius: "50%",
                              background: RISK_COLORS[h.risk_level],
                              flexShrink: 0,
                            }} />
                            <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{h.district}</span>
                          </div>
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "center", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{h.crime_count}</td>
                        <td style={{ padding: "12px 16px", textAlign: "center" }}>
                          <div style={{
                            display: "inline-flex", alignItems: "center", gap: 4,
                            padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600,
                            background: h.risk_level === "High" ? "rgba(239,68,68,0.15)" : h.risk_level === "Medium" ? "rgba(245,158,11,0.15)" : "rgba(34,197,94,0.15)",
                            color: RISK_COLORS[h.risk_level],
                          }}>
                            {h.risk_score}
                          </div>
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "center" }}>
                          <span style={{
                            padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600,
                            background: h.risk_level === "High" ? "rgba(239,68,68,0.15)" : h.risk_level === "Medium" ? "rgba(245,158,11,0.15)" : "rgba(34,197,94,0.15)",
                            color: RISK_COLORS[h.risk_level],
                          }}>{h.risk_level}</span>
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "center" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 3, color: trendColor, fontSize: 13, fontWeight: 600 }}>
                            {trendIcon} {trendLabel}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "center", color: T.textSecondary, fontSize: 13 }}>{h.pending_count}</td>
                        <td style={{ padding: "12px 16px", textAlign: "center", color: T.textSecondary, fontSize: 13 }}>{h.recent_count}</td>
                        <td style={{ padding: "12px 16px", textAlign: "right", color: T.textMuted, fontSize: 12 }}>
                          {h.last_incident ? h.last_incident.slice(0, 10) : "—"}
                        </td>
                      </tr>
                );})}
                  </tbody>
                </table>
              </div>
            </div>

            {detail && (
              <div style={{
                background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16,
                animation: "slideUp 0.3s ease", maxHeight: "calc(100vh - 300px)", overflowY: "auto",
              }}>
                <div style={{
                  padding: "16px 20px", borderBottom: `1px solid ${T.cardBorder}`,
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  position: "sticky", top: 0, background: T.card, zIndex: 1,
                }}>
                  <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>
                    {detail.error ? "Error" : `${detail.district} Details`}
                  </h3>
                  <button onClick={() => setDetail(null)} style={{
                    padding: 4, borderRadius: 6, border: "none", background: "transparent",
                    color: T.textMuted, cursor: "pointer",
                  }}><X size={16} /></button>
                </div>

                {detailLoading ? (
                  <div style={{ padding: 20 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} style={{ height: 14, background: T.inputBorder, borderRadius: 4, marginBottom: 12, width: `${60 + i * 10}%` }} />)}
                  </div>
                ) : detail.error ? (
                  <div style={{ padding: 20, textAlign: "center", color: T.danger, fontSize: 13 }}>
                    {detail.error}
                  </div>
                ) : (
                  <div style={{ padding: 20 }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
                      <div style={{ background: T.inputBg, borderRadius: 10, padding: 12, textAlign: "center" }}>
                        <div style={{ color: T.textMuted, fontSize: 11, marginBottom: 4 }}>Total Crimes</div>
                        <div style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700 }}>{detail.crime_count}</div>
                      </div>
                      <div style={{ background: T.inputBg, borderRadius: 10, padding: 12, textAlign: "center" }}>
                        <div style={{ color: T.textMuted, fontSize: 11, marginBottom: 4 }}>Risk Score</div>
                        <div style={{ color: RISK_COLORS[detail.risk_level], fontSize: 20, fontWeight: 700 }}>{detail.risk_score}</div>
                      </div>
                    </div>

                    {crimeTypeData.length > 0 && (
                      <div style={{ marginBottom: 16 }}>
                        <h4 style={{ color: T.textMuted, fontSize: 12, fontWeight: 600, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 0.5 }}>Crime Types</h4>
                        <ResponsiveContainer width="100%" height={180}>
                          <PieChart>
                            <Pie data={crimeTypeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={40}>
                              {crimeTypeData.map((entry, i) => (
                                <Cell key={i} fill={entry.fill} />
                              ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                          </PieChart>
                        </ResponsiveContainer>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center" }}>
                          {crimeTypeData.slice(0, 5).map((ct, i) => (
                            <span key={i} style={{ fontSize: 11, color: T.textMuted, display: "flex", alignItems: "center", gap: 4 }}>
                              <span style={{ width: 8, height: 8, borderRadius: "50%", background: ct.fill, display: "inline-block" }} />
                              {ct.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {trendData.length > 0 && (
                      <div style={{ marginBottom: 16 }}>
                        <h4 style={{ color: T.textMuted, fontSize: 12, fontWeight: 600, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 0.5 }}>Monthly Trend</h4>
                        <ResponsiveContainer width="100%" height={140}>
                          <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.cardBorder} />
                            <XAxis dataKey="month" tick={{ fontSize: 10, fill: T.textMuted }} />
                            <YAxis tick={{ fontSize: 10, fill: T.textMuted }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Line type="monotone" dataKey="count" stroke="#4F8CFF" strokeWidth={2} dot={{ fill: "#4F8CFF", r: 3 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {detail.ai_insight && (
                      <div style={{
                        padding: 12, borderRadius: 10, marginTop: 8,
                        background: detail.risk_level === "High" ? "rgba(239,68,68,0.08)" : detail.risk_level === "Medium" ? "rgba(245,158,11,0.08)" : "rgba(34,197,94,0.08)",
                        border: `1px solid ${detail.risk_level === "High" ? "rgba(239,68,68,0.2)" : detail.risk_level === "Medium" ? "rgba(245,158,11,0.2)" : "rgba(34,197,94,0.2)"}`,
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                          <AlertTriangle size={14} color={RISK_COLORS[detail.risk_level]} />
                          <span style={{ color: RISK_COLORS[detail.risk_level], fontSize: 12, fontWeight: 600 }}>AI Insight</span>
                        </div>
                        <p style={{ color: T.textSecondary, fontSize: 12, lineHeight: 1.5, margin: 0 }}>
                          {detail.ai_insight}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: 24, marginBottom: 24 }}>
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20 }}>
              <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: "0 0 16px" }}>Top 10 Crime Districts</h3>
              {topDistrictData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={topDistrictData} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={T.cardBorder} horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: T.textMuted }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: T.textMuted }} width={80} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="Crimes" radius={[0, 4, 4, 0]}>
                      {topDistrictData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ height: 300, display: "flex", alignItems: "center", justifyContent: "center", color: T.textMuted, fontSize: 13 }}>
                  Insufficient data for chart
                </div>
              )}
            </div>

            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20 }}>
              <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: "0 0 16px" }}>Risk Distribution</h3>
              {riskData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={55}>
                        {riskData.map((entry, i) => (
                          <Cell key={i} fill={RISK_COLORS[entry.name]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 8 }}>
                    {riskData.map((r, i) => (
                      <div key={i} style={{ textAlign: "center" }}>
                        <div style={{ color: RISK_COLORS[r.name], fontSize: 18, fontWeight: 700 }}>{r.value}</div>
                        <div style={{ color: T.textMuted, fontSize: 11 }}>{r.name}</div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ height: 250, display: "flex", alignItems: "center", justifyContent: "center", color: T.textMuted, fontSize: 13 }}>
                  Insufficient data for chart
                </div>
              )}
            </div>
          </div>

          {insights.length > 0 && (
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                <div style={{ width: 32, height: 32, borderRadius: 10, background: "rgba(79,140,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <AlertTriangle size={16} color="#4F8CFF" />
                </div>
                <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>AI Hotspot Intelligence</h3>
              </div>
              <div style={{ display: "grid", gap: 12 }}>
                {insights.map((insight, i) => (
                  <div key={i} style={{
                    padding: 14, borderRadius: 12,
                    background: insight.impact === "danger" ? "rgba(239,68,68,0.08)" : insight.impact === "warning" ? "rgba(245,158,11,0.08)" : "rgba(79,140,255,0.08)",
                    border: `1px solid ${
                      insight.impact === "danger" ? "rgba(239,68,68,0.2)" :
                      insight.impact === "warning" ? "rgba(245,158,11,0.2)" :
                      "rgba(79,140,255,0.2)"
                    }`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{
                        width: 6, height: 6, borderRadius: "50%",
                        background: insight.impact === "danger" ? "#EF4444" : insight.impact === "warning" ? "#F59E0B" : "#4F8CFF",
                      }} />
                      <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{insight.district}</span>
                    </div>
                    <p style={{ color: T.textSecondary, fontSize: 12, lineHeight: 1.5, margin: "0 0 0 14px" }}>{insight.insight}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}
