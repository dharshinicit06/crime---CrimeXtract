import { useState, useEffect, useCallback } from "react";
import { T } from "../styles/theme";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import { getDashboard } from "../services/analyticsService";
import { listFIRs } from "../services/firService";
import { FileText, Download, Calendar, User, MapPin, Shield, TrendingUp, AlertTriangle, X, Printer } from "lucide-react";

const REPORT_TYPES = [
  { id: "executive", label: "Executive Summary", icon: FileText, desc: "High-level crime statistics and trends" },
  { id: "monthly", label: "Monthly Crime Report", icon: Calendar, desc: "Detailed monthly crime breakdown" },
  { id: "district", label: "District Analysis", icon: MapPin, desc: "District-wise crime comparison" },
  { id: "hotspot", label: "Hotspot Report", icon: AlertTriangle, desc: "Crime hotspot risk assessment" },
  { id: "performance", label: "Officer Performance", icon: Shield, desc: "Investigation clearance rates" },
];

function formatDate(d) {
  if (!d) return "—";
  const date = typeof d === "string" ? new Date(d) : d;
  return date.toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function Reports({ user }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [recentFIRs, setRecentFIRs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [reportContent, setReportContent] = useState(null);
  const [activeTab, setActiveTab] = useState("generate");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [dash, firs] = await Promise.all([
        getDashboard().catch(() => null),
        listFIRs({ page_size: 50, sort_by: "created_at", sort_order: "desc" }).catch(() => ({ items: [] })),
      ]);
      setDashboardData(dash);
      setRecentFIRs(firs.items || []);
    } catch (e) {
      console.error("Failed to load report data", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const generateReport = async (reportType) => {
    setSelectedReport(reportType);
    setGenerating(true);
    setReportContent(null);

    // Simulate generation delay for UX
    await new Promise((r) => setTimeout(r, 600));

    const now = new Date();
    const summary = dashboardData?.summary || {};
    const crimeByType = dashboardData?.crime_by_type || {};
    const topHotspots = dashboardData?.top_hotspots || {};

    let content = { title: "", sections: [], generatedAt: now, generatedBy: user?.name || "Officer" };

    switch (reportType.id) {
      case "executive":
        content.title = "Executive Crime Summary";
        content.sections = [
          {
            heading: "Overview",
            items: [
              { label: "Total FIRs Registered", value: summary.total_firs || 0 },
              { label: "Cases Solved", value: summary.solved_count || 0 },
              { label: "Pending Investigations", value: summary.pending_count || 0 },
              { label: "Clearance Rate", value: `${summary.conviction_rate || 0}%` },
              { label: "Active Districts", value: summary.unique_districts || 0 },
              { label: "Period", value: summary.time_period || "All time" },
            ],
          },
          {
            heading: "Crime Type Distribution",
            items: (crimeByType.labels || []).slice(0, 8).map((label, i) => ({
              label,
              value: (crimeByType.datasets?.[0]?.data?.[i]) || 0,
            })),
          },
          {
            heading: "Top Crime Hotspots",
            items: (topHotspots.labels || []).slice(0, 5).map((label, i) => ({
              label,
              value: (topHotspots.datasets?.[0]?.data?.[i]) || 0,
            })),
          },
        ];
        break;

      case "monthly":
        content.title = "Monthly Crime Report";
        const monthly = dashboardData?.crime_by_month || {};
        content.sections = [
          {
            heading: "Monthly Crime Trend",
            items: (monthly.labels || []).slice(-12).map((label, i) => {
              const data = monthly.datasets?.[0]?.data || [];
              const dataSlice = data.slice(-12);
              return { label, value: dataSlice[i] || 0 };
            }),
          },
          {
            heading: "Summary",
            items: [
              { label: "Total (shown period)", value: ((monthly.datasets?.[0]?.data || []).slice(-12).reduce((a, b) => a + b, 0)) },
              { label: "Monthly Average", value: Math.round(((monthly.datasets?.[0]?.data || []).slice(-12).reduce((a, b) => a + b, 0) / Math.max((monthly.labels || []).slice(-12).length, 1))) },
            ],
          },
        ];
        break;

      case "district":
        content.title = "District Crime Analysis";
        const districtData = dashboardData?.top_hotspots || {};
        content.sections = [
          {
            heading: "Crime by District",
            items: (districtData.labels || []).slice(0, 10).map((label, i) => ({
              label,
              value: (districtData.datasets?.[0]?.data?.[i]) || 0,
            })),
          },
          {
            heading: "Coverage",
            items: [
              { label: "Total Districts", value: summary.unique_districts || 0 },
              { label: "Total FIRs (all)", value: summary.total_firs || 0 },
            ],
          },
        ];
        break;

      case "hotspot":
        content.title = "Crime Hotspot Risk Assessment";
        content.sections = [
          {
            heading: "High-Risk Areas",
            items: (topHotspots.labels || []).slice(0, 5).map((label, i) => ({
              label,
              value: (topHotspots.datasets?.[0]?.data?.[i]) || 0,
            })),
          },
          {
            heading: "Risk Metrics",
            items: [
              { label: "High Risk Districts", value: "Requires immediate patrol allocation" },
              { label: "Trend", value: "Monitor weekly for rising patterns" },
              { label: "Recommendation", value: "Increase surveillance in top 3 areas" },
            ],
          },
        ];
        break;

      case "performance":
        content.title = "Officer Performance Report";
        content.sections = [
          {
            heading: "Recent FIRs & Assignments",
            items: recentFIRs.slice(0, 10).map((f) => ({
              label: f.fir_number || `#${f.fir_id}`,
              value: `${f.title || "No title"} — ${f.investigation_status || "Pending"}`,
            })),
          },
          {
            heading: "Overall Statistics",
            items: [
              { label: "Total Cases", value: summary.total_firs || 0 },
              { label: "Solved", value: summary.solved_count || 0 },
              { label: "Clearance Rate", value: `${summary.conviction_rate || 0}%` },
            ],
          },
        ];
        break;

      default:
        content.title = "Crime Intelligence Report";
        content.sections = [{ heading: "Data", items: [{ label: "Status", value: "Report generated" }] }];
    }

    setReportContent(content);
    setGenerating(false);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadText = () => {
    if (!reportContent) return;
    let text = `${reportContent.title}\n${"=".repeat(reportContent.title.length)}\n\n`;
    text += `Generated: ${formatDate(reportContent.generatedAt)}\n`;
    text += `Officer: ${reportContent.generatedBy}\n\n`;
    reportContent.sections.forEach((section) => {
      text += `${section.heading}\n${"-".repeat(section.heading.length)}\n`;
      section.items.forEach((item) => {
        text += `${item.label}: ${item.value}\n`;
      });
      text += "\n";
    });
    text += `${"-".repeat(40)}\n`;
    text += `Crime Intelligence Platform — Karnataka SCRB\n`;
    text += `Report ID: RPT-${Date.now().toString(36).toUpperCase()}\n`;

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportContent.title.replace(/\s+/g, "_")}_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageShell title="Reports" user={user}>
      <style>{`
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @media print {
          .no-print { display: none !important; }
          body { background: #fff !important; color: #000 !important; }
        }
      `}</style>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Reports & Analytics</h1>
          <p style={{ color: T.textMuted, fontSize: 13, marginTop: 4 }}>Generate crime intelligence reports with officer details and summaries</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: 0, marginBottom: 24, background: T.card, borderRadius: 12, border: `1px solid ${T.cardBorder}`, overflow: "hidden" }}>
        {["generate", "history"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="no-print"
            style={{
              flex: 1, padding: "12px 20px", border: "none", cursor: "pointer", fontSize: 14, fontWeight: 600,
              background: activeTab === tab ? T.accentGlow : "transparent",
              color: activeTab === tab ? T.accent : T.textSecondary,
              transition: "all 0.2s",
            }}
          >
            {tab === "generate" ? "Generate Report" : "Recent Reports"}
          </button>
        ))}
      </div>

      {activeTab === "generate" && (
        <div style={{ animation: "slideUp 0.3s ease" }}>
          {/* Report Type Selection */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
            {REPORT_TYPES.map((rt) => {
              const Icon = rt.icon;
              const isSelected = selectedReport?.id === rt.id;
              return (
                <button
                  key={rt.id}
                  onClick={() => generateReport(rt)}
                  disabled={generating}
                  className="no-print"
                  style={{
                    padding: 20, borderRadius: 16, cursor: "pointer", textAlign: "left",
                    border: isSelected ? `2px solid ${T.accent}` : `1px solid ${T.cardBorder}`,
                    background: isSelected ? T.accentGlow : T.card,
                    transition: "all 0.2s", opacity: generating ? 0.6 : 1,
                    display: "flex", flexDirection: "column", gap: 10,
                  }}
                >
                  <div style={{ width: 40, height: 40, borderRadius: 12, background: `${T.accent}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={20} color={T.accent} />
                  </div>
                  <div>
                    <div style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{rt.label}</div>
                    <div style={{ color: T.textMuted, fontSize: 12 }}>{rt.desc}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Loading State */}
          {generating && (
            <div style={{ textAlign: "center", padding: 40, background: T.card, borderRadius: 16, border: `1px solid ${T.cardBorder}`, marginBottom: 24 }}>
              <div style={{ fontSize: 32, marginBottom: 12, animation: "pulse 1s infinite" }}>📄</div>
              <p style={{ color: T.textSecondary, fontSize: 14 }}>Generating {selectedReport?.label}...</p>
            </div>
          )}

          {/* Report Content */}
          {reportContent && !generating && (
            <div style={{ animation: "slideUp 0.4s ease", marginBottom: 24 }}>
              <div style={{
                background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden",
              }}>
                {/* Report Header */}
                <div style={{
                  padding: "24px 28px", borderBottom: `1px solid ${T.cardBorder}`,
                  background: `linear-gradient(135deg, ${T.accent}08, ${T.purple}08)`,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
                    <div>
                      <h2 style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700, margin: "0 0 6px" }}>
                        {reportContent.title}
                      </h2>
                      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                        <span style={{ color: T.textMuted, fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                          <Calendar size={12} /> {formatDate(reportContent.generatedAt)}
                        </span>
                        <span style={{ color: T.textMuted, fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                          <User size={12} /> {reportContent.generatedBy}
                        </span>
                        <span style={{ color: T.textMuted, fontSize: 12 }}>
                          Karnataka Police · Crime Intelligence Platform
                        </span>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8 }} className="no-print">
                      <button onClick={handlePrint} style={{
                        padding: "8px 16px", borderRadius: 10, border: `1px solid ${T.cardBorder}`,
                        background: T.card, color: T.textSecondary, cursor: "pointer", fontSize: 12,
                        display: "flex", alignItems: "center", gap: 6,
                      }}>
                        <Printer size={14} /> Print
                      </button>
                      <button onClick={handleDownloadText} style={{
                        padding: "8px 16px", borderRadius: 10, border: "none",
                        background: T.accent, color: "#fff", cursor: "pointer", fontSize: 12,
                        display: "flex", alignItems: "center", gap: 6,
                      }}>
                        <Download size={14} /> Download
                      </button>
                    </div>
                  </div>
                </div>

                {/* Report Body */}
                <div style={{ padding: "20px 28px" }}>
                  {reportContent.sections.map((section, si) => (
                    <div key={si} style={{ marginBottom: si < reportContent.sections.length - 1 ? 24 : 0 }}>
                      <h3 style={{
                        color: T.textPrimary, fontSize: 14, fontWeight: 600, margin: "0 0 12px",
                        paddingBottom: 8, borderBottom: `1px solid ${T.cardBorder}`,
                      }}>
                        {section.heading}
                      </h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {section.items.map((item, ii) => (
                          <div key={ii} style={{
                            display: "flex", justifyContent: "space-between", alignItems: "center",
                            padding: "8px 0", borderBottom: ii < section.items.length - 1 ? `1px solid ${T.cardBorder}` : "none",
                          }}>
                            <span style={{ color: T.textSecondary, fontSize: 13 }}>{item.label}</span>
                            <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600, textAlign: "right", maxWidth: "60%" }}>
                              {typeof item.value === "number" ? item.value.toLocaleString() : item.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Report Footer */}
                <div style={{
                  padding: "16px 28px", borderTop: `1px solid ${T.cardBorder}`,
                  background: T.inputBg, display: "flex", justifyContent: "space-between", alignItems: "center",
                  flexWrap: "wrap", gap: 8,
                }}>
                  <span style={{ color: T.textMuted, fontSize: 11 }}>
                    Report ID: RPT-{Date.now().toString(36).toUpperCase()} · Generated by CrimeAI Platform
                  </span>
                  <span style={{ color: T.textMuted, fontSize: 11 }}>
                    Karnataka State Crime Records Bureau
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Empty/Loading State */}
          {!selectedReport && !generating && (
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              minHeight: 200, textAlign: "center", background: T.card,
              border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 40,
            }}>
              <FileText size={48} color={T.textMuted} strokeWidth={1.5} />
              <h3 style={{ color: T.textPrimary, fontSize: 16, margin: "16px 0 8px" }}>Select a Report Type</h3>
              <p style={{ color: T.textMuted, fontSize: 13, maxWidth: 400 }}>
                Choose from the report types above to generate a detailed crime intelligence report with officer details and timestamps.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === "history" && (
        <div style={{ animation: "slideUp 0.3s ease" }}>
          {/* Recent FIRs as report history */}
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
            <div style={{ padding: "16px 20px", borderBottom: `1px solid ${T.cardBorder}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>Recent FIR Records</h3>
              <Badge label={loading ? "Loading" : `${recentFIRs.length} records`} />
            </div>

            {loading ? (
              <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>
                Loading report data...
              </div>
            ) : recentFIRs.length === 0 ? (
              <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>
                No FIR records found
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                      <th style={{ padding: "10px 16px", textAlign: "left", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>FIR #</th>
                      <th style={{ padding: "10px 16px", textAlign: "left", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Title</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Status</th>
                      <th style={{ padding: "10px 16px", textAlign: "center", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Priority</th>
                      <th style={{ padding: "10px 16px", textAlign: "right", color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentFIRs.map((f, i) => (
                      <tr key={f.fir_id || i} style={{ borderBottom: i < recentFIRs.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                        <td style={{ padding: "12px 16px", color: T.accent, fontSize: 13, fontWeight: 600 }}>{f.fir_number}</td>
                        <td style={{ padding: "12px 16px", color: T.textPrimary, fontSize: 13 }}>{f.title || "—"}</td>
                        <td style={{ padding: "12px 16px", textAlign: "center" }}>
                          <Badge label={f.investigation_status || "Pending"} />
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "center" }}>
                          <Badge label={f.priority || "Normal"} />
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "right", color: T.textMuted, fontSize: 12 }}>
                          {f.incident_date ? f.incident_date.slice(0, 10) : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Officer Info Summary */}
          {dashboardData?.summary && (
            <div style={{
              marginTop: 16, padding: 16, background: T.card, borderRadius: 12,
              border: `1px solid ${T.cardBorder}`, display: "flex", gap: 16, flexWrap: "wrap",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <User size={16} color={T.textMuted} />
                <span style={{ color: T.textMuted, fontSize: 12 }}>Officer: <strong style={{ color: T.textPrimary }}>{user?.name || user?.full_name || "N/A"}</strong></span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Calendar size={16} color={T.textMuted} />
                <span style={{ color: T.textMuted, fontSize: 12 }}>Period: <strong style={{ color: T.textPrimary }}>{dashboardData.summary.time_period || "All time"}</strong></span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Shield size={16} color={T.textMuted} />
                <span style={{ color: T.textMuted, fontSize: 12 }}>Clearance: <strong style={{ color: T.success }}>{dashboardData.summary.conviction_rate || 0}%</strong></span>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}
