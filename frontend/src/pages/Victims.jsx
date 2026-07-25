import { useState, useEffect } from "react";
import { T } from "../styles/theme";
import { listVictims, getVictim, createVictim, updateVictim, deleteVictim } from "../services/victimsService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Input from "../components/Input";
import {
  validateName, NAME_RULES,
  validateAge, AGE_RULES,
  validatePhone, PHONE_RULES,
  validateEmail, EMAIL_RULES,
  validateAddress, ADDRESS_RULES,
  validateDropdown,
  validateForm,
} from "../utils/validation";

export default function Victims({ user }) {
  const [victims, setVictims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ full_name: "", age: "", gender: "Male", phone: "", email: "", address: "", fir_ids: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const canDelete = user?.role_id <= 2;
  const canEdit = user?.role_id <= 3;

  const fetchVictims = async () => {
    setLoading(true); setError("");
    try {
      const data = await listVictims({ page_size: 100 });
      setVictims(data.items || []);
    } catch (err) { setError(err.response?.data?.detail || "Failed to load victims"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchVictims(); }, []);

  const openCreate = () => {
    setEditId(null);
    setForm({ full_name: "", age: "", gender: "Male", phone: "", email: "", address: "", fir_ids: "" });
    setFieldErrors({}); setFormError(""); setShowForm(true);
  };

  const openEdit = async (id) => {
    try {
      const data = await getVictim(id);
      setEditId(id);
      setForm({ full_name: data.full_name || "", age: data.age?.toString() || "", gender: data.gender || "Male", phone: data.phone || "", email: data.email || "", address: data.address || "", fir_ids: "" });
      setFieldErrors({}); setFormError(""); setShowForm(true);
    } catch { setFormError("Failed to load victim details"); }
  };

  const handleSave = async () => {
    const rules = {
      full_name: [validateName, true],
      age: [validateAge, false],
      phone: [validatePhone, false],
      email: [validateEmail, false],
      address: [validateAddress, false],
    };
    const errs = validateForm(form, rules);
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setFormError("Please correct the highlighted fields before submitting."); return; }
    setSaveLoading(true); setFormError("");
    try {
      const payload = { full_name: form.full_name, gender: form.gender };
      if (form.age) payload.age = parseInt(form.age);
      if (form.phone) payload.phone = form.phone;
      if (form.email) payload.email = form.email;
      if (form.address) payload.address = form.address;
      if (editId) await updateVictim(editId, payload);
      else await createVictim(null, payload);
      setShowForm(false); fetchVictims();
    } catch (err) { setFormError(err.response?.data?.detail || "Failed to save victim"); }
    finally { setSaveLoading(false); }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete victim "${name}"?`)) return;
    try { await deleteVictim(id); fetchVictims(); }
    catch (err) { alert(err.response?.data?.detail || "Failed to delete victim"); }
  };

  return (
    <PageShell title="Victims" user={user}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <p style={{ color: T.textSecondary, fontSize: 14, margin: 0 }}>{victims.length} registered victims</p>
        <Button onClick={openCreate}>+ New Victim</Button>
      </div>
      {showForm && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: "0 0 16px", fontSize: 15 }}>{editId ? "Edit Victim" : "New Victim"}</h3>
          {formError && <div style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>⚠ {formError}</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Input label="Full Name" required error={fieldErrors.full_name} placeholder={NAME_RULES.placeholder} value={form.full_name} onChange={(e) => { setForm({ ...form, full_name: e.target.value }); setFieldErrors((p) => ({ ...p, full_name: "" })); }} />
            <Input label="Age" type="number" error={fieldErrors.age} placeholder={AGE_RULES.placeholder} value={form.age} onChange={(e) => { setForm({ ...form, age: e.target.value }); setFieldErrors((p) => ({ ...p, age: "" })); }} />
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Gender</label>
              <select value={form.gender} onChange={(e) => { setForm({ ...form, gender: e.target.value }); setFieldErrors((p) => ({ ...p, gender: "" })); }}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                {["Male","Female","Other"].map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <Input label="Phone" error={fieldErrors.phone} helper={PHONE_RULES.helper} placeholder={PHONE_RULES.placeholder} value={form.phone} onChange={(e) => { setForm({ ...form, phone: e.target.value }); setFieldErrors((p) => ({ ...p, phone: "" })); }} />
            <Input label="Email" type="email" error={fieldErrors.email} helper={EMAIL_RULES.helper} placeholder={EMAIL_RULES.placeholder} value={form.email} onChange={(e) => { setForm({ ...form, email: e.target.value }); setFieldErrors((p) => ({ ...p, email: "" })); }} />
            <Input label="Address" error={fieldErrors.address} placeholder={ADDRESS_RULES.placeholder} value={form.address} onChange={(e) => { setForm({ ...form, address: e.target.value }); setFieldErrors((p) => ({ ...p, address: "" })); }} />
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <Button onClick={handleSave} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading victims...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : victims.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>No victims found</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                {["Name", "Age", "Gender", "Phone", "Email", "Actions"].map((h) => (
                  <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {victims.map((v, i) => (
                <tr key={v.victim_id} style={{ borderBottom: i < victims.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                  <td style={{ padding: "14px 20px", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{v.full_name}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{v.age ?? "—"}</td>
                  <td style={{ padding: "14px 20px" }}><Badge label={v.gender || "—"} /></td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{v.phone || "—"}</td>
                  <td style={{ padding: "14px 20px", color: T.textSecondary, fontSize: 12 }}>{v.email || "—"}</td>
                  <td style={{ padding: "14px 20px" }}>
                    <div style={{ display: "flex", gap: 6 }}>
                      {canEdit && <button onClick={() => openEdit(v.victim_id)} style={{ background: T.accentGlow, color: T.accent, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Edit</button>}
                      {canDelete && <button onClick={() => handleDelete(v.victim_id, v.full_name)} style={{ background: "rgba(239,68,68,0.15)", color: T.danger, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Delete</button>}
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
