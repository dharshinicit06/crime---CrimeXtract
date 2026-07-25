import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { T } from "../styles/theme";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { useAuth } from "../context/AuthContext";
import AuthHero from "../components/auth/AuthHero";
import AuthCard from "../components/auth/AuthCard";
import SignupFooter from "../components/auth/SignupFooter";
import { Mail, Lock, User, Phone, Eye, EyeOff, Loader2 } from "lucide-react";
import { validateEmail, EMAIL_RULES, validatePassword, PASSWORD_RULES, validatePhone, PHONE_RULES, validateName, NAME_RULES, validateConfirmPassword } from "../utils/validation";

const ROLES = ["Crime Analyst", "Investigator", "Supervisor", "Policymaker"];

const GLOW_BASE = {
  position: "absolute",
  borderRadius: "50%",
  pointerEvents: "none",
};

export default function SignupPage() {
  const isTabletOrMobile = useMediaQuery("(max-width: 900px)");
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "Crime Analyst",
    phone: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");

  const inputFocus = {
    outline: "none",
    transition: "border 0.2s, box-shadow 0.2s",
  };

  const updateField = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }));
    setErrors((p) => ({ ...p, [field]: "" }));
  };

  const validate = () => {
    const errs = {};
    const fnErr = validateName(form.firstName, true);
    if (fnErr) errs.firstName = fnErr;
    const lnErr = validateName(form.lastName, true);
    if (lnErr) errs.lastName = lnErr;
    const emailErr = validateEmail(form.email, true);
    if (emailErr) errs.email = emailErr;
    const pwdErr = validatePassword(form.password, true);
    if (pwdErr) errs.password = pwdErr;
    const confirmErr = validateConfirmPassword(form.confirmPassword, form.password, true);
    if (confirmErr) errs.confirmPassword = confirmErr;
    if (!form.role) errs.role = "Please select an option.";
    const phoneErr = validatePhone(form.phone, false);
    if (phoneErr) errs.phone = phoneErr;
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      const payload = {
        name: `${form.firstName} ${form.lastName}`.trim(),
        email: form.email,
        password: form.password,
        phone: form.phone || undefined,
        role: form.role,
      };
      await signup(payload);
      navigate("/", { replace: true });
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Registration failed. Please try again.";
      setApiError(msg);
    } finally {
      setLoading(false);
    }
  };

  const renderField = ({ field, label, type = "text", placeholder, icon: Icon, autoComplete, width }) => {
    const isPassword = type === "password";
    const showState = field === "password" ? showPassword : showConfirmPassword;
    const toggleShow = field === "password" ? setShowPassword : setShowConfirmPassword;

    return (
      <div style={{ marginBottom: 14, width: width || "100%" }}>
        <label
          style={{
            display: "block",
            fontSize: 13,
            color: T.textSecondary,
            marginBottom: 6,
            fontWeight: 500,
          }}
        >
          {label}
        </label>
        <div style={{ position: "relative" }}>
          {Icon && (
            <Icon
              size={16}
              style={{
                position: "absolute",
                left: 14,
                top: "50%",
                transform: "translateY(-50%)",
                color: T.textMuted,
                pointerEvents: "none",
              }}
            />
          )}
          <input
            type={isPassword ? (showState ? "text" : "password") : type}
            value={form[field]}
            onChange={(e) => updateField(field, e.target.value)}
            placeholder={placeholder}
            autoComplete={autoComplete}
            onFocus={(e) => { e.currentTarget.style.borderColor = T.inputBorderFocus; e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = errors[field] ? T.danger : T.inputBorder; e.currentTarget.style.boxShadow = "none"; }}
            style={{
              width: "100%",
              padding: Icon ? "12px 42px 12px 42px" : "12px 14px",
              background: T.inputBg,
              border: `1px solid ${errors[field] ? T.danger : T.inputBorder}`,
              borderRadius: 10,
              color: T.textPrimary,
              fontSize: 14,
              boxSizing: "border-box",
              ...inputFocus,
            }}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => toggleShow(!showState)}
              aria-label={showState ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
              style={{
                position: "absolute",
                right: 14,
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                color: T.textMuted,
                padding: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {showState ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          )}
        </div>
        {errors[field] && (
          <p style={{ color: T.danger, fontSize: 12, margin: "4px 0 0" }}>{errors[field]}</p>
        )}
      </div>
    );
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: T.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Inter, -apple-system, sans-serif",
        position: "relative",
        overflow: "auto",
      }}
    >
      {/* Glowing background gradients */}
      <div style={{ ...GLOW_BASE, top: "10%", left: "5%", width: 600, height: 600, background: `radial-gradient(circle, ${T.accent}06 0%, transparent 70%)` }} />
      <div style={{ ...GLOW_BASE, bottom: "5%", right: "0%", width: 500, height: 500, background: `radial-gradient(circle, ${T.purple}06 0%, transparent 70%)` }} />
      <div style={{ ...GLOW_BASE, top: "50%", right: "30%", width: 300, height: 300, background: `radial-gradient(circle, ${T.accent}04 0%, transparent 60%)` }} />

      <div
        style={{
          display: "flex",
          flexDirection: isTabletOrMobile ? "column" : "row",
          width: "100%",
          maxWidth: 1280,
          minHeight: "100vh",
          position: "relative",
          zIndex: 1,
        }}
      >
        <AuthHero isVertical={isTabletOrMobile} />
        <AuthCard
          title="Officer Registration"
          subtitle="Register using your official Karnataka Police email"
          isVertical={isTabletOrMobile}
        >
          <form onSubmit={handleSubmit} style={{ width: "100%" }}>
            {/* API Error */}
            {apiError && (
              <div
                style={{
                  padding: "10px 14px",
                  borderRadius: 10,
                  background: "rgba(239,68,68,0.1)",
                  border: "1px solid rgba(239,68,68,0.2)",
                  color: T.danger,
                  fontSize: 13,
                  marginBottom: 16,
                  lineHeight: 1.5,
                }}
                role="alert"
              >
                {apiError}
              </div>
            )}

            {/* First Name + Last Name */}
            <div style={{ display: "flex", gap: 12 }}>
              {renderField({ field: "firstName", label: "First Name", placeholder: NAME_RULES.placeholder, icon: User, autoComplete: "given-name", width: "50%" })}
              {renderField({ field: "lastName", label: "Last Name", placeholder: NAME_RULES.placeholder, autoComplete: "family-name", width: "50%" })}
            </div>

            {/* Email */}
            {renderField({ field: "email", label: "Email Address", type: "email", placeholder: EMAIL_RULES.placeholder, icon: Mail, autoComplete: "email" })}

            {/* Role */}
            <div style={{ marginBottom: 14 }}>
              <label
                style={{
                  display: "block",
                  fontSize: 13,
                  color: T.textSecondary,
                  marginBottom: 6,
                  fontWeight: 500,
                }}
              >
                Role
              </label>
              <select
                value={form.role}
                onChange={(e) => updateField("role", e.target.value)}
                onFocus={(e) => { e.currentTarget.style.borderColor = T.inputBorderFocus; e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = errors.role ? T.danger : T.inputBorder; e.currentTarget.style.boxShadow = "none"; }}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  background: T.inputBg,
                  border: `1px solid ${errors.role ? T.danger : T.inputBorder}`,
                  borderRadius: 10,
                  color: T.textPrimary,
                  fontSize: 14,
                  boxSizing: "border-box",
                  cursor: "pointer",
                  ...inputFocus,
                }}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
              {errors.role && (
                <p style={{ color: T.danger, fontSize: 12, margin: "4px 0 0" }}>{errors.role}</p>
              )}
            </div>

            {/* Password */}
            {renderField({ field: "password", label: "Password", type: "password", placeholder: PASSWORD_RULES.placeholder, icon: Lock, autoComplete: "new-password" })}

            {/* Confirm Password */}
            {renderField({ field: "confirmPassword", label: "Confirm Password", type: "password", placeholder: "Confirm your password", icon: Lock, autoComplete: "new-password" })}

            {/* Phone */}
            {renderField({ field: "phone", label: "Phone (optional)", type: "tel", placeholder: PHONE_RULES.placeholder, icon: Phone, autoComplete: "tel" })}

            {/* Register Button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "12px 20px",
                borderRadius: 10,
                background: loading ? T.accentHover : T.accent,
                color: "#fff",
                border: "none",
                fontSize: 14,
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
                transition: "all 0.2s",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                outline: "none",
                marginTop: 4,
              }}
              onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.background = T.accentHover; e.currentTarget.style.transform = "translateY(-1px)"; } }}
              onMouseLeave={(e) => { e.currentTarget.style.background = T.accent; e.currentTarget.style.transform = "none"; }}
              onFocus={(e) => { e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
              onBlur={(e) => { e.currentTarget.style.boxShadow = "none"; }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} style={{ animation: "signup-spin 0.8s linear infinite" }} />
                  Registering…
                </>
              ) : (
                "Register"
              )}
            </button>

            <style>{`
              @keyframes signup-spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
          </form>

          <SignupFooter />
        </AuthCard>
      </div>
    </div>
  );
}
