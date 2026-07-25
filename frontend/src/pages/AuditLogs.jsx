import { useState, useEffect } from "react";
import { T } from "../styles/theme";
import { listAuditLogs, getAuditLog, getAuditStats } from "../services/auditLogService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Input from "../components/Input";

export default function AuditLogs({ user }) {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  const [search, setSearch] = useState("");

  const fetchAll = async () => {
    setLoading(true); setError("");
    try {
      const [l, s] = await Promise.all([
        listAuditLogs({ page_size: 100 }).catch(() => ({ items: [] })),
        getAuditStats().catch(() => null),
      ]);
      setLogs(l.items || []);
      setStats(s);
    } catch { setError("Failed to load audit logs"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const filtered = search
    ? logs.filter((l) =>
        [l.action, l.table_name, l.record_id?.toString(), l.ip_address]
          .some((v) => v?.toLowerCase().includes(search.toLowerCase()))
      )
    : logs;

  return (
    <PageShell title="Audit Logs" user={user}>
      {stats && (
        <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 140 }}>
            <div style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Total Entries</div>
            <div style={{ color: T.accent, fontSize: 24, fontWeight: 700, marginTop: 4 }}>{stats.total_logs ?? logs.length}</div>
          </div>
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 140 }}>
            <div style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Unique Users</div>
            <div style={{ color: T.success, fontSize: 24, fontWeight: 700, marginTop: 4 }}>{stats.unique_users ?? "—"}</div>
          </div>
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 140 }}>
            <div style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Tables Tracked</div>
            <div style={{ color: T.purple, fontSize: 24, fontWeight: 700, marginTop: 4 }}>{stats.tables_tracked ?? "—"}</div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: 20, maxWidth: 320 }}>
        <Input placeholder="Search by action, table, IP..." value={search} onChange={(e) => setSearch(e.target.value)} icon="🔍" />
      </div>

      {selectedLog && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: 0, fontSize: 15 }}>Audit Log Details</h3>
            <button onClick={() => setSelectedLog(null)} style={{ background: "none", border: "none", color: T.textMuted, cursor: "pointer", fontSize: 18 }}>✕</button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {[
              ["Log ID", selectedLog.audit_log_id ?? selectedLog.id],
              ["Action", selectedLog.action],
              ["Table", selectedLog.table_name],
              ["Record ID", selectedLog.record_id],
              ["User ID", selectedLog.user_id],
              ["IP Address", selectedLog.ip_address],
              ["Timestamp", selectedLog.log_time ?? selectedLog.created_at],
              ["Details", selectedLog.details ? JSON.stringify(selectedLog.details, null, 2) : "—"],
            ].map(([label, value]) => (
              <div key={label}>
                <div style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
                <div style={{ color: T.textPrimary, fontSize: 13, marginTop: 4, fontFamily: label === "Details" && value !== "—" ? "monospace" : "inherit", whiteSpace: "pre-wrap" }}>{value ?? "—"}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading audit logs...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>{search ? "No matching logs" : "No audit logs found"}</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                {["Action", "Table", "Record ID", "User", "IP Address", "Timestamp", ""].map((h) => (
                  <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((l, i) => {
                const lid = l.audit_log_id ?? l.id ?? i;
                return (
                  <tr key={lid} style={{ borderBottom: i < filtered.length - 1 ? `1px solid ${T.cardBorder}` : "none", cursor: "pointer" }} onClick={() => setSelectedLog(l)}>
                    <td style={{ padding: "14px 20px" }}><Badge label={l.action} /></td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{l.table_name}</td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{l.record_id ?? "—"}</td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>#{l.user_id ?? "—"}</td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12, fontFamily: "monospace" }}>{l.ip_address || "—"}</td>
                    <td style={{ padding: "14px 20px", color: T.textMuted, fontSize: 11 }}>{l.log_time?.split(".")[0]?.replace("T", " ") || "—"}</td>
                    <td style={{ padding: "14px 20px", color: T.accent, fontSize: 11 }}>View →</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </PageShell>
  );
}
