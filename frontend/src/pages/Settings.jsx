import { useState, useEffect, useCallback } from "react";
import { T } from "../styles/theme";
import {
  getProfile,
  updateProfile,
  changePassword,
  getPreferences,
  updatePreferences,
  getSystemInfo,
  logoutAllSessions,
} from "../services/settingsService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";

// ═══════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════

const ANIM_STYLES = `
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
`;

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

const ROLE_NAMES = { 1: "Admin", 2: "Investigator", 3: "Analyst", 4: "Supervisor" };

const TABS = [
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "security", label: "Security", icon: "🔒" },
  { id: "preferences", label: "Preferences", icon: "🎨" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "administration", label: "Administration", icon: "⚙", adminOnly: true },
];

const INPUT_STYLE = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${T.inputBorder}`,
  background: T.inputBg,
  color: T.textPrimary,
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
  transition: "border-color 0.2s",
};

const SELECT_STYLE = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${T.inputBorder}`,
  background: T.inputBg,
  color: T.textPrimary,
  fontSize: 13,
  outline: "none",
  cursor: "pointer",
  boxSizing: "border-box",
};

const LABEL_STYLE = {
  display: "block",
  color: T.textSecondary,
  fontSize: 11,
  fontWeight: 600,
  marginBottom: 4,
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};

// ═══════════════════════════════════════════════════════════════
// TOAST COMPONENT
// ═══════════════════════════════════════════════════════════════

function Toast({ toast, onClose }) {
  if (!toast) return null;
  const isSuccess = toast.type === "success";
  const isWarning = toast.type === "warning";

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(onClose, 3500);
      return () => clearTimeout(timer);
    }
  }, [toast, onClose]);

  if (!toast) return null;

  const bg = isSuccess ? T.success : isWarning ? T.warning : T.danger;

  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        right: 20,
        zIndex: 2000,
        padding: "12px 20px",
        borderRadius: 10,
        background: bg,
        color: "#fff",
        fontSize: 13,
        fontWeight: 600,
        boxShadow: `0 4px 16px ${bg}44`,
        animation: "slideUp 0.25s ease",
        display: "flex",
        alignItems: "center",
        gap: 8,
        cursor: "pointer",
      }}
      onClick={onClose}
    >
      <span>{isSuccess ? "✅" : isWarning ? "⚠️" : "❌"}</span>
      {toast.message}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// CARD WRAPPER
// ═══════════════════════════════════════════════════════════════

function Card({ title, subtitle, children, style }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 28,
        marginBottom: 20,
        animation: "slideUp 0.3s ease",
        ...style,
      }}
    >
      {title && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: 0, fontSize: 16 }}>
            {title}
          </h3>
          {subtitle && (
            <p style={{ color: T.textMuted, fontSize: 12, margin: "4px 0 0", lineHeight: 1.4 }}>
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SKELETON
// ═══════════════════════════════════════════════════════════════

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

// ═══════════════════════════════════════════════════════════════
// TOGGLE SWITCH
// ═══════════════════════════════════════════════════════════════

function ToggleSwitch({ checked, onChange, label, sub }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 0",
        borderBottom: `1px solid ${T.cardBorder}`,
        gap: 16,
      }}
    >
      <div>
        <div style={{ color: T.textPrimary, fontSize: 14, fontWeight: 500 }}>{label}</div>
        {sub && <div style={{ color: T.textMuted, fontSize: 12, marginTop: 2 }}>{sub}</div>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        style={{
          width: 44,
          height: 24,
          borderRadius: 12,
          border: "none",
          cursor: "pointer",
          background: checked ? T.accent : T.textMuted,
          position: "relative",
          transition: "background 0.2s",
          flexShrink: 0,
          padding: 0,
        }}
      >
        <div
          style={{
            width: 18,
            height: 18,
            borderRadius: "50%",
            background: "#fff",
            position: "absolute",
            top: 3,
            left: checked ? 23 : 3,
            transition: "left 0.2s",
            boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
          }}
        />
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// TAB BUTTONS
// ═══════════════════════════════════════════════════════════════

function TabBar({ tabs, activeTab, setActiveTab }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        marginBottom: 24,
        padding: 4,
        background: T.surface,
        borderRadius: 12,
        border: `1px solid ${T.cardBorder}`,
        overflowX: "auto",
        flexWrap: "nowrap",
      }}
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "none",
            background: activeTab === tab.id ? T.accent : "transparent",
            color: activeTab === tab.id ? "#fff" : T.textSecondary,
            fontSize: 13,
            fontWeight: activeTab === tab.id ? 600 : 400,
            cursor: "pointer",
            transition: "all 0.2s",
            whiteSpace: "nowrap",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span>{tab.icon}</span>
          <span>{tab.label}</span>
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// PASSWORD STRENGTH INDICATOR
// ═══════════════════════════════════════════════════════════════

function getPasswordStrength(password) {
  let score = 0;
  if (password.length >= 8) score += 25;
  if (password.length >= 12) score += 15;
  if (/[A-Z]/.test(password)) score += 20;
  if (/[a-z]/.test(password)) score += 10;
  if (/[0-9]/.test(password)) score += 15;
  if (/[^A-Za-z0-9]/.test(password)) score += 15;
  return Math.min(score, 100);
}

function PasswordStrengthBar({ password }) {
  if (!password) return null;
  const strength = getPasswordStrength(password);
  const getColor = () => {
    if (strength < 30) return T.danger;
    if (strength < 60) return T.warning;
    if (strength < 80) return T.accent;
    return T.success;
  };
  const getLabel = () => {
    if (strength < 30) return "Weak";
    if (strength < 60) return "Fair";
    if (strength < 80) return "Good";
    return "Strong";
  };

  return (
    <div style={{ marginTop: 6 }}>
      <div
        style={{
          height: 4,
          borderRadius: 2,
          background: T.inputBorder,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${strength}%`,
            height: "100%",
            borderRadius: 2,
            background: getColor(),
            transition: "width 0.3s ease, background 0.3s ease",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: 3,
        }}
      >
        <span style={{ color: getColor(), fontSize: 10, fontWeight: 600 }}>{getLabel()}</span>
        <span style={{ color: T.textMuted, fontSize: 10 }}>{strength}%</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════
// MAIN SETTINGS PAGE
// ═══════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════

export default function Settings({ user }) {
  const isAdmin = user?.role_id === 1;
  const availableTabs = TABS.filter((t) => !t.adminOnly || isAdmin);
  const [activeTab, setActiveTab] = useState("profile");

  // ── Toast state ─────────────────────────────────────────
  const [toast, setToast] = useState(null);
  const showToast = (message, type = "success") => {
    setToast({ message, type });
  };

  // ── Profile state ───────────────────────────────────────
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);
  const [profileForm, setProfileForm] = useState({ full_name: "", email: "", phone: "" });
  const [profileSaving, setProfileSaving] = useState(false);

  // ── Password state ──────────────────────────────────────
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPassword, setShowPassword] = useState({ current: false, new: false, confirm: false });
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  // ── Preferences state ───────────────────────────────────
  const [preferences, setPreferences] = useState(null);
  const [prefsLoading, setPrefsLoading] = useState(true);
  const [prefSaving, setPrefSaving] = useState(false);

  // ── System info state (admin) ──────────────────────────
  const [systemInfo, setSystemInfo] = useState(null);
  const [sysInfoLoading, setSysInfoLoading] = useState(false);

  // ══════════════════════════════════════════════════════════
  // Fetch: Profile
  // ══════════════════════════════════════════════════════════

  const fetchProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError(null);
    try {
      const data = await getProfile();
      setProfile(data);
      setProfileForm({
        full_name: data.full_name || "",
        email: data.email || "",
        phone: data.phone || "",
      });
    } catch (err) {
      setProfileError(err?.response?.data?.detail || "Failed to load profile");
    } finally {
      setProfileLoading(false);
    }
  }, []);

  // ══════════════════════════════════════════════════════════
  // Fetch: Preferences
  // ══════════════════════════════════════════════════════════

  const fetchPreferences = useCallback(async () => {
    setPrefsLoading(true);
    try {
      const data = await getPreferences();
      setPreferences(data);
    } catch (err) {
      console.error("Failed to load preferences:", err);
    } finally {
      setPrefsLoading(false);
    }
  }, []);

  // ══════════════════════════════════════════════════════════
  // Load profile + preferences in parallel
  // ══════════════════════════════════════════════════════════

  useEffect(() => {
    fetchProfile();
    fetchPreferences();
  }, [fetchProfile, fetchPreferences]);

  // ══════════════════════════════════════════════════════════
  // Fetch: System Info (admin)
  // ══════════════════════════════════════════════════════════

  const fetchSystemInfo = useCallback(async () => {
    setSysInfoLoading(true);
    try {
      const data = await getSystemInfo();
      setSystemInfo(data);
    } catch (err) {
      console.error("Failed to load system info:", err);
    } finally {
      setSysInfoLoading(false);
    }
  }, []);

  // ══════════════════════════════════════════════════════════
  // Handlers: Profile
  // ══════════════════════════════════════════════════════════

  const handleProfileSave = async () => {
    if (!profileForm.full_name.trim()) {
      showToast("Full name is required", "error");
      return;
    }
    if (!profileForm.email.trim()) {
      showToast("Email is required", "error");
      return;
    }
    setProfileSaving(true);
    try {
      const data = {};
      if (profileForm.full_name !== profile?.full_name) data.full_name = profileForm.full_name.trim();
      if (profileForm.email !== profile?.email) data.email = profileForm.email.trim();
      if (profileForm.phone !== (profile?.phone || "")) data.phone = profileForm.phone.trim() || null;

      if (Object.keys(data).length === 0) {
        showToast("No changes to save", "warning");
        setProfileSaving(false);
        return;
      }

      const updated = await updateProfile(data);
      setProfile(updated);
      showToast("Profile updated successfully");
    } catch (err) {
      showToast(err?.response?.data?.detail || "Failed to update profile", "error");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleProfileCancel = () => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name || "",
        email: profile.email || "",
        phone: profile.phone || "",
      });
    }
  };

  // ══════════════════════════════════════════════════════════
  // Handlers: Password
  // ══════════════════════════════════════════════════════════

  const handlePasswordChange = async () => {
    setPasswordError("");
    if (!passwordForm.current_password) {
      setPasswordError("Current password is required");
      return;
    }
    if (!passwordForm.new_password) {
      setPasswordError("New password is required");
      return;
    }
    if (passwordForm.new_password.length < 8) {
      setPasswordError("New password must be at least 8 characters");
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError("Passwords do not match");
      return;
    }

    setPasswordSaving(true);
    try {
      await changePassword(passwordForm.current_password, passwordForm.new_password);
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      showToast("Password changed successfully");
    } catch (err) {
      setPasswordError(err?.response?.data?.detail || "Failed to change password");
    } finally {
      setPasswordSaving(false);
    }
  };

  // ══════════════════════════════════════════════════════════
  // Handlers: Preferences
  // ══════════════════════════════════════════════════════════

  const handlePreferenceChange = async (field, value) => {
    const updated = { ...preferences, [field]: value };
    setPreferences(updated);
    setPrefSaving(true);
    try {
      await updatePreferences({ [field]: value });
      // No toast for individual toggle — too noisy
    } catch (err) {
      // Revert on error
      setPreferences(preferences);
      showToast("Failed to update preference", "error");
    } finally {
      setPrefSaving(false);
    }
  };

  // ══════════════════════════════════════════════════════════
  // TAB RENDERERS
  // ══════════════════════════════════════════════════════════

  const renderProfileTab = () => (
    <Card title="Profile Information" subtitle="Update your personal details and contact information.">
      {profileLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <Skeleton width={80} height={10} />
              <Skeleton width="100%" height={36} borderRadius={8} />
            </div>
          ))}
        </div>
      ) : profileError ? (
        <div style={{ padding: 20, textAlign: "center" }}>
          <span style={{ fontSize: 28 }}>⚠️</span>
          <p style={{ color: T.danger, fontSize: 13, margin: "8px 0" }}>{profileError}</p>
          <button
            onClick={fetchProfile}
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
        </div>
      ) : (
        <>
          {/* Avatar */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 16,
                background: `linear-gradient(135deg, ${T.accent}44, ${T.purple}44)`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 28,
                fontWeight: 700,
                color: T.accent,
                flexShrink: 0,
              }}
            >
              {(profile?.full_name || user?.name)?.[0]?.toUpperCase() || "?"}
            </div>
            <div>
              <div style={{ color: T.textPrimary, fontWeight: 700, fontSize: 18 }}>
                {profile?.full_name || user?.name}
              </div>
              <div style={{ color: T.textMuted, fontSize: 13 }}>
                {profile?.email} · {ROLE_NAMES[profile?.role_id] || user?.role || "Officer"}
              </div>
            </div>
          </div>

          {/* Form fields */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Full Name</label>
              <input
                style={INPUT_STYLE}
                value={profileForm.full_name}
                onChange={(e) => setProfileForm((p) => ({ ...p, full_name: e.target.value }))}
                placeholder="Your full name"
                aria-label="Full name"
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Email</label>
              <input
                style={INPUT_STYLE}
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm((p) => ({ ...p, email: e.target.value }))}
                placeholder="Email address"
                aria-label="Email"
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Phone</label>
              <input
                style={INPUT_STYLE}
                type="tel"
                value={profileForm.phone}
                onChange={(e) => setProfileForm((p) => ({ ...p, phone: e.target.value }))}
                placeholder="Phone number (optional)"
                aria-label="Phone number"
              />
            </div>
          </div>

          {/* Role info (read-only) */}
          <div
            style={{
              marginTop: 20,
              padding: "12px 16px",
              background: T.inputBg,
              borderRadius: 8,
              border: `1px solid ${T.cardBorder}`,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: T.textMuted, fontSize: 12 }}>Role</span>
              <Badge label={ROLE_NAMES[profile?.role_id] || "Officer"} />
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: 8,
                paddingTop: 8,
                borderTop: `1px solid ${T.cardBorder}`,
              }}
            >
              <span style={{ color: T.textMuted, fontSize: 12 }}>Account Status</span>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 12,
                  color: profile?.is_active !== false ? T.success : T.textMuted,
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: profile?.is_active !== false ? T.success : T.textMuted,
                  }}
                />
                {profile?.is_active !== false ? "Active" : "Inactive"}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 20 }}>
            <button
              onClick={handleProfileCancel}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                border: `1px solid ${T.cardBorder}`,
                background: T.inputBg,
                color: T.textSecondary,
                fontSize: 13,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = T.card;
                e.currentTarget.style.color = T.textPrimary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = T.inputBg;
                e.currentTarget.style.color = T.textSecondary;
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleProfileSave}
              disabled={profileSaving}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                border: "none",
                background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                cursor: profileSaving ? "not-allowed" : "pointer",
                opacity: profileSaving ? 0.6 : 1,
                transition: "all 0.2s",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
              onMouseEnter={(e) => {
                if (!profileSaving) {
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = `0 4px 12px ${T.accent}44`;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {profileSaving ? (
                <>
                  <span style={{ animation: "pulse 1s infinite" }}>●</span>
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </>
      )}
    </Card>
  );

  const renderSecurityTab = () => (
    <>
      <Card title="Change Password" subtitle="Update your password. You'll need to enter your current password.">
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {passwordError && (
            <div
              style={{
                padding: "10px 14px",
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.2)",
                borderRadius: 8,
                color: T.danger,
                fontSize: 13,
              }}
            >
              {passwordError}
            </div>
          )}

          <div>
            <label style={LABEL_STYLE}>Current Password</label>
            <div style={{ position: "relative" }}>
              <input
                style={INPUT_STYLE}
                type={showPassword.current ? "text" : "password"}
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, current_password: e.target.value }))}
                placeholder="Enter current password"
                aria-label="Current password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((p) => ({ ...p, current: !p.current }))}
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: T.textMuted,
                  cursor: "pointer",
                  fontSize: 14,
                  padding: "4px 8px",
                }}
                aria-label={showPassword.current ? "Hide password" : "Show password"}
              >
                {showPassword.current ? "🙈" : "👁"}
              </button>
            </div>
          </div>

          <div>
            <label style={LABEL_STYLE}>New Password</label>
            <div style={{ position: "relative" }}>
              <input
                style={INPUT_STYLE}
                type={showPassword.new ? "text" : "password"}
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, new_password: e.target.value }))}
                placeholder="Min 8 characters"
                aria-label="New password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((p) => ({ ...p, new: !p.new }))}
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: T.textMuted,
                  cursor: "pointer",
                  fontSize: 14,
                  padding: "4px 8px",
                }}
                aria-label={showPassword.new ? "Hide password" : "Show password"}
              >
                {showPassword.new ? "🙈" : "👁"}
              </button>
            </div>
            <PasswordStrengthBar password={passwordForm.new_password} />
          </div>

          <div>
            <label style={LABEL_STYLE}>Confirm New Password</label>
            <div style={{ position: "relative" }}>
              <input
                style={{
                  ...INPUT_STYLE,
                  borderColor:
                    passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password
                      ? T.danger
                      : passwordForm.confirm_password
                      ? T.success
                      : T.inputBorder,
                }}
                type={showPassword.confirm ? "text" : "password"}
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, confirm_password: e.target.value }))}
                placeholder="Re-enter new password"
                aria-label="Confirm new password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((p) => ({ ...p, confirm: !p.confirm }))}
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: T.textMuted,
                  cursor: "pointer",
                  fontSize: 14,
                  padding: "4px 8px",
                }}
                aria-label={showPassword.confirm ? "Hide password" : "Show password"}
              >
                {showPassword.confirm ? "🙈" : "👁"}
              </button>
            </div>
            {passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password && (
              <span style={{ color: T.danger, fontSize: 11, marginTop: 4, display: "block" }}>
                Passwords do not match
              </span>
            )}
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
            <button
              onClick={handlePasswordChange}
              disabled={passwordSaving}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "none",
                background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                cursor: passwordSaving ? "not-allowed" : "pointer",
                opacity: passwordSaving ? 0.6 : 1,
                transition: "all 0.2s",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
              onMouseEnter={(e) => {
                if (!passwordSaving) {
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = `0 4px 12px ${T.accent}44`;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {passwordSaving ? (
                <>
                  <span style={{ animation: "pulse 1s infinite" }}>●</span>
                  Updating...
                </>
              ) : (
                "Update Password"
              )}
            </button>
          </div>
        </div>
      </Card>

      <Card title="Active Sessions" subtitle="Manage your account sessions across devices.">
        <div style={{ padding: "12px 0", textAlign: "center" }}>
          <p style={{ color: T.textMuted, fontSize: 13, margin: "0 0 12px" }}>
            You are currently logged in on this device.
          </p>
          <button
            onClick={async () => {
              try {
                await logoutAllSessions();
                showToast("All sessions logged out successfully");
              } catch (err) {
                showToast(err?.response?.data?.detail || "Failed to log out sessions", "error");
              }
            }}
            style={{
              padding: "8px 20px",
              borderRadius: 8,
              border: `1px solid ${T.cardBorder}`,
              background: T.inputBg,
              color: T.warning,
              fontSize: 12,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = `${T.warning}44`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = T.cardBorder;
            }}
          >
            🔒 Logout All Devices
          </button>
        </div>
      </Card>
    </>
  );

  const renderPreferencesTab = () => (
    <Card title="Display & Regional Settings" subtitle="Customize your experience across the platform.">
      {prefsLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i}>
              <Skeleton width={80} height={10} />
              <Skeleton width="100%" height={36} borderRadius={8} />
            </div>
          ))}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Theme */}
          <div>
            <label style={LABEL_STYLE}>Theme</label>
            <div style={{ display: "flex", gap: 8 }}>
              {["dark", "light", "system"].map((t) => (
                <button
                  key={t}
                  onClick={() => handlePreferenceChange("theme", t)}
                  style={{
                    flex: 1,
                    padding: "10px 12px",
                    borderRadius: 8,
                    border: preferences?.theme === t ? `2px solid ${T.accent}` : `1px solid ${T.cardBorder}`,
                    background: preferences?.theme === t ? `${T.accent}15` : T.inputBg,
                    color: preferences?.theme === t ? T.accent : T.textSecondary,
                    fontSize: 13,
                    fontWeight: preferences?.theme === t ? 600 : 400,
                    cursor: "pointer",
                    textTransform: "capitalize",
                    transition: "all 0.2s",
                  }}
                >
                  {t === "dark" ? "🌙 Dark" : t === "light" ? "☀️ Light" : "💻 System"}
                </button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div>
            <label style={LABEL_STYLE}>Language</label>
            <select
              style={SELECT_STYLE}
              value={preferences?.language || "en"}
              onChange={(e) => handlePreferenceChange("language", e.target.value)}
              aria-label="Language"
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी (Hindi)</option>
              <option value="kn">ಕನ್ನಡ (Kannada)</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="ta">தமிழ் (Tamil)</option>
            </select>
          </div>

          {/* Timezone */}
          <div>
            <label style={LABEL_STYLE}>Timezone</label>
            <select
              style={SELECT_STYLE}
              value={preferences?.timezone || "Asia/Kolkata"}
              onChange={(e) => handlePreferenceChange("timezone", e.target.value)}
              aria-label="Timezone"
            >
              <option value="Asia/Kolkata">India Standard Time (UTC+5:30)</option>
              <option value="UTC">Coordinated Universal Time (UTC+0)</option>
              <option value="America/New_York">Eastern (UTC-5)</option>
              <option value="America/Chicago">Central (UTC-6)</option>
              <option value="America/Los_Angeles">Pacific (UTC-8)</option>
              <option value="Europe/London">London (UTC+0)</option>
              <option value="Europe/Berlin">Berlin (UTC+1)</option>
              <option value="Asia/Dubai">Dubai (UTC+4)</option>
              <option value="Asia/Singapore">Singapore (UTC+8)</option>
              <option value="Asia/Tokyo">Tokyo (UTC+9)</option>
            </select>
          </div>

          {/* Date Format */}
          <div>
            <label style={LABEL_STYLE}>Date Format</label>
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { value: "DD/MM/YYYY", label: "31/12/2024" },
                { value: "MM/DD/YYYY", label: "12/31/2024" },
                { value: "YYYY-MM-DD", label: "2024-12-31" },
              ].map((fmt) => (
                <button
                  key={fmt.value}
                  onClick={() => handlePreferenceChange("date_format", fmt.value)}
                  style={{
                    flex: 1,
                    padding: "10px 12px",
                    borderRadius: 8,
                    border:
                      preferences?.date_format === fmt.value
                        ? `2px solid ${T.accent}`
                        : `1px solid ${T.cardBorder}`,
                    background: preferences?.date_format === fmt.value ? `${T.accent}15` : T.inputBg,
                    color: preferences?.date_format === fmt.value ? T.accent : T.textSecondary,
                    fontSize: 12,
                    fontWeight: preferences?.date_format === fmt.value ? 600 : 400,
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  {fmt.label}
                </button>
              ))}
            </div>
          </div>

          {prefSaving && (
            <div style={{ textAlign: "center", color: T.textMuted, fontSize: 11, animation: "pulse 1s infinite" }}>
              Saving...
            </div>
          )}
        </div>
      )}
    </Card>
  );

  const renderNotificationsTab = () => (
    <Card
      title="Notification Preferences"
      subtitle="Choose which notifications you receive and how they're delivered."
    >
      {prefsLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} height={48} borderRadius={8} />
          ))}
        </div>
      ) : (
        <div>
          <h4 style={{ color: T.textSecondary, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", margin: "0 0 4px" }}>
            Email & SMS
          </h4>
          <ToggleSwitch
            checked={preferences?.email_notifications !== false}
            onChange={() => handlePreferenceChange("email_notifications", !preferences?.email_notifications)}
            label="Email Notifications"
            sub="Receive updates via official email"
          />
          <ToggleSwitch
            checked={preferences?.sms_notifications === true}
            onChange={() => handlePreferenceChange("sms_notifications", !preferences?.sms_notifications)}
            label="SMS Notifications"
            sub="Receive alerts via SMS"
          />

          <h4 style={{ color: T.textSecondary, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", margin: "16px 0 4px" }}>
            Platform Alerts
          </h4>
          <ToggleSwitch
            checked={preferences?.ai_notifications !== false}
            onChange={() => handlePreferenceChange("ai_notifications", !preferences?.ai_notifications)}
            label="AI Alerts"
            sub="AI-generated crime predictions and insights"
          />
          <ToggleSwitch
            checked={preferences?.report_notifications !== false}
            onChange={() => handlePreferenceChange("report_notifications", !preferences?.report_notifications)}
            label="Report Notifications"
            sub="Weekly and automated crime summary reports"
          />
          <ToggleSwitch
            checked={preferences?.security_alerts !== false}
            onChange={() => handlePreferenceChange("security_alerts", !preferences?.security_alerts)}
            label="Security Alerts"
            sub="Account security and login notifications"
          />
        </div>
      )}
    </Card>
  );

  const renderAdministrationTab = () => (
    <>
      <Card title="System Information" subtitle="Application and server status.">
        {sysInfoLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between" }}>
                <Skeleton width={120} height={14} />
                <Skeleton width={180} height={14} />
              </div>
            ))}
          </div>
        ) : systemInfo ? (
          <div>
            {[
              { label: "Application", value: systemInfo.app_name },
              { label: "Version", value: systemInfo.app_version },
              { label: "Environment", value: systemInfo.environment },
              { label: "Python Version", value: systemInfo.python_version },
              {
                label: "Database",
                value: (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      color: systemInfo.database_status === "connected" ? T.success : T.danger,
                    }}
                  >
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background: systemInfo.database_status === "connected" ? T.success : T.danger,
                      }}
                    />
                    {systemInfo.database_status === "connected" ? "Connected" : "Disconnected"}
                  </span>
                ),
              },
              { label: "Server Time", value: new Date(systemInfo.server_time).toLocaleString("en-IN") },
            ].map((item, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 0",
                  borderBottom: i < 5 ? `1px solid ${T.cardBorder}` : "none",
                }}
              >
                <span style={{ color: T.textMuted, fontSize: 13 }}>{item.label}</span>
                <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{item.value}</span>
              </div>
            ))}
            <div style={{ marginTop: 16 }}>
              <button
                onClick={fetchSystemInfo}
                style={{
                  padding: "6px 14px",
                  borderRadius: 6,
                  border: `1px solid ${T.cardBorder}`,
                  background: T.inputBg,
                  color: T.accent,
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: 12 }}>
            <button
              onClick={() => {
                fetchSystemInfo();
              }}
              style={{
                padding: "8px 20px",
                borderRadius: 8,
                border: `1px solid ${T.cardBorder}`,
                background: T.inputBg,
                color: T.accent,
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              Load System Info
            </button>
          </div>
        )}
      </Card>

      <Card title="Administration Panel" subtitle="Quick access to administrative functions.">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { icon: "👥", label: "User Management", desc: "Manage officers, investigators, and analysts", path: "/users" },
            { icon: "📝", label: "Audit Logs", desc: "View system activity and change history", path: "/audit-logs" },
            { icon: "🔑", label: "Role Management", desc: "Configure roles and permissions", path: "/users" },
          ].map((item, i) => (
            <a
              key={i}
              href={item.path}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "14px 16px",
                borderRadius: 10,
                background: T.inputBg,
                border: `1px solid ${T.cardBorder}`,
                textDecoration: "none",
                transition: "all 0.2s",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = `${T.accent}33`;
                e.currentTarget.style.background = `${T.accent}08`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = T.cardBorder;
                e.currentTarget.style.background = T.inputBg;
              }}
            >
              <span style={{ fontSize: 20 }}>{item.icon}</span>
              <div>
                <div style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600 }}>{item.label}</div>
                <div style={{ color: T.textMuted, fontSize: 12 }}>{item.desc}</div>
              </div>
              <span style={{ marginLeft: "auto", color: T.textMuted, fontSize: 16 }}>→</span>
            </a>
          ))}
        </div>
      </Card>
    </>
  );

  // ══════════════════════════════════════════════════════════
  // MAIN RENDER
  // ══════════════════════════════════════════════════════════

  return (
    <PageShell title="Settings" user={user}>
      <style>{ANIM_STYLES}</style>

      <Toast toast={toast} onClose={() => setToast(null)} />

      <div style={{ width: "100%", maxWidth: 720, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>
            Settings
          </h1>
          <p style={{ color: T.textSecondary, fontSize: 13, margin: 0 }}>
            Manage your profile, security, preferences, and more
          </p>
        </div>

        {/* Tab Navigation */}
        <TabBar tabs={availableTabs} activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Tab Content */}
        {activeTab === "profile" && renderProfileTab()}
        {activeTab === "security" && renderSecurityTab()}
        {activeTab === "preferences" && renderPreferencesTab()}
        {activeTab === "notifications" && renderNotificationsTab()}
        {activeTab === "administration" && renderAdministrationTab()}
      </div>
    </PageShell>
  );
}
