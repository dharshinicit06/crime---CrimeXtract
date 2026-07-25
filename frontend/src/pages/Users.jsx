import { useState, useEffect, useCallback } from "react";
import { T } from "../styles/theme";
import {
  listUsers, createUser, updateUser,
} from "../services/usersService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import { validateName, NAME_RULES, validateEmail, EMAIL_RULES, validatePhone, PHONE_RULES, validatePassword, PASSWORD_RULES } from "../utils/validation";

// ═══════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════

const ANIM_STYLES = `
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
`;

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

const ROLE_NAMES = { 1: "Admin", 2: "Investigator", 3: "Analyst" };
const ROLE_OPTIONS = [
  { id: 1, label: "Admin" },
  { id: 2, label: "Investigator" },
  { id: 3, label: "Analyst" },
];

const ROLE_COLORS = {
  1: T.danger,
  2: T.accent,
  3: T.purple,
};

const STYLE = {
  modalOverlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000, padding: 20,
  },
  modalContent: {
    background: T.card, border: `1px solid ${T.cardBorder}`,
    borderRadius: 16, width: "100%", maxWidth: 480,
    maxHeight: "90vh", overflow: "auto", animation: "slideUp 0.25s ease",
  },
  input: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none",
    boxSizing: "border-box",
  },
  select: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none", cursor: "pointer",
    boxSizing: "border-box",
  },
  label: { display: "block", color: T.textSecondary, fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" },
  btnPrimary: {
    padding: "10px 20px", borderRadius: 8, border: "none",
    background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff",
    fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
  btnSecondary: {
    padding: "10px 20px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
    background: T.inputBg, color: T.textSecondary, fontSize: 13, cursor: "pointer",
  },
  btnDanger: {
    padding: "10px 20px", borderRadius: 8, border: "none",
    background: T.danger, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
};

// ═══════════════════════════════════════════════════════════════
// KPI CARD
// ═══════════════════════════════════════════════════════════════

function KPICard({ icon, label, value, color = T.accent }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14,
      padding: "14px 18px", display: "flex", alignItems: "center", gap: 12, minWidth: 120,
      transition: "all 0.2s",
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
// TOAST
// ═══════════════════════════════════════════════════════════════

const SHOW_TOAST = {};

// ═══════════════════════════════════════════════════════════════
// USER FORM MODAL (Create / Edit)
// ═══════════════════════════════════════════════════════════════

function UserFormModal({ user, onClose, onSaved }) {
  const isEdit = !!user;
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
    password: "",
    phone: user?.phone || "",
    role_id: user?.role_id || 3,
    is_active: user?.is_active !== false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    const nameErr = validateName(form.full_name, true);
    if (nameErr) errs.full_name = nameErr;
    const emailErr = validateEmail(form.email, true);
    if (emailErr) errs.email = emailErr;
    const phoneErr = validatePhone(form.phone, false);
    if (phoneErr) errs.phone = phoneErr;
    if (!isEdit && !form.password) {
      errs.password = "Password is required for new users";
    } else if (form.password) {
      const pwdErr = validatePassword(form.password, true);
      if (pwdErr) errs.password = pwdErr;
    }
    if (Object.keys(errs).length > 0) { setError(Object.values(errs)[0]); return; }
    setSaving(true);
    setError("");
    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone || null,
        role_id: form.role_id,
        is_active: form.is_active,
      };
      if (form.password) payload.password = form.password;
      if (isEdit) await updateUser(user.user_id, payload);
      else await createUser(payload);
      onSaved();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save user");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={STYLE.modalContent}>
        <div style={{ padding: "20px 24px", borderBottom: `1px solid ${T.cardBorder}` }}>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: 0 }}>{isEdit ? "Edit User" : "Create User"}</h2>
          <p style={{ color: T.textMuted, fontSize: 12, margin: "4px 0 0" }}>{isEdit ? "Update user profile details" : "Add a new user to the system"}</p>
        </div>
        <form onSubmit={handleSubmit} style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          {error && (
            <div style={{ padding: "10px 14px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, color: T.danger, fontSize: 13 }}>{error}</div>
          )}
          <div>
            <label style={STYLE.label}>Full Name *</label>
            <input style={STYLE.input} value={form.full_name} onChange={(e) => handleChange("full_name", e.target.value)} placeholder={NAME_RULES.placeholder} />
          </div>
          <div>
            <label style={STYLE.label}>Email *</label>
            <input style={STYLE.input} type="email" value={form.email} onChange={(e) => handleChange("email", e.target.value)} placeholder={EMAIL_RULES.placeholder} />
          </div>
          <div>
            <label style={STYLE.label}>{isEdit ? "New Password (leave blank to keep current)" : "Password *"}</label>
            <input style={STYLE.input} type="password" value={form.password} onChange={(e) => handleChange("password", e.target.value)} placeholder={isEdit ? "Leave blank to keep current" : PASSWORD_RULES.placeholder} />
          </div>
          <div>
            <label style={STYLE.label}>Phone</label>
            <input style={STYLE.input} value={form.phone} onChange={(e) => handleChange("phone", e.target.value)} placeholder={PHONE_RULES.placeholder} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={STYLE.label}>Role</label>
              <select style={STYLE.select} value={form.role_id} onChange={(e) => handleChange("role_id", parseInt(e.target.value))}>
                {ROLE_OPTIONS.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label style={STYLE.label}>Status</label>
              <select style={STYLE.select} value={form.is_active ? "active" : "inactive"} onChange={(e) => handleChange("is_active", e.target.value === "active")}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <button type="button" onClick={onClose} style={STYLE.btnSecondary}>Cancel</button>
            <button type="submit" disabled={saving} style={{ ...STYLE.btnPrimary, opacity: saving ? 0.6 : 1, cursor: saving ? "not-allowed" : "pointer" }}>
              {saving ? "Saving..." : isEdit ? "Update User" : "Create User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// PASSWORD RESET MODAL
// ═══════════════════════════════════════════════════════════════

function PasswordResetModal({ user, onClose, onReset }) {
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const generatePassword = () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$";
    let pwd = "";
    for (let i = 0; i < 12; i++) pwd += chars[Math.floor(Math.random() * chars.length)];
    setPassword(pwd);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const pwdErr = validatePassword(password, true);
    if (pwdErr) { setError(pwdErr); return; }
    setSaving(true);
    setError("");
    try {
      await updateUser(user.user_id, { password });
      onReset();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to reset password");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 420 }}>
        <div style={{ padding: "20px 24px", borderBottom: `1px solid ${T.cardBorder}` }}>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: 0 }}>Reset Password</h2>
          <p style={{ color: T.textMuted, fontSize: 12, margin: "4px 0 0" }}>Reset password for <strong>{user?.full_name}</strong></p>
        </div>
        <form onSubmit={handleSubmit} style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          {error && (
            <div style={{ padding: "10px 14px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, color: T.danger, fontSize: 13 }}>{error}</div>
          )}
          <div>
            <label style={STYLE.label}>New Password</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input style={{ ...STYLE.input, flex: 1 }} type="text" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter or generate password" />
              <button type="button" onClick={generatePassword} style={{ padding: "10px 14px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: T.accent, fontSize: 12, cursor: "pointer", whiteSpace: "nowrap" }}>Generate</button>
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <button type="button" onClick={onClose} style={STYLE.btnSecondary}>Cancel</button>
            <button type="submit" disabled={saving} style={{ ...STYLE.btnPrimary, opacity: saving ? 0.6 : 1, cursor: saving ? "not-allowed" : "pointer" }}>
              {saving ? "Resetting..." : "Reset Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// CONFIRM MODAL
// ═══════════════════════════════════════════════════════════════

function ConfirmModal({ title, message, confirmText = "Confirm", confirmColor = T.danger, onConfirm, onClose }) {
  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 400 }}>
        <div style={{ padding: "24px", textAlign: "center" }}>
          <span style={{ fontSize: 40 }}>⚠️</span>
          <h3 style={{ color: T.textPrimary, fontSize: 16, margin: "12px 0 4px" }}>{title}</h3>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0, lineHeight: 1.5 }}>{message}</p>
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
            <button onClick={onClose} style={STYLE.btnSecondary}>Cancel</button>
            <button onClick={onConfirm} style={{ ...STYLE.btnDanger, background: confirmColor }}>{confirmText}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// USER DETAIL DRAWER
// ═══════════════════════════════════════════════════════════════

function UserDrawer({ user, onClose, onEdit, onResetPwd, onToggleStatus }) {
  if (!user) return null;
  const isActive = user.is_active !== false;
  const roleName = ROLE_NAMES[user.role_id] || "Officer";

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 420 }}>
        <div style={{ padding: "24px", textAlign: "center", borderBottom: `1px solid ${T.cardBorder}` }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: `${ROLE_COLORS[user.role_id] || T.accent}18`, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 24, fontWeight: 700, color: ROLE_COLORS[user.role_id] || T.accent, marginBottom: 12 }}>
            {user.full_name?.[0]?.toUpperCase()}
          </div>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: "0 0 4px" }}>{user.full_name}</h2>
          <Badge label={roleName} />
          <Badge label={isActive ? "Active" : "Inactive"} />
        </div>
        <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { label: "Email", value: user.email },
            { label: "Phone", value: user.phone || "—" },
            { label: "Role ID", value: `${user.role_id} (${roleName})` },
            { label: "Status", value: isActive ? "Active" : "Inactive" },
            { label: "Created", value: user.created_at ? new Date(user.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" }) : "—" },
            { label: "Updated", value: user.updated_at ? new Date(user.updated_at).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" }) : "—" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < 5 ? `1px solid ${T.cardBorder}` : "none" }}>
              <span style={{ color: T.textMuted, fontSize: 12 }}>{item.label}</span>
              <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 500 }}>{item.value}</span>
            </div>
          ))}
        </div>
        <div style={{ padding: "16px 24px", borderTop: `1px solid ${T.cardBorder}`, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={() => { onEdit(user); onClose(); }} style={STYLE.btnPrimary}>Edit</button>
          <button onClick={() => { onResetPwd(user); onClose(); }} style={{ ...STYLE.btnSecondary, color: T.warning }}>Reset Password</button>
          <button onClick={() => { onToggleStatus(user); onClose(); }} style={{ ...STYLE.btnSecondary, color: isActive ? T.warning : T.success }}>
            {isActive ? "Deactivate" : "Activate"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════

export default function Users({ user }) {
  const isAdmin = user?.role_id === 1;
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Modals
  const [showFormModal, setShowFormModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null); // drawer
  const [resetPwdUser, setResetPwdUser] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null); // { title, message, onConfirm }
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Stats
  const stats = {
    total: users.length,
    active: users.filter((u) => u.is_active !== false).length,
    admins: users.filter((u) => u.role_id === 1).length,
    investigators: users.filter((u) => u.role_id === 2).length,
    analysts: users.filter((u) => u.role_id === 3).length,
    disabled: users.filter((u) => u.is_active === false).length,
  };

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page, page_size: 20 };
      if (search) params.search = search;
      if (roleFilter) params.role_id = parseInt(roleFilter);
      if (activeFilter !== "") params.is_active = activeFilter === "active";
      const data = await listUsers(params);
      setUsers(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, activeFilter, page]);

  useEffect(() => { if (isAdmin) fetchUsers(); }, [fetchUsers, isAdmin]);

  // ── Non-admin view: show own profile only ──
  if (!isAdmin) {
    return (
      <PageShell title="My Profile" user={user}>
        <style>{ANIM_STYLES}</style>
        <div style={{ maxWidth: 600, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <div style={{ width: 64, height: 64, borderRadius: 16, background: `${T.accent}18`, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 28, fontWeight: 700, color: T.accent, marginBottom: 12 }}>
              {user?.full_name?.[0]?.toUpperCase()}
            </div>
            <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>{user?.full_name}</h1>
            <Badge label={ROLE_NAMES[user?.role_id] || "Officer"} />
          </div>
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24 }}>
            {[
              { label: "Email", value: user?.email },
              { label: "Phone", value: user?.phone || "—" },
              { label: "Role", value: ROLE_NAMES[user?.role_id] || "Officer" },
              { label: "Status", value: user?.is_active !== false ? "Active" : "Inactive" },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: i < 3 ? `1px solid ${T.cardBorder}` : "none" }}>
                <span style={{ color: T.textMuted, fontSize: 13 }}>{item.label}</span>
                <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{item.value}</span>
              </div>
            ))}
          </div>
          <p style={{ color: T.textMuted, fontSize: 12, textAlign: "center", marginTop: 16 }}>
            Contact an administrator to update your profile details.
          </p>
        </div>
      </PageShell>
    );
  }

  // ── Admin view ──
  const pages = [];
  for (let i = 1; i <= totalPages; i++) pages.push(i);

  const handleToggleStatus = (targetUser) => {
    const isActive = targetUser.is_active !== false;
    setConfirmAction({
      title: isActive ? "Deactivate User" : "Activate User",
      message: `Are you sure you want to ${isActive ? "deactivate" : "activate"} "${targetUser.full_name}"?`,
      confirmText: isActive ? "Deactivate" : "Activate",
      confirmColor: isActive ? T.warning : T.success,
      onConfirm: async () => {
        try {
          await updateUser(targetUser.user_id, { is_active: !isActive });
          showToast(`User ${isActive ? "deactivated" : "activated"} successfully`);
          fetchUsers();
        } catch (err) {
          showToast(err?.response?.data?.detail || "Failed to update status", "error");
        }
        setConfirmAction(null);
      },
    });
  };

  const handleDeleteConfirm = (targetUser) => {
    setConfirmAction({
      title: "Deactivate User",
      message: `Are you sure you want to deactivate "${targetUser.full_name}"? They will not be able to log in.`,
      confirmText: "Deactivate",
      onConfirm: async () => {
        try {
          await updateUser(targetUser.user_id, { is_active: false });
          showToast("User deactivated successfully");
          fetchUsers();
        } catch (err) {
          showToast(err?.response?.data?.detail || "Failed to deactivate user", "error");
        }
        setConfirmAction(null);
      },
    });
  };

  return (
    <PageShell title="User Management" user={user}>
      <style>{ANIM_STYLES}</style>

      {/* ── Toasts ── */}
      {toast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 2000,
          padding: "12px 20px", borderRadius: 10,
          background: toast.type === "success" ? T.success : T.danger,
          color: "#fff", fontSize: 13, fontWeight: 600,
          boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          animation: "slideUp 0.25s ease",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <span>{toast.type === "success" ? "✅" : "⚠️"}</span>
          {toast.message}
        </div>
      )}

      {/* ── Modals ── */}
      {showFormModal && (
        <UserFormModal
          user={editUser}
          onClose={() => { setShowFormModal(false); setEditUser(null); }}
          onSaved={() => { showToast(editUser ? "User updated successfully" : "User created successfully"); fetchUsers(); }}
        />
      )}
      {resetPwdUser && (
        <PasswordResetModal
          user={resetPwdUser}
          onClose={() => setResetPwdUser(null)}
          onReset={() => showToast("Password reset successfully")}
        />
      )}
      {selectedUser && (
        <UserDrawer
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
          onEdit={(u) => { setEditUser(u); setShowFormModal(true); }}
          onResetPwd={(u) => setResetPwdUser(u)}
          onToggleStatus={handleToggleStatus}
        />
      )}
      {confirmAction && (
        <ConfirmModal
          title={confirmAction.title}
          message={confirmAction.message}
          confirmText={confirmAction.confirmText}
          confirmColor={confirmAction.confirmColor}
          onConfirm={confirmAction.onConfirm}
          onClose={() => setConfirmAction(null)}
        />
      )}

      {/* ── Header ── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>User Management</h1>
        <p style={{ color: T.textSecondary, fontSize: 13, margin: 0 }}>Manage officers, investigators, and analysts · Admin panel</p>
      </div>

      {/* ── KPI Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
        {[
          { icon: "👥", label: "Total Users", value: stats.total, color: T.accent },
          { icon: "✅", label: "Active", value: stats.active, color: T.success },
          { icon: "👑", label: "Admins", value: stats.admins, color: T.danger },
          { icon: "🔍", label: "Investigators", value: stats.investigators, color: T.accent },
          { icon: "📊", label: "Analysts", value: stats.analysts, color: T.purple },
          { icon: "⛔", label: "Disabled", value: stats.disabled, color: T.textMuted },
        ].map((k, i) => <KPICard key={i} {...k} />)}
      </div>

      {/* ── Toolbar ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 180, maxWidth: 280 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: T.textMuted, fontSize: 14, pointerEvents: "none" }}>🔍</span>
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search name or email..."
            style={{ width: "100%", padding: "8px 12px 8px 32px", borderRadius: 8, border: `1px solid ${T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box" }}
          />
        </div>
        <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }} style={STYLE.select}>
          <option value="">All Roles</option>
          {ROLE_OPTIONS.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
        </select>
        <select value={activeFilter} onChange={(e) => { setActiveFilter(e.target.value); setPage(1); }} style={STYLE.select}>
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button onClick={() => { setEditUser(null); setShowFormModal(true); }} style={{ ...STYLE.btnPrimary, marginLeft: "auto" }}>+ Add User</button>
      </div>

      {/* ── Table ── */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 30 }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ display: "flex", gap: 12, padding: "14px 20px", borderBottom: i < 5 ? `1px solid ${T.cardBorder}` : "none" }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: T.inputBg }} />
                <div style={{ flex: 2, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite" }} />
                <div style={{ flex: 2, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.1s" }} />
                <div style={{ flex: 1, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.2s" }} />
                <div style={{ width: 60, height: 14, borderRadius: 4, background: T.inputBg }} />
              </div>
            ))}
          </div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <span style={{ fontSize: 32 }}>⚠️</span>
            <p style={{ color: T.danger, fontSize: 14, margin: "8px 0" }}>{error}</p>
          </div>
        ) : users.length === 0 ? (
          <div style={{ padding: 60, textAlign: "center" }}>
            <span style={{ fontSize: 40, opacity: 0.4 }}>👥</span>
            <p style={{ color: T.textMuted, fontSize: 14, margin: "12px 0 4px" }}>No users found</p>
            <p style={{ color: T.textMuted, fontSize: 12, margin: 0 }}>Try adjusting your search or filters</p>
          </div>
        ) : (
          <>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 650 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                    {["Name", "Email", "Role", "Status", "Created", "Actions"].map((h) => (
                      <th key={h} style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textAlign: "left", padding: "14px 16px", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => {
                    const roleName = ROLE_NAMES[u.role_id] || u.role_name || "Officer";
                    const isActive = u.is_active !== false;
                    return (
                      <tr key={u.user_id} style={{ borderBottom: i < users.length - 1 ? `1px solid ${T.cardBorder}` : "none", transition: "background 0.1s", cursor: "pointer" }}
                        onMouseEnter={(e) => e.currentTarget.style.background = `${T.accent}06`}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                        onClick={() => setSelectedUser(u)}
                      >
                        <td style={{ padding: "12px 16px", display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ width: 28, height: 28, borderRadius: 6, background: `${ROLE_COLORS[u.role_id] || T.accent}18`, color: ROLE_COLORS[u.role_id] || T.accent, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700 }}>{u.full_name?.[0]}</span>
                          <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{u.full_name}</span>
                        </td>
                        <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{u.email}</td>
                        <td style={{ padding: "12px 16px" }}><Badge label={roleName} /></td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, color: isActive ? T.success : T.textMuted }}>
                            <span style={{ width: 6, height: 6, borderRadius: "50%", background: isActive ? T.success : T.textMuted }} />
                            {isActive ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>
                          {u.created_at ? u.created_at.split("T")[0] : "—"}
                        </td>
                        <td style={{ padding: "12px 16px" }} onClick={(e) => e.stopPropagation()}>
                          <div style={{ display: "flex", gap: 4 }}>
                            <button onClick={() => { setEditUser(u); setShowFormModal(true); }} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.accent}15`, color: T.accent, fontSize: 11, cursor: "pointer" }}>Edit</button>
                            <button onClick={() => setResetPwdUser(u)} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.warning}15`, color: T.warning, fontSize: 11, cursor: "pointer" }}>Pwd</button>
                            <button onClick={() => handleDeleteConfirm(u)} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.danger}15`, color: T.danger, fontSize: 11, cursor: "pointer" }}>{isActive ? "Deact" : "Activate"}</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {/* ── Pagination ── */}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderTop: `1px solid ${T.cardBorder}` }}>
                <span style={{ color: T.textMuted, fontSize: 12 }}>{total} users total</span>
                <div style={{ display: "flex", gap: 4 }}>
                  <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: page <= 1 ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page <= 1 ? "default" : "pointer" }}>Prev</button>
                  {pages.slice(Math.max(0, page - 3), Math.min(totalPages, page + 2)).map((p) => (
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
