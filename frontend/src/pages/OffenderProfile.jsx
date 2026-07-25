import { useState, useCallback, useMemo } from "react";
import { Search, User, AlertTriangle, Shield, FileText, MapPin, Scale, Clock, Activity, Zap, ChevronRight, X, TrendingUp, Users as UsersIcon, Eye } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import PageShell from "../components/PageShell";
import { getOffenderProfile } from "../services/offenderService";
import { T } from "../styles/theme";

const RISK_COLORS = { critical: "#EF4444", high: "#F59E0B", medium: "#4F8CFF", low: "#22C55E" };
const PIE_COLORS = ["#4F8CFF", "#EF4444", "#22C55E", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"];

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
      <div style={{ fontSize: 28, fontWeight: 700, color: T.textPrimary }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: T.textMuted, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function Section({ title, icon: Icon, color, children }) {
  return (
    <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden", marginBottom: 20 }}>
      <div style={{ padding: "16px 20px", borderBottom: `1px solid ${T.cardBorder}`, display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon size={14} color={color} />
        </div>
        <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>{title}</h3>
      </div>
      <div style={{ padding: 20 }}>{children}</div>
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

function SkeletonBlock({ height = 100, width = "100%" }) {
  return <div style={{ height, width, background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, animation: "pulse 2s infinite" }} />;
}

export default function OffenderProfile({ user }) {
  const [accusedId, setAccusedId] = useState("");
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = useCallback(async () => {
    if (!accusedId.trim()) return;
    setLoading(true);
    setError("");
    setProfile(null);
    try {
      const result = await getOffenderProfile(accusedId.trim());
      setProfile(result);
    } catch (e) {
      setError(e?.response?.data?.detail || "Offender not found. Enter a valid Accused ID.");
    } finally {
      setLoading(false);
    }
  }, [accusedId]);

  const handleKeyDown = (e) => { if (e.key === "Enter") search(); };

  const crimeTypeData = useMemo(() => {
    if (!profile?.previous_firs) return [];
    const counts = {};
    profile.previous_firs.forEach(f => {
      const cat = f.crime_category || "Unknown";
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return Object.entries(counts).slice(0, 8).map(([name, value], i) => ({
      name, value, fill: PIE_COLORS[i % PIE_COLORS.length],
    }));
  }, [profile]);

  const firStatusData = useMemo(() => {
    if (!profile?.statistics) return [];
    const s = profile.statistics;
    return [
      { name: "Active", value: s.active_firs, fill: "#F59E0B" },
      { name: "Solved", value: s.solved_firs, fill: "#22C55E" },
      { name: "Pending", value: s.pending_firs, fill: "#4F8CFF" },
    ].filter(d => d.value > 0);
  }, [profile]);

  const scorerData = useMemo(() => {
    if (!profile?.scorer_results) return [];
    return profile.scorer_results.map(s => ({
      name: s.name.replace(/_/g, " "),
      score: s.raw_score,
      fill: s.raw_score >= 75 ? "#EF4444" : s.raw_score >= 50 ? "#F59E0B" : s.raw_score >= 25 ? "#4F8CFF" : "#22C55E",
    }));
  }, [profile]);

  return (
    <PageShell title="Offender Profile" user={user}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        .timeline-item { transition: all 0.15s ease; }
        .timeline-item:hover { background: rgba(79, 140, 255, 0.05); }
      `}</style>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Offender Profile</h1>
          <p style={{ color: T.textMuted, fontSize: 13, marginTop: 4 }}>AI-powered criminal intelligence & risk assessment</p>
        </div>
      </div>

      {/* Search Bar */}
      <div style={{
        display: "flex", gap: 12, marginBottom: 24,
        padding: 16, background: T.card, borderRadius: 12,
        border: `1px solid ${T.cardBorder}`, alignItems: "center",
      }}>
        <Search size={16} color={T.textMuted} />
        <input
          type="text"
          placeholder="Enter Accused ID to search..."
          value={accusedId}
          onChange={e => setAccusedId(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{
            flex: 1, padding: "8px 12px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
            background: T.inputBg, color: T.textPrimary, fontSize: 14, outline: "none",
          }}
        />
        <button onClick={search} disabled={loading} style={{
          padding: "8px 20px", borderRadius: 8, border: "none",
          background: T.accent, color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600,
          display: "flex", alignItems: "center", gap: 6, opacity: loading ? 0.6 : 1,
        }}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Error State */}
      {error && !loading && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          minHeight: 300, textAlign: "center", background: T.card,
          border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 40,
        }}>
          <User size={48} color={T.danger} strokeWidth={1.5} />
          <p style={{ color: T.danger, fontSize: 15, margin: "16px 0 8px" }}>{error}</p>
          <p style={{ color: T.textMuted, fontSize: 13 }}>Enter a valid accused ID to search for an offender profile.</p>
        </div>
      )}

      {/* Loading Skeleton — only show if no previous data */}
      {loading && !profile && (
        <div style={{ display: "grid", gap: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
            {[1,2,3,4,5,6].map(i => <SkeletonBlock key={i} height={100} />)}
          </div>
          <SkeletonBlock height={200} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <SkeletonBlock height={300} />
            <SkeletonBlock height={300} />
          </div>
        </div>
      )}

      {/* Refreshing overlay — keep old profile visible */}
      {loading && profile && (
        <div style={{ position: "relative" }}>
          <div style={{ position: "absolute", top: 0, left: 0, right: 0, padding: 8, textAlign: "center", zIndex: 10, borderRadius: 8 }}>
            <span style={{ color: T.accent, fontSize: 12 }}>Updating...</span>
          </div>
        </div>
      )}

      {/* Profile Content */}
      {!loading && !error && profile && (
        <div style={{ animation: "slideUp 0.3s ease" }}>
          {/* Profile Header + Risk */}
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20, marginBottom: 20 }}>
            {/* Personal Info */}
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20, display: "flex", gap: 20, alignItems: "flex-start" }}>
              <div style={{
                width: 72, height: 72, borderRadius: 18,
                background: `linear-gradient(135deg, ${RISK_COLORS[profile.risk_level]}44, ${T.purple}44)`,
                border: `2px solid ${RISK_COLORS[profile.risk_level]}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 30, fontWeight: 700, color: T.textPrimary, flexShrink: 0,
              }}>
                {profile.name?.[0] || "?"}
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>{profile.name}</h2>
                <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
                  <span style={{
                    padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                    background: `${RISK_COLORS[profile.risk_level]}22`,
                    color: RISK_COLORS[profile.risk_level],
                  }}>
                    {profile.risk_level.toUpperCase()} RISK
                  </span>
                  {profile.gender && <span style={{ padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${T.textMuted}22`, color: T.textMuted }}>{profile.gender}</span>}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
                  {profile.age && <InfoRow label="Age" value={profile.age} />}
                  {profile.phone && <InfoRow label="Phone" value={profile.phone} />}
                  {profile.occupation && <InfoRow label="Occupation" value={profile.occupation} />}
                  {profile.city && <InfoRow label="City" value={profile.city} />}
                  {profile.district && <InfoRow label="District" value={profile.district} />}
                  {profile.address && <InfoRow label="Address" value={profile.address} span />}
                </div>
              </div>
            </div>

            {/* Risk Score Card */}
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                <AlertTriangle size={16} color={RISK_COLORS[profile.risk_level]} />
                <span style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600 }}>AI Risk Assessment</span>
              </div>
              <div style={{ textAlign: "center", marginBottom: 16 }}>
                <div style={{
                  width: 100, height: 100, borderRadius: "50%", margin: "0 auto 12px",
                  background: `conic-gradient(${RISK_COLORS[profile.risk_level]} ${profile.risk_score * 3.6}deg, ${T.inputBg} ${profile.risk_score * 3.6}deg)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  position: "relative",
                }}>
                  <div style={{
                    width: 80, height: 80, borderRadius: "50%", background: T.card,
                    display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column",
                  }}>
                    <span style={{ color: RISK_COLORS[profile.risk_level], fontSize: 22, fontWeight: 700 }}>{profile.risk_score}</span>
                    <span style={{ color: T.textMuted, fontSize: 10 }}>/100</span>
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                {[
                  { label: "Repeat", value: profile.statistics?.repeat_offender_score ? "Yes" : "No", color: profile.statistics?.repeat_offender_score ? "#EF4444" : "#22C55E" },
                  { label: "FIRs", value: profile.statistics?.total_firs || 0, color: "#4F8CFF" },
                  { label: "Co-accused", value: profile.statistics?.co_accused_count || 0, color: "#F59E0B" },
                ].map((item, i) => (
                  <div key={i} style={{ flex: 1, background: T.inputBg, borderRadius: 10, padding: 10, textAlign: "center" }}>
                    <div style={{ color: item.color, fontSize: 16, fontWeight: 700 }}>{item.value}</div>
                    <div style={{ color: T.textMuted, fontSize: 10 }}>{item.label}</div>
                  </div>
                ))}
              </div>
              {profile.recommendation && (
                <div style={{
                  padding: 10, borderRadius: 10,
                  background: profile.risk_level === "critical" ? "rgba(239,68,68,0.08)" : profile.risk_level === "high" ? "rgba(245,158,11,0.08)" : "rgba(79,140,255,0.08)",
                  border: `1px solid ${profile.risk_level === "critical" ? "rgba(239,68,68,0.2)" : profile.risk_level === "high" ? "rgba(245,158,11,0.2)" : "rgba(79,140,255,0.2)"}`,
                }}>
                  <p style={{ color: T.textSecondary, fontSize: 11, lineHeight: 1.5, margin: 0 }}>{profile.recommendation}</p>
                </div>
              )}
            </div>
          </div>

          {/* KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 20 }}>
            <StatCard icon={FileText} label="Total FIRs" value={profile.statistics?.total_firs || 0} color="#4F8CFF" />
            <StatCard icon={Activity} label="Active Cases" value={profile.statistics?.active_firs || 0} sub={profile.statistics ? `${profile.statistics.solved_firs} solved` : ""} color="#F59E0B" />
            <StatCard icon={Shield} label="Evidence Items" value={profile.statistics?.total_evidence || 0} color="#22C55E" />
            <StatCard icon={UsersIcon} label="Victims" value={profile.statistics?.total_victims || 0} color="#EC4899" />
            <StatCard icon={MapPin} label="Locations" value={profile.statistics?.unique_locations || 0} sub={profile.statistics?.most_common_district || ""} color="#8B5CF6" />
            <StatCard icon={Scale} label="Co-accused" value={profile.statistics?.co_accused_count || 0} color="#06B6D4" />
          </div>

          {/* Scorer Breakdown & Crime Categories */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
            <Section title="Risk Score Breakdown" icon={TrendingUp} color="#EF4444">
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {scorerData.map((s, i) => (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ color: T.textSecondary, fontSize: 12, textTransform: "capitalize" }}>{s.name}</span>
                      <span style={{ color: s.fill, fontSize: 12, fontWeight: 600 }}>{s.score}/100</span>
                    </div>
                    <div style={{ background: T.inputBorder, borderRadius: 4, height: 6 }}>
                      <div style={{ width: `${Math.min(s.score, 100)}%`, height: "100%", borderRadius: 4, background: s.fill, transition: "width 1s" }} />
                    </div>
                  </div>
                ))}
                {profile.scorer_results?.slice(0, 3).map((sr, i) => (
                  <div key={`reason-${i}`} style={{ padding: "8px 10px", background: T.inputBg, borderRadius: 8 }}>
                    <div style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textTransform: "uppercase", marginBottom: 2 }}>{sr.name.replace(/_/g, " ")}</div>
                    <div style={{ color: T.textSecondary, fontSize: 11 }}>{sr.reasoning}</div>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Crime Categories" icon={FileText} color="#4F8CFF">
              {crimeTypeData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={crimeTypeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={45}>
                        {crimeTypeData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center", marginTop: 8 }}>
                    {profile.crime_categories?.slice(0, 6).map((c, i) => (
                      <span key={i} style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${PIE_COLORS[i % PIE_COLORS.length]}22`, color: PIE_COLORS[i % PIE_COLORS.length] }}>
                        {c}
                      </span>
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: T.textMuted, fontSize: 13 }}>No crime categories recorded</div>
              )}
            </Section>
          </div>

          {/* FIR Timeline */}
          <Section title={`FIR History (${profile.previous_firs?.length || 0})`} icon={Clock} color="#F59E0B">
            {profile.previous_firs?.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                {profile.previous_firs.map((fir, i) => {
                  const statusColor = fir.status === "Solved" || fir.status === "Closed" ? "#22C55E"
                    : fir.status === "Under Investigation" ? "#F59E0B"
                    : fir.status === "Pending" ? "#4F8CFF" : T.textMuted;
                  return (
                    <div key={i} className="timeline-item" style={{
                      display: "flex", gap: 16, padding: "12px 0",
                      borderBottom: i < (profile.previous_firs?.length || 0) - 1 ? `1px solid ${T.cardBorder}` : "none",
                    }}>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                        <div style={{ width: 12, height: 12, borderRadius: "50%", background: statusColor, flexShrink: 0 }} />
                        {i < (profile.previous_firs?.length || 0) - 1 && <div style={{ width: 1, flex: 1, background: T.cardBorder }} />}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                          <div>
                            <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{fir.fir_number}</span>
                            {fir.title && <span style={{ color: T.textMuted, fontSize: 12, marginLeft: 8 }}>— {fir.title}</span>}
                          </div>
                          <span style={{ padding: "1px 8px", borderRadius: 12, fontSize: 10, fontWeight: 600, background: `${statusColor}22`, color: statusColor, whiteSpace: "nowrap" }}>
                            {fir.status}
                          </span>
                        </div>
                        <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
                          {fir.incident_date && <span style={{ color: T.textMuted, fontSize: 11 }}>{typeof fir.incident_date === "string" ? fir.incident_date.slice(0, 10) : String(fir.incident_date).slice(0, 10)}</span>}
                          {fir.crime_category && <span style={{ color: T.textMuted, fontSize: 11 }}>• {fir.crime_category}</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: "center", color: T.textMuted, fontSize: 13, padding: 20 }}>No FIR records linked to this offender</div>
            )}
          </Section>

          {/* Locations & Scorers Detail */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
            <Section title="Location Intelligence" icon={MapPin} color="#8B5CF6">
              {profile.locations?.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {profile.locations.slice(0, 5).map((loc, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "8px 10px", background: T.inputBg, borderRadius: 8 }}>
                      <div>
                        <div style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{loc.district}</div>
                        <div style={{ color: T.textMuted, fontSize: 11 }}>{loc.city}{loc.area ? `, ${loc.area}` : ""}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600 }}>{loc.fir_count}</div>
                        <div style={{ color: T.textMuted, fontSize: 10 }}>FIRs</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: "center", color: T.textMuted, fontSize: 13, padding: 20 }}>No location data available</div>
              )}
            </Section>

            <Section title="Score Details" icon={Eye} color="#06B6D4">
              {profile.scorer_results?.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {profile.scorer_results.map((sr, i) => (
                    <div key={i} style={{ padding: "8px 10px", background: T.inputBg, borderRadius: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                        <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600, textTransform: "capitalize" }}>{sr.name.replace(/_/g, " ")}</span>
                        <span style={{
                          color: sr.raw_score >= 75 ? "#EF4444" : sr.raw_score >= 50 ? "#F59E0B" : sr.raw_score >= 25 ? "#4F8CFF" : "#22C55E",
                          fontSize: 12, fontWeight: 600,
                        }}>
                          {sr.raw_score} (w: {sr.weight})
                        </span>
                      </div>
                      <div style={{ color: T.textMuted, fontSize: 11, lineHeight: 1.4 }}>{sr.reasoning}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: "center", color: T.textMuted, fontSize: 13, padding: 20 }}>No scoring data available</div>
              )}
            </Section>
          </div>

          {/* Reasoning Summary */}
          {profile.reasoning_summary && (
            <div style={{
              background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 16, marginBottom: 20,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                <Zap size={14} color="#8B5CF6" />
                <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>AI Reasoning Summary</span>
              </div>
              <p style={{ color: T.textSecondary, fontSize: 11, lineHeight: 1.6, margin: 0 }}>{profile.reasoning_summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!loading && !error && !profile && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          minHeight: 400, textAlign: "center", background: T.card,
          border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 40,
        }}>
          <User size={64} color={T.textMuted} strokeWidth={1.5} />
          <h3 style={{ color: T.textPrimary, fontSize: 18, margin: "16px 0 8px" }}>Search Offender Profile</h3>
          <p style={{ color: T.textMuted, fontSize: 14, maxWidth: 400, lineHeight: 1.6 }}>
            Enter an accused ID above to view their complete intelligence profile, including risk assessment, FIR history, evidence summary, location intelligence, and AI-powered recommendations.
          </p>
        </div>
      )}
    </PageShell>
  );
}

function InfoRow({ label, value, span }) {
  return (
    <div style={span ? { gridColumn: "1 / -1" } : {}}>
      <span style={{ color: T.textMuted, fontSize: 11, display: "block" }}>{label}</span>
      <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{value || "—"}</span>
    </div>
  );
}
