import { useState, useEffect } from "react";
import { T } from "../styles/theme";
import { listAccused, getAccused, createAccused, updateAccused, deleteAccused } from "../services/accusedService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Input from "../components/Input";
import {
  validateName, NAME_RULES,
  validatePhone, PHONE_RULES,
  validateEmail, EMAIL_RULES,
  validateAddress, ADDRESS_RULES,
  validateForm,
} from "../utils/validation";

export default function Accused({ user }) {
  const [accused, setAccused] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", address: "", fir_ids: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const canDelete = user?.role_id <= 2;
  const canEdit = user?.role_id <= 3;

  const fetchAccused = async () => {
    setLoading(true); setError("");
    try {
      const data = await listAccused({ page_size: 100 });
      setAccused(data.items || []);
    } catch (err) { setError(err.response?.data?.detail || "Failed to load accused"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAccused(); }, []);

  const openCreate = () => {
    setEditId(null);
    setForm({ full_name: "", phone: "", email: "", address: "", fir_ids: "" });
    setFieldErrors({}); setFormError(""); setShowForm(true);
  };

  const openEdit = async (id) => {
    try {
      const data = await getAccused(id);
      setEditId(id);
      setForm({ full_name: data.full_name || "", phone: data.phone || "", email: data.email || "", address: data.address || "", fir_ids: "" });
      setFieldErrors({}); setFormError(""); setShowForm(true);
    } catch { setFormError("Failed to load accused details"); }
  };

  const handleSave = async () => {
    const rules = {
      full_name: [validateName, true],
      phone: [validatePhone, false],
      email: [validateEmail, false],
      address: [validateAddress, false],
    };
    const errs = validateForm(form, rules);
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setFormError("Please correct the highlighted fields before submitting."); return; }
    setSaveLoading(true); setFormError("");
    try {
      const payload = { full_name: form.full_name };
      if (form.phone) payload.phone = form.phone;
      if (form.email) payload.email = form.email;
      if (form.address) payload.address = form.address;
      if (form.fir_ids) payload.fir_ids = form.fir_ids.split(",").map((s) => parseInt(s.trim())).filter(Boolean);
      if (editId) await updateAccused(editId, payload);
      else await createAccused(payload);
      setShowForm(false); fetchAccused();
    } catch (err) { setFormError(err.response?.data?.detail || "Failed to save accused"); }
    finally { setSaveLoading(false); }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete accused "${name}"?`)) return;
    try { await deleteAccused(id); fetchAccused(); }
    catch (err) { alert(err.response?.data?.detail || "Failed to delete accused"); }
  };

  return (
    <PageShell title="Accused" user={user}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <p style={{ color: T.textSecondary, fontSize: 14, margin: 0 }}>{accused.length} accused persons</p>
        <Button onClick={openCreate}>+ New Accused</Button>
      </div>
      {showForm && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: "0 0 16px", fontSize: 15 }}>{editId ? "Edit Accused" : "New Accused"}</h3>
          {formError && <div style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>⚠ {formError}</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Input label="Full Name" required error={fieldErrors.full_name} placeholder={NAME_RULES.placeholder} value={form.full_name} onChange={(e) => { setForm({ ...form, full_name: e.target.value }); setFieldErrors((p) => ({ ...p, full_name: "" })); }} />
            <Input label="Phone" error={fieldErrors.phone} helper={PHONE_RULES.helper} placeholder={PHONE_RULES.placeholder} value={form.phone} onChange={(e) => { setForm({ ...form, phone: e.target.value }); setFieldErrors((p) => ({ ...p, phone: "" })); }} />
            <Input label="Email" type="email" error={fieldErrors.email} helper={EMAIL_RULES.helper} placeholder={EMAIL_RULES.placeholder} value={form.email} onChange={(e) => { setForm({ ...form, email: e.target.value }); setFieldErrors((p) => ({ ...p, email: "" })); }} />
            <Input label="Address" error={fieldErrors.address} placeholder={ADDRESS_RULES.placeholder} value={form.address} onChange={(e) => { setForm({ ...form, address: e.target.value }); setFieldErrors((p) => ({ ...p, address: "" })); }} />
            <Input label="FIR IDs (comma-separated)" value={form.fir_ids} onChange={(e) => { setForm({ ...form, fir_ids: e.target.value }); setFieldErrors((p) => ({ ...p, fir_ids: "" })); }} placeholder="e.g. 1, 3, 5" />
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <Button onClick={handleSave} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading accused...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : accused.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>No accused persons found</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                {["Name", "Phone", "Email", "Address", "Actions"].map((h) => (
                  <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {accused.map((a, i) => (
                <tr key={a.accused_id} style={{ borderBottom: i < accused.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                  <td style={{ padding: "14px 20px", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{a.full_name}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{a.phone || "—"}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{a.email || "—"}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{a.address || "—"}</td>
                  <td style={{ padding: "14px 20px" }}>
                    <div style={{ display: "flex", gap: 6 }}>
                      {canEdit && <button onClick={() => openEdit(a.accused_id)} style={{ background: T.accentGlow, color: T.accent, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Edit</button>}
                      {canDelete && <button onClick={() => handleDelete(a.accused_id, a.full_name)} style={{ background: "rgba(239,68,68,0.15)", color: T.danger, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Delete</button>}
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
