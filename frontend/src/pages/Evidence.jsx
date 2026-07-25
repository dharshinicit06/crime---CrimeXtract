import { useState, useEffect } from "react";
import { T } from "../styles/theme";
import { listEvidence, getEvidence, createEvidence, updateEvidence, deleteEvidence } from "../services/evidenceService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Input from "../components/Input";
import { listFIRs } from "../services/firService";
import {
  validateRequired, validateDate, validateRemarks,
  validateForm,
} from "../utils/validation";

export default function Evidence({ user }) {
  const [evidence, setEvidence] = useState([]);
  const [firOptions, setFirOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ evidence_name: "", evidence_type: "Physical", description: "", collected_date: "", fir_id: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const canDelete = user?.role_id <= 2;
  const canEdit = user?.role_id <= 3;

  const fetchAll = async () => {
    setLoading(true); setError("");
    try {
      const [ev, firData] = await Promise.all([
        listEvidence({ page_size: 100 }).catch(() => ({ items: [] })),
        listFIRs({ page_size: 200 }).catch(() => ({ items: [] })),
      ]);
      setEvidence(ev.items || []);
      setFirOptions(firData.items || []);
    } catch { setError("Failed to load data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const openCreate = async () => {
    setEditId(null);
    setForm({ evidence_name: "", evidence_type: "Physical", description: "", collected_date: "", fir_id: "" });
    setFieldErrors({}); setFormError(""); setShowForm(true);
    // Refresh FIR list so newly registered FIRs appear in the Linked FIR dropdown
    try { const firData = await listFIRs({ page_size: 200 }); setFirOptions(firData.items || []); } catch {}
  };

  const openEdit = async (id) => {
    try {
      const [data, firData] = await Promise.all([
        getEvidence(id),
        listFIRs({ page_size: 200 }).catch(() => ({ items: [] })),
      ]);
      setEditId(id);
      setForm({ evidence_name: data.evidence_name || "", evidence_type: data.evidence_type || "Physical", description: data.description || "", collected_date: data.collected_date || "", fir_id: data.fir_id?.toString() || "" });
      setFirOptions(firData.items || []);
      setFieldErrors({}); setFormError(""); setShowForm(true);
    } catch { setFormError("Failed to load evidence details"); }
  };

  const handleSave = async () => {
    const rules = {
      evidence_name: [(v) => validateRequired(v, "Evidence name"), true],
      description: [validateRemarks, false],
      collected_date: [(v) => validateDate(v, false, false), false],
    };
    const errs = validateForm(form, rules);
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setFormError("Please correct the highlighted fields before submitting."); return; }
    setSaveLoading(true); setFormError("");
    try {
      const payload = { evidence_name: form.evidence_name, evidence_type: form.evidence_type, description: form.description || null, collected_date: form.collected_date || null };
      const firIdVal = form.fir_id ? parseInt(form.fir_id) : null;
      if (editId) await updateEvidence(editId, payload);
      else await createEvidence(firIdVal, payload);
      setShowForm(false); fetchAll();
    } catch (err) { setFormError(err.response?.data?.detail || "Failed to save evidence"); }
    finally { setSaveLoading(false); }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete evidence "${name}"?`)) return;
    try { await deleteEvidence(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || "Failed to delete evidence"); }
  };

  return (
    <PageShell title="Evidence" user={user}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <p style={{ color: T.textSecondary, fontSize: 14, margin: 0 }}>{evidence.length} evidence records</p>
        <Button onClick={openCreate}>+ New Evidence</Button>
      </div>
      {showForm && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: "0 0 16px", fontSize: 15 }}>{editId ? "Edit Evidence" : "New Evidence"}</h3>
          {formError && <div style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>⚠ {formError}</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Input label="Evidence Name" required error={fieldErrors.evidence_name} value={form.evidence_name} onChange={(e) => { setForm({ ...form, evidence_name: e.target.value }); setFieldErrors((p) => ({ ...p, evidence_name: "" })); }} />
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Type</label>
              <select value={form.evidence_type} onChange={(e) => setForm({ ...form, evidence_type: e.target.value })}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                {["Physical","Digital","Document","Forensic","Weapon","Other"].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Linked FIR</label>
              <select value={form.fir_id} onChange={(e) => { setForm({ ...form, fir_id: e.target.value }); setFieldErrors((p) => ({ ...p, fir_id: "" })); }}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                <option value="">— None —</option>
                {firOptions.map((f) => <option key={f.fir_id} value={f.fir_id}>{f.fir_number} — {f.title?.slice(0, 30)}</option>)}
              </select>
            </div>
            <Input label="Collected Date" type="date" error={fieldErrors.collected_date} value={form.collected_date} onChange={(e) => { setForm({ ...form, collected_date: e.target.value }); setFieldErrors((p) => ({ ...p, collected_date: "" })); }} />
            <div style={{ gridColumn: "1 / -1" }}>
              <Input label="Description" error={fieldErrors.description} value={form.description} onChange={(e) => { setForm({ ...form, description: e.target.value }); setFieldErrors((p) => ({ ...p, description: "" })); }} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <Button onClick={handleSave} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading evidence...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : evidence.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>No evidence found</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                {["Name", "Type", "FIR", "Date", "Actions"].map((h) => (
                  <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {evidence.map((e, i) => (
                <tr key={e.evidence_id} style={{ borderBottom: i < evidence.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                  <td style={{ padding: "14px 20px", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{e.evidence_name}</td>
                  <td style={{ padding: "14px 20px" }}><Badge label={e.evidence_type} /></td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>#{e.fir_id || "—"}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{e.collected_date || "—"}</td>
                  <td style={{ padding: "14px 20px" }}>
                    <div style={{ display: "flex", gap: 6 }}>
                      {canEdit && <button onClick={() => openEdit(e.evidence_id)} style={{ background: T.accentGlow, color: T.accent, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Edit</button>}
                      {canDelete && <button onClick={() => handleDelete(e.evidence_id, e.evidence_name)} style={{ background: "rgba(239,68,68,0.15)", color: T.danger, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Delete</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </PageShell>
  );
}
