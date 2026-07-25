import { useState, useEffect } from "react";
import { T } from "../styles/theme";
import { listCrimeHistory, getCrimeHistory, createCrimeHistory, updateCrimeHistory, deleteCrimeHistory } from "../services/crimeHistoryService";
import { listFIRs } from "../services/firService";
import { listAccused } from "../services/accusedService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Input from "../components/Input";
import { validateRequired, validateRemarks, validateForm } from "../utils/validation";

const STATUSES = ["Convicted", "Acquitted", "Pending", "Dropped", "Under Investigation"];

export default function CrimeHistory({ user }) {
  const [history, setHistory] = useState([]);
  const [firOptions, setFirOptions] = useState([]);
  const [accusedOptions, setAccusedOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ fir_id: "", accused_id: "", crime_type: "", arrest_date: "", conviction_status: "Pending", sentence_years: "", notes: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const canDelete = user?.role_id <= 2;
  const canEdit = user?.role_id <= 3;

  const fetchAll = async () => {
    setLoading(true); setError("");
    try {
      const [h, f, a] = await Promise.all([
        listCrimeHistory({ page_size: 100 }).catch(() => ({ items: [] })),
        listFIRs({ page_size: 200 }).catch(() => ({ items: [] })),
        listAccused({ page_size: 200 }).catch(() => ({ items: [] })),
      ]);
      setHistory(h.items || []);
      setFirOptions(f.items || []);
      setAccusedOptions(a.items || []);
    } catch { setError("Failed to load data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const openCreate = () => {
    setEditId(null);
    setForm({ fir_id: "", accused_id: "", crime_type: "", arrest_date: "", conviction_status: "Pending", sentence_years: "", notes: "" });
    setFieldErrors({}); setFormError(""); setShowForm(true);
  };

  const openEdit = async (id) => {
    try {
      const data = await getCrimeHistory(id);
      const rowId = data.id ?? data.crime_history_id ?? data.history_id;
      setEditId(id);
      setForm({ fir_id: data.fir_id?.toString() || "", accused_id: data.accused_id?.toString() || "", crime_type: data.crime_type || "", arrest_date: data.arrest_date || "", conviction_status: data.conviction_status || "Pending", sentence_years: data.sentence_years?.toString() || "", notes: data.notes || "" });
      setFieldErrors({}); setFormError(""); setShowForm(true);
    } catch { setFormError("Failed to load crime history details"); }
  };

  const handleSave = async () => {
    const rules = {
      fir_id: [(v) => validateRequired(v, "FIR"), true],
      crime_type: [(v) => validateRequired(v, "Crime type"), false],
      notes: [validateRemarks, false],
    };
    const errs = validateForm(form, rules);
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setFormError("Please correct the highlighted fields before submitting."); return; }
    setSaveLoading(true); setFormError("");
    try {
      const payload = { fir_id: parseInt(form.fir_id), accused_id: form.accused_id ? parseInt(form.accused_id) : null, crime_type: form.crime_type || null, arrest_date: form.arrest_date || null, conviction_status: form.conviction_status, sentence_years: form.sentence_years ? parseInt(form.sentence_years) : null, notes: form.notes || null };
      if (editId) await updateCrimeHistory(editId, payload);
      else await createCrimeHistory(payload);
      setShowForm(false); fetchAll();
    } catch (err) { setFormError(err.response?.data?.detail || "Failed to save crime history"); }
    finally { setSaveLoading(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this crime history record?")) return;
    try { await deleteCrimeHistory(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || "Failed to delete"); }
  };

  return (
    <PageShell title="Crime History" user={user}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <p style={{ color: T.textSecondary, fontSize: 14, margin: 0 }}>{history.length} crime history records</p>
        <Button onClick={openCreate}>+ New Record</Button>
      </div>
      {showForm && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: "0 0 16px", fontSize: 15 }}>{editId ? "Edit Record" : "New Crime History Record"}</h3>
          {formError && <div style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>⚠ {formError}</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>FIR *</label>
              <select value={form.fir_id} onChange={(e) => setForm({ ...form, fir_id: e.target.value })}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                <option value="">— Select FIR —</option>
                {firOptions.map((f) => <option key={f.fir_id} value={f.fir_id}>#{f.fir_number} {f.title?.slice(0, 25)}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Accused</label>
              <select value={form.accused_id} onChange={(e) => setForm({ ...form, accused_id: e.target.value })}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                <option value="">— None —</option>
                {accusedOptions.map((a) => <option key={a.accused_id} value={a.accused_id}>{a.full_name}</option>)}
              </select>
            </div>
            <Input label="Crime Type" error={fieldErrors.crime_type} value={form.crime_type} onChange={(e) => { setForm({ ...form, crime_type: e.target.value }); setFieldErrors((p) => ({ ...p, crime_type: "" })); }} />
            <Input label="Arrest Date" type="date" error={fieldErrors.arrest_date} value={form.arrest_date} onChange={(e) => { setForm({ ...form, arrest_date: e.target.value }); setFieldErrors((p) => ({ ...p, arrest_date: "" })); }} />
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Status</label>
              <select value={form.conviction_status} onChange={(e) => setForm({ ...form, conviction_status: e.target.value })}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <Input label="Sentence (years)" type="number" error={fieldErrors.sentence_years} value={form.sentence_years} onChange={(e) => { setForm({ ...form, sentence_years: e.target.value }); setFieldErrors((p) => ({ ...p, sentence_years: "" })); }} />
          </div>
          <div style={{ marginTop: 16 }}><Input label="Notes" error={fieldErrors.notes} value={form.notes} onChange={(e) => { setForm({ ...form, notes: e.target.value }); setFieldErrors((p) => ({ ...p, notes: "" })); }} /></div>
          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <Button onClick={handleSave} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading crime history...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : history.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>No records found</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                {["FIR #", "Accused", "Crime Type", "Arrest Date", "Status", "Sentence", "Actions"].map((h) => (
                  <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((r, i) => {
                const accused = accusedOptions.find((a) => a.accused_id === r.accused_id);
                const fir = firOptions.find((f) => f.fir_id === r.fir_id);
                const rowId = r.id ?? r.crime_history_id ?? r.history_id ?? i;
                return (
                  <tr key={rowId} style={{ borderBottom: i < history.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                    <td style={{ padding: "14px 20px", color: T.accent, fontSize: 13, fontWeight: 600 }}>{fir?.fir_number || `#${r.fir_id}`}</td>
                    <td style={{ padding: "14px 20px", color: T.textPrimary, fontSize: 13 }}>{accused?.full_name || accusedOptions.find(a => a.accused_id === r.accused_id)?.full_name || `Accused #${r.accused_id}`}</td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{r.crime_type || "—"}</td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{r.arrest_date || "—"}</td>
                    <td style={{ padding: "14px 20px" }}><Badge label={r.conviction_status || "Pending"} /></td>
                    <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{r.sentence_years ? `${r.sentence_years}y` : "—"}</td>
                    <td style={{ padding: "14px 20px" }}>
                      <div style={{ display: "flex", gap: 6 }}>
                        {canEdit && <button onClick={() => openEdit(rowId)} style={{ background: T.accentGlow, color: T.accent, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Edit</button>}
                        {canDelete && <button onClick={() => handleDelete(rowId)} style={{ background: "rgba(239,68,68,0.15)", color: T.danger, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Delete</button>}
                      </div>
                    </td>
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
