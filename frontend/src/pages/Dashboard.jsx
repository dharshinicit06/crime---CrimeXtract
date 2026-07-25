import { useState, useEffect, useCallback } from "react";
import { T } from "../styles/theme";
import { getDashboard } from "../services/analyticsService";
import PageShell from "../components/PageShell";
import StatCard from "../components/StatCard";
import Badge from "../components/Badge";

// ─── Helpers ──────────────────────────────────────────────────

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now - d;
  const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHrs < 1) return "Just now";
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

function StatusDot({ status }) {
  const s = (status || "").toLowerCase();
  const color = s.includes("closed") || s.includes("solved")
    ? T.success
    : s.includes("investigation")
    ? T.warning
    : s.includes("pending")
    ? T.textMuted
    : T.accent;
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: color,
        marginRight: 6,
        flexShrink: 0,
      }}
    />
  );
}

// ─── Skeleton Loader ──────────────────────────────────────────

function Skeleton({ width = "100%", height = 16, borderRadius = 6 }) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        background: `linear-gradient(90deg, ${T.card} 25%, ${T.cardBorder} 50%, ${T.card} 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s ease-in-out infinite",
      }}
    />
  );
}

// ─── Widget Frame ─────────────────────────────────────────────

function Widget({ title, children, loading, error, onRetry, action }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 24,
        display: "flex",
        flexDirection: "column",
        minHeight: 200,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <h3
          style={{
            color: T.textPrimary,
            fontWeight: 600,
            margin: 0,
            fontSize: 15,
          }}
        >
          {title}
        </h3>
        {action && action}
      </div>

      {error ? (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 12,
            padding: 20,
          }}
        >
          <span style={{ fontSize: 28 }}>⚠️</span>
          <p style={{ color: T.textMuted, fontSize: 13, textAlign: "center", margin: 0 }}>
            Failed to load data
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              style={{
                padding: "6px 16px",
                borderRadius: 8,
                border: `1px solid ${T.cardBorder}`,
                background: T.inputBg,
                color: T.accent,
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          )}
        </div>
      ) : loading ? (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12, justifyContent: "center" }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} height={14} />
          ))}
        </div>
      ) : (
        children
      )}
    </div>
  );
}

// ─── Bar Chart (simple) ───────────────────────────────────────

function SimpleBarChart({ data, labels }) {
  if (!data || data.length === 0) return null;
  const maxVal = Math.max(...data, 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {labels.map((label, i) => {
        const pct = ((data[i] || 0) / maxVal) * 100;
        return (
          <div key={i}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 4,
              }}
            >
              <span style={{ color: T.textSecondary, fontSize: 12 }}>{label}</span>
              <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
                {data[i] || 0}
              </span>
            </div>
            <div
              style={{
                background: T.inputBorder,
                borderRadius: 4,
                height: 6,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${pct}%`,
                  height: "100%",
                  borderRadius: 4,
                  background:
                    pct > 70
                      ? `linear-gradient(90deg, ${T.danger}, ${T.warning})`
                      : pct > 40
                      ? `linear-gradient(90deg, ${T.warning}, ${T.accent})`
                      : `linear-gradient(90deg, ${T.accent}, ${T.purple})`,
                  transition: "width 0.6s ease",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────

function EmptyState({ message = "No data available yet" }) {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 30,
        gap: 8,
      }}
    >
      <span style={{ fontSize: 32, opacity: 0.5 }}>📭</span>
      <p style={{ color: T.textMuted, fontSize: 13, margin: 0, textAlign: "center" }}>
        {message}
      </p>
    </div>
  );
}

// ─── Greeting helper ──────────────────────────────────────────

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

// ─── Main Dashboard Component ─────────────────────────────────

export default function Dashboard({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboard();
      setData(result);
    } catch (err) {
      console.error("Dashboard fetch failed:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const summary = data?.summary;
  const crimeByType = data?.crime_by_type;
  const crimeByMonth = data?.crime_by_month;
  const topHotspots = data?.top_hotspots;
  const recentFIRs = data?.recent_firs || [];

  const displayName = user?.name || user?.full_name || "Officer";
  const displayRole = user?.role || "Officer";
  const firstName = displayName.split(" ")[0];

  // Derived stats
  const statCards = loading
    ? [
        { icon: "📋", label: "Total FIRs", value: "—", sub: "Loading...", color: T.accent },
        { icon: "✅", label: "Solved", value: "—", sub: "Loading...", color: T.success },
        { icon: "⏳", label: "Pending", value: "—", sub: "Loading...", color: T.warning },
        { icon: "📈", label: "Conviction Rate", value: "—", sub: "Loading...", color: T.purple },
        { icon: "📍", label: "Districts", value: "—", sub: "Loading...", color: T.accent },
        { icon: "👥", label: "Users", value: "—", sub: "Loading...", color: T.textSecondary },
      ]
    : [
        {
          icon: "📋",
          label: "Total FIRs",
          value: (summary?.total_firs || 0).toLocaleString(),
          sub: `${summary?.unique_districts || 0} districts covered`,
          color: T.accent,
        },
        {
          icon: "✅",
          label: "Solved",
          value: (summary?.solved_count || 0).toLocaleString(),
          sub: `${summary?.conviction_rate || 0}% clearance rate`,
          color: T.success,
        },
        {
          icon: "⏳",
          label: "Pending",
          value: (summary?.pending_count || 0).toLocaleString(),
          sub: `${(100 - (summary?.conviction_rate || 0)).toFixed(1)}% open`,
          color: T.warning,
        },
        {
          icon: "📈",
          label: "Conviction Rate",
          value: `${summary?.conviction_rate || 0}%`,
          sub: summary?.time_period ? `Since ${summary.time_period.split(" to ")[0]}` : "All time",
          color: T.purple,
        },
        {
          icon: "📍",
          label: "Districts",
          value: (summary?.unique_districts || 0).toLocaleString(),
          sub: "Active jurisdictions",
          color: T.accent,
        },
        {
          icon: "👥",
          label: "Users",
          value: (data?.total_users || 0).toLocaleString(),
          sub: "Registered officers",
          color: T.textSecondary,
        },
      ];

  return (
    <PageShell title="Dashboard" user={user}>
      {/* Shimmer animation */}
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>

      <div style={{ width: "100%" }}>
        {/* ── Greeting ── */}
        <div style={{ marginBottom: 24 }}>
          <h1
            style={{
              color: T.textPrimary,
              fontSize: 22,
              fontWeight: 700,
              margin: "0 0 4px",
            }}
          >
            {getGreeting()}, {firstName} 👋
          </h1>
          <p style={{ color: T.textSecondary, fontSize: 14, margin: 0 }}>
            Karnataka Police · {displayRole} ·{" "}
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>

        {/* ── Global Error State ── */}
        {error && !loading && !data && (
          <div
            style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 12,
              padding: "20px 24px",
              marginBottom: 24,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 20 }}>🚨</span>
              <div>
                <p style={{ color: T.danger, fontSize: 14, fontWeight: 600, margin: 0 }}>
                  Failed to load dashboard
                </p>
                <p style={{ color: T.textMuted, fontSize: 12, margin: "2px 0 0" }}>
                  {error?.response?.data?.detail || error?.message || "Connection error"}
                </p>
              </div>
            </div>
            <button
              onClick={fetchDashboard}
              style={{
                padding: "8px 20px",
                borderRadius: 8,
                border: "none",
                background: T.danger,
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* ── Stat Cards ── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            gap: 16,
            marginBottom: 28,
            width: "100%",
          }}
        >
          {statCards.map((s, i) => (
            <StatCard key={i} {...s} />
          ))}
        </div>

        {/* ── Charts Grid ── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
            gap: 24,
            marginBottom: 24,
            width: "100%",
          }}
        >
          {/* Crime by Type */}
          <Widget
            title="Crime by Type"
            loading={loading}
            error={error && !data}
            onRetry={fetchDashboard}
          >
            {crimeByType?.labels?.length > 0 ? (
              <SimpleBarChart
                labels={crimeByType.labels.slice(0, 8)}
                data={crimeByType.datasets[0]?.data?.slice(0, 8) || []}
              />
            ) : (
              <EmptyState message="No crime type data recorded yet" />
            )}
          </Widget>

          {/* Monthly Trends */}
          <Widget
            title="Monthly Trends"
            loading={loading}
            error={error && !data}
            onRetry={fetchDashboard}
          >
            {crimeByMonth?.labels?.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {crimeByMonth.labels.slice(-6).map((label, i) => {
                  const allData = crimeByMonth.datasets[0]?.data || [];
                  const dataSlice = allData.slice(-6);
                  const val = dataSlice[i] || 0;
                  const maxV = Math.max(...dataSlice, 1);
                  const pct = (val / maxV) * 100;
                  return (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                      }}
                    >
                      <span
                        style={{
                          color: T.textMuted,
                          fontSize: 11,
                          width: 80,
                          flexShrink: 0,
                          textAlign: "right",
                        }}
                      >
                        {label}
                      </span>
                      <div
                        style={{
                          flex: 1,
                          background: T.inputBorder,
                          borderRadius: 4,
                          height: 20,
                          overflow: "hidden",
                          position: "relative",
                        }}
                      >
                        <div
                          style={{
                            width: `${pct}%`,
                            height: "100%",
                            borderRadius: 4,
                            background: `linear-gradient(90deg, ${T.accent}, ${T.purple})`,
                            transition: "width 0.6s ease",
                            minWidth: val > 0 ? 4 : 0,
                          }}
                        />
                      </div>
                      <span
                        style={{
                          color: T.textPrimary,
                          fontSize: 12,
                          fontWeight: 600,
                          width: 30,
                          textAlign: "right",
                        }}
                      >
                        {val}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState message="No monthly data yet" />
            )}
          </Widget>

          {/* Top Hotspots */}
          <Widget
            title="Top Hotspots"
            loading={loading}
            error={error && !data}
            onRetry={fetchDashboard}
          >
            {topHotspots?.labels?.length > 0 ? (
              <SimpleBarChart
                labels={topHotspots.labels}
                data={topHotspots.datasets[0]?.data || []}
              />
            ) : (
              <EmptyState message="No hotspot data yet" />
            )}
          </Widget>

          {/* Recent Activity / Alerts */}
          <Widget
            title="Recent Activity"
            loading={loading}
            error={error && !data}
            onRetry={fetchDashboard}
          >
            {recentFIRs.length > 0 ? (
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 0 }}>
                {recentFIRs.slice(0, 6).map((fir, i) => (
                  <div
                    key={fir.fir_id || i}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 10,
                      padding: "10px 0",
                      borderBottom:
                        i < Math.min(recentFIRs.length, 6) - 1
                          ? `1px solid ${T.cardBorder}`
                          : "none",
                    }}
                  >
                    <StatusDot status={fir.investigation_status} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          color: T.textPrimary,
                          fontSize: 13,
                          fontWeight: 500,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {fir.fir_number}
                        {fir.title ? ` — ${fir.title}` : ""}
                      </div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          marginTop: 2,
                        }}
                      >
                        <Badge label={fir.investigation_status || "Unknown"} />
                        <span style={{ color: T.textMuted, fontSize: 11 }}>
                          {timeAgo(fir.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState message="No recent FIR activity" />
            )}
          </Widget>
        </div>

        {/* ── Recent FIRs Table ── */}
        <Widget
          title="Recent FIRs"
          loading={loading}
          error={error && !data}
          onRetry={fetchDashboard}
          action={
            <Badge label={loading ? "Loading" : recentFIRs.length > 0 ? "Live" : "Empty"} />
          }
        >
          {recentFIRs.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    {["FIR #", "Title", "Priority", "Status", "Date"].map((h) => (
                      <th
                        key={h}
                        style={{
                          color: T.textMuted,
                          fontSize: 11,
                          fontWeight: 600,
                          textAlign: "left",
                          padding: "0 12px 12px 0",
                          textTransform: "uppercase",
                          letterSpacing: "0.5px",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentFIRs.map((f) => (
                    <tr key={f.fir_id}>
                      <td
                        style={{
                          padding: "10px 12px 10px 0",
                          color: T.accent,
                          fontSize: 13,
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {f.fir_number}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px 10px 0",
                          color: T.textPrimary,
                          fontSize: 13,
                          maxWidth: 200,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {f.title || "—"}
                      </td>
                      <td style={{ padding: "10px 12px 10px 0", whiteSpace: "nowrap" }}>
                        <Badge label={f.priority || "Normal"} />
                      </td>
                      <td style={{ padding: "10px 12px 10px 0", whiteSpace: "nowrap" }}>
                        <Badge label={f.investigation_status || "Pending"} />
                      </td>
                      <td
                        style={{
                          padding: "10px 12px 10px 0",
                          color: T.textSecondary,
                          fontSize: 13,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {f.incident_date || f.created_at?.split("T")[0] || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            !loading && (
              <div
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 30,
                  gap: 8,
                }}
              >
                <span style={{ fontSize: 32, opacity: 0.5 }}>📋</span>
                <p
                  style={{
                    color: T.textMuted,
                    fontSize: 13,
                    margin: 0,
                    textAlign: "center",
                  }}
                >
                  No FIRs registered yet
                </p>
              </div>
            )
          )}
        </Widget>
      </div>
    </PageShell>
  );
}
