import { useState, useEffect, useCallback } from "react";
import { T } from "../styles/theme";
import {
  listFIRs, createFIR, deleteFIR, getFIRStatistics,
} from "../services/firService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import { Toast } from "../styles/shared";

const STATUSES = ["All", "Pending", "Under Investigation", "Solved", "Closed"];

const STYLE = {
  modalOverlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000, padding: 20,
  },
  modalContent: {
    background: T.card, border: `1px solid ${T.cardBorder}`,
    borderRadius: 16, width: "100%", maxWidth: 520,
    maxHeight: "90vh", overflow: "auto", animation: "slideUp 0.25s ease",
  },
  input: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none",
    boxSizing: "border-box",
  },
  label: { display: "block", color: T.textSecondary, fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" },
  select: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none", cursor: "pointer",
    boxSizing: "border-box",
  },
};

// ═══════════════════════════════════════════════════════════════
// CREATE FIR MODAL
// ═══════════════════════════════════════════════════════════════

function CreateFIRModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "", description: "", incident_date: "",
    crime_type: "", location: "", officer: "",
    priority: "Medium",
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!form.title.trim()) errs.title = "Title is required";
    if (!form.description.trim()) errs.description = "Description is required";
    if (!form.incident_date) errs.incident_date = "Incident date is required";
    if (!form.crime_type.trim()) errs.crime_type = "Crime type is required";
    if (!form.location.trim()) errs.location = "Location is required";
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setError("Please correct the highlighted fields before submitting."); return; }
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        title: form.title,
        description: form.description,
        incident_date: form.incident_date,
        crime_type: form.crime_type,
        location: form.location,
        officer: form.officer || null,
        priority: form.priority,
      };
      await createFIR(payload);
      onCreated();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to create FIR");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={STYLE.modalContent}>
        <div style={{ padding: "20px 24px", borderBottom: `1px solid ${T.cardBorder}` }}>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: 0 }}>Register New FIR</h2>
          <p style={{ color: T.textMuted, fontSize: 12, margin: "4px 0 0" }}>Enter incident details to file a new FIR</p>
        </div>
        <form onSubmit={handleSubmit} style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
          {error && (
            <div style={{ padding: "10px 14px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, color: T.danger, fontSize: 13 }}>{error}</div>
          )}
          <div>
            <label style={STYLE.label}>Title *</label>
            <input style={{ ...STYLE.input, borderColor: fieldErrors.title ? T.danger : T.inputBorder }} value={form.title} onChange={(e) => handleChange("title", e.target.value)} placeholder="Brief incident title" />
            {fieldErrors.title && <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0" }}>{fieldErrors.title}</p>}
          </div>
          <div>
            <label style={STYLE.label}>Description *</label>
            <textarea style={{ ...STYLE.input, minHeight: 80, resize: "vertical", borderColor: fieldErrors.description ? T.danger : T.inputBorder }} value={form.description} onChange={(e) => handleChange("description", e.target.value)} placeholder="Detailed description of the incident" />
            {fieldErrors.description && <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0" }}>{fieldErrors.description}</p>}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={STYLE.label}>Incident Date *</label>
              <input type="date" style={{ ...STYLE.input, borderColor: fieldErrors.incident_date ? T.danger : T.inputBorder }} value={form.incident_date} onChange={(e) => handleChange("incident_date", e.target.value)} />
              {fieldErrors.incident_date && <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0" }}>{fieldErrors.incident_date}</p>}
            </div>
            <div>
              <label style={STYLE.label}>Priority</label>
              <select style={STYLE.select} value={form.priority} onChange={(e) => handleChange("priority", e.target.value)}>
                {["Low", "Medium", "High", "Critical"].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label style={STYLE.label}>Crime Type *</label>
            <input style={{ ...STYLE.input, borderColor: fieldErrors.crime_type ? T.danger : T.inputBorder }} value={form.crime_type} onChange={(e) => handleChange("crime_type", e.target.value)} placeholder="e.g. Theft, Cyber Fraud, Assault" />
            {fieldErrors.crime_type && <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0" }}>{fieldErrors.crime_type}</p>}
          </div>
          <div>
            <label style={STYLE.label}>Location *</label>
            <input style={{ ...STYLE.input, borderColor: fieldErrors.location ? T.danger : T.inputBorder }} value={form.location} onChange={(e) => handleChange("location", e.target.value)} placeholder="e.g. Bengaluru Urban, Mysuru" />
            {fieldErrors.location && <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0" }}>{fieldErrors.location}</p>}
          </div>
          <div>
            <label style={STYLE.label}>Investigating Officer</label>
            <input style={STYLE.input} value={form.officer} onChange={(e) => handleChange("officer", e.target.value)} placeholder="e.g. Inspector Ravi or badge number" />
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 4 }}>
            <button type="button" onClick={onClose} style={{
              padding: "10px 20px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
              background: T.inputBg, color: T.textSecondary, fontSize: 13, cursor: "pointer",
            }}>Cancel</button>
            <button type="submit" disabled={submitting} style={{
              padding: "10px 20px", borderRadius: 8, border: "none",
              background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff",
              fontSize: 13, fontWeight: 600, cursor: submitting ? "not-allowed" : "pointer", opacity: submitting ? 0.6 : 1,
            }}>{submitting ? "Registering..." : "Register FIR"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// DELETE CONFIRMATION MODAL
// ═══════════════════════════════════════════════════════════════

function DeleteModal({ fir, onClose, onDeleted }) {
  const [deleting, setDeleting] = useState(false);
  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteFIR(fir.fir_id);
      onDeleted();
      onClose();
    } catch { setDeleting(false); }
  };
  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 400 }}>
        <div style={{ padding: "24px", textAlign: "center" }}>
          <span style={{ fontSize: 40 }}>⚠️</span>
          <h3 style={{ color: T.textPrimary, fontSize: 16, margin: "12px 0 4px" }}>Delete FIR</h3>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0 }}>Are you sure you want to delete <strong>{fir.fir_number}</strong>? This action cannot be undone.</p>
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
            <button onClick={onClose} style={{ padding: "8px 16px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: T.textSecondary, fontSize: 13, cursor: "pointer" }}>Cancel</button>
            <button onClick={handleDelete} disabled={deleting} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: T.danger, color: "#fff", fontSize: 13, fontWeight: 600, cursor: deleting ? "not-allowed" : "pointer", opacity: deleting ? 0.6 : 1 }}>{deleting ? "Deleting..." : "Delete"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// STATUS PILL
// ═══════════════════════════════════════════════════════════════

function StatusPill({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: "6px 14px", borderRadius: 20, fontSize: 12, cursor: "pointer",
      background: active ? T.accent : "transparent",
      color: active ? "#fff" : T.textSecondary,
      border: `1px solid ${active ? T.accent : T.cardBorder}`,
      fontWeight: active ? 600 : 400, transition: "all 0.15s", whiteSpace: "nowrap",
    }}>{children}</button>
  );
}

// ═══════════════════════════════════════════════════════════════
// KPI CARD
// ═══════════════════════════════════════════════════════════════

function KPICard({ icon, label, value, color = T.accent }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14,
      padding: "14px 18px", display: "flex", alignItems: "center", gap: 12, minWidth: 130,
      transition: "all 0.2s", cursor: "default",
    }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = `${color}33`; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.cardBorder; e.currentTarget.style.transform = "none"; }}
    >
      <div style={{ width: 38, height: 38, borderRadius: 10, background: `${color}18`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>{icon}</div>
      <div style={{ minWidth: 0 }}>
        <div style={{ color: T.textSecondary, fontSize: 10, fontWeight: 500, marginBottom: 1 }}>{label}</div>
        <div style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700 }}>{value}</div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════

export default function FIRManagement({ user }) {
  const [firs, setFirs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [toast, setToast] = useState(null); // { message, type }

  const fetchFIRs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page, page_size: 15 };
      if (filter !== "All") params.status = filter;
      if (search) params.search = search;
      const data = await listFIRs(params);
      setFirs(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load FIRs");
    } finally {
      setLoading(false);
    }
  }, [filter, search, page]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getFIRStatistics();
      setStats(data);
    } catch { /* stats are non-critical */ }
  }, []);

  useEffect(() => { fetchFIRs(); }, [fetchFIRs]);
  useEffect(() => { fetchStats(); }, [fetchStats]);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleCreated = () => { fetchFIRs(); fetchStats(); showToast("FIR registered successfully"); };
  const handleDeleted = () => { fetchFIRs(); fetchStats(); showToast("FIR deleted successfully"); };

  // Pagination pages
  const pages = [];
  for (let i = 1; i <= totalPages; i++) pages.push(i);

  return (
    <PageShell title="FIR Management" user={user}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* ── Create Modal ── */}
      {showCreateModal && (
        <CreateFIRModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleCreated}
        />
      )}

      {/* ── Delete Modal ── */}
      {deleteTarget && (
        <DeleteModal
          fir={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={handleDeleted}
        />
      )}

      {/* ── Page Header ── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>
          FIR Management
        </h1>
        <p style={{ color: T.textSecondary, fontSize: 13, margin: 0 }}>
          File, track, and manage First Information Reports · Karnataka Police
        </p>
      </div>

      {/* ── KPI Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
        {[
          { icon: "📋", label: "Total FIRs", value: stats?.total_firs ?? "—", color: T.accent },
          { icon: "⏳", label: "Pending", value: stats?.pending_count ?? "—", color: T.textMuted },
          { icon: "🔍", label: "Investigating", value: stats?.under_investigation_count ?? "—", color: T.warning },
          { icon: "✅", label: "Solved", value: stats?.solved_count ?? "—", color: T.success },
          { icon: "🔴", label: "High Priority", value: stats?.high_priority_count ?? "—", color: T.danger },
          { icon: "📊", label: "Total Cases", value: stats?.total_firs ?? "—", color: T.purple },
        ].map((k, i) => <KPICard key={i} {...k} />)}
      </div>

      {/* ── Toolbar ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 200, maxWidth: 320 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: T.textMuted, fontSize: 14, pointerEvents: "none" }}>🔍</span>
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search FIR number, title..."
            style={{
              width: "100%", padding: "8px 12px 8px 32px", borderRadius: 8,
              border: `1px solid ${T.inputBorder}`, background: T.inputBg,
              color: T.textPrimary, fontSize: 13, outline: "none",
              boxSizing: "border-box",
            }}
          />
        </div>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {STATUSES.map((s) => (
            <StatusPill key={s} active={filter === s} onClick={() => { setFilter(s); setPage(1); }}>{s}</StatusPill>
          ))}
        </div>
        <button
          onClick={() => { setShowCreateModal(true); }}
          style={{
            marginLeft: "auto", padding: "8px 18px", borderRadius: 8, border: "none",
            background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff",
            fontSize: 13, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap",
            transition: "opacity 0.15s",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.9"; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
        >+ New FIR</button>
      </div>

      {/* ── Table ── */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 30 }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ display: "flex", gap: 12, padding: "12px 20px", borderBottom: i < 5 ? `1px solid ${T.cardBorder}` : "none" }}>
                <div style={{ width: 80, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite" }} />
                <div style={{ flex: 1, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.1s" }} />
                <div style={{ width: 60, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.2s" }} />
              </div>
            ))}
          </div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <span style={{ fontSize: 32 }}>⚠️</span>
            <p style={{ color: T.danger, fontSize: 14, margin: "8px 0" }}>{error}</p>
            <button onClick={fetchFIRs} style={{ padding: "6px 16px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: T.accent, fontSize: 12, cursor: "pointer" }}>Retry</button>
          </div>
        ) : firs.length === 0 ? (
          <div style={{ padding: 60, textAlign: "center" }}>
            <span style={{ fontSize: 40, opacity: 0.4 }}>📭</span>
            <p style={{ color: T.textMuted, fontSize: 14, margin: "12px 0 4px" }}>No FIRs found{filter !== "All" ? ` with status "${filter}"` : search ? ` matching "${search}"` : ""}</p>
            <p style={{ color: T.textMuted, fontSize: 12, margin: 0 }}>Click + New FIR to create one</p>
          </div>
        ) : (
          <>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                    {["FIR #", "Title", "Crime Type", "District", "Priority", "Status", "Date", ""].map((h) => (
                      <th key={h} style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textAlign: "left", padding: "14px 16px", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {firs.map((f, i) => (
                    <tr key={f.fir_id} style={{
                      borderBottom: i < firs.length - 1 ? `1px solid ${T.cardBorder}` : "none",
                      transition: "background 0.1s",
                    }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = `${T.accent}06`; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                    >
                      <td style={{ padding: "12px 16px", color: T.accent, fontSize: 13, fontWeight: 600, whiteSpace: "nowrap" }}>{f.fir_number}</td>
                      <td style={{ padding: "12px 16px", color: T.textPrimary, fontSize: 13, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.title || "—"}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{f.crime_type_id || "—"}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{f.location_id || "—"}</td>
                      <td style={{ padding: "12px 16px" }}><Badge label={f.priority || "Medium"} /></td>
                      <td style={{ padding: "12px 16px" }}><Badge label={f.investigation_status || "Pending"} /></td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>
                        {f.incident_date || (f.created_at && f.created_at.split("T")[0]) || "—"}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            onClick={() => showToast(`FIR ${f.fir_number} - expand View in next update`, "info")}
                            style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.accent}15`, color: T.accent, fontSize: 11, cursor: "pointer" }}
                          >View</button>
                          <button
                            onClick={() => setDeleteTarget(f)}
                            style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.danger}15`, color: T.danger, fontSize: 11, cursor: "pointer" }}
                          >Del</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* ── Pagination ── */}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderTop: `1px solid ${T.cardBorder}` }}>
                <span style={{ color: T.textMuted, fontSize: 12 }}>{total} FIRs total</span>
                <div style={{ display: "flex", gap: 4 }}>
                  <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: page <= 1 ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page <= 1 ? "default" : "pointer" }}>Prev</button>
                  {pages.map((p) => (
                    <button key={p} onClick={() => setPage(p)} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: p === page ? T.accent : "transparent", color: p === page ? "#fff" : T.textSecondary, fontSize: 12, cursor: "pointer", fontWeight: p === page ? 600 : 400, minWidth: 28 }}>{p}</button>
                  ))}
                  <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: page >= totalPages ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page >= totalPages ? "default" : "pointer" }}>Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  );
}
