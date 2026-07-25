import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { T } from "../styles/theme";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { useAuth } from "../context/AuthContext";
import AuthHero from "../components/auth/AuthHero";
import AuthCard from "../components/auth/AuthCard";
import AuthFooter from "../components/auth/AuthFooter";
import { Mail, Lock, Eye, EyeOff, Loader2 } from "lucide-react";
import { validateEmail, EMAIL_RULES, validatePassword, PASSWORD_RULES } from "../utils/validation";

const GLOW_BASE = {
  position: "absolute",
  borderRadius: "50%",
  pointerEvents: "none",
};

export default function LoginPage() {
  const isTabletOrMobile = useMediaQuery("(max-width: 900px)");
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");

  const inputFocus = {
    outline: "none",
    transition: "border 0.2s, box-shadow 0.2s",
  };

  const validate = () => {
    const errs = {};
    const emailErr = validateEmail(email, true);
    if (emailErr) errs.email = emailErr;
    const pwdErr = validatePassword(password, true);
    if (pwdErr) errs.password = pwdErr;
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Invalid email or password. Please try again.";
      setApiError(msg);
    } finally {
      setLoading(false);
    }
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
          title="Officer Sign In"
          subtitle="Secure authentication using your official credentials"
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

            {/* Email Field */}
            <div style={{ marginBottom: 16 }}>
              <label
                style={{
                  display: "block",
                  fontSize: 13,
                  color: T.textSecondary,
                  marginBottom: 6,
                  fontWeight: 500,
                }}
              >
                Email Address
              </label>
              <div style={{ position: "relative" }}>
                <Mail
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
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: "" })); }}
                  placeholder={EMAIL_RULES.placeholder}
                  autoComplete="email"
                  onFocus={(e) => { e.currentTarget.style.borderColor = T.inputBorderFocus; e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = errors.email ? T.danger : T.inputBorder; e.currentTarget.style.boxShadow = "none"; }}
                  style={{
                    width: "100%",
                    padding: "12px 14px 12px 42px",
                    background: T.inputBg,
                    border: `1px solid ${errors.email ? T.danger : T.inputBorder}`,
                    borderRadius: 10,
                    color: T.textPrimary,
                    fontSize: 14,
                    boxSizing: "border-box",
                    ...inputFocus,
                  }}
                />
              </div>
              {errors.email && (
                <p style={{ color: T.danger, fontSize: 12, margin: "4px 0 0" }}>{errors.email}</p>
              )}
            </div>

            {/* Password Field */}
            <div style={{ marginBottom: 12 }}>
              <label
                style={{
                  display: "block",
                  fontSize: 13,
                  color: T.textSecondary,
                  marginBottom: 6,
                  fontWeight: 500,
                }}
              >
                Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock
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
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: "" })); }}
                  placeholder={PASSWORD_RULES.placeholder}
                  autoComplete="current-password"
                  onFocus={(e) => { e.currentTarget.style.borderColor = T.inputBorderFocus; e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = errors.password ? T.danger : T.inputBorder; e.currentTarget.style.boxShadow = "none"; }}
                  style={{
                    width: "100%",
                    padding: "12px 42px 12px 42px",
                    background: T.inputBg,
                    border: `1px solid ${errors.password ? T.danger : T.inputBorder}`,
                    borderRadius: 10,
                    color: T.textPrimary,
                    fontSize: 14,
                    boxSizing: "border-box",
                    ...inputFocus,
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
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
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && (
                <p style={{ color: T.danger, fontSize: 12, margin: "4px 0 0" }}>{errors.password}</p>
              )}
            </div>

            {/* Remember Me + Forgot Password */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 20,
              }}
            >
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  cursor: "pointer",
                  color: T.textMuted,
                  fontSize: 13,
                }}
              >
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  style={{
                    width: 16,
                    height: 16,
                    accentColor: T.accent,
                    cursor: "pointer",
                  }}
                />
                Remember me
              </label>
              <button
                type="button"
                onClick={() => {/* Placeholder: implement forgot password flow */}}
                style={{
                  background: "none",
                  border: "none",
                  color: T.accent,
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  padding: 0,
                  textDecoration: "none",
                  transition: "color 0.2s",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = T.accentHover; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = T.accent; }}
              >
                Forgot Password?
              </button>
            </div>

            {/* Login Button */}
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
              }}
              onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.background = T.accentHover; e.currentTarget.style.transform = "translateY(-1px)"; } }}
              onMouseLeave={(e) => { e.currentTarget.style.background = T.accent; e.currentTarget.style.transform = "none"; }}
              onFocus={(e) => { e.currentTarget.style.boxShadow = `0 0 0 3px ${T.accentGlow}`; }}
              onBlur={(e) => { e.currentTarget.style.boxShadow = "none"; }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} style={{ animation: "login-spin 0.8s linear infinite" }} />
                  Signing in…
                </>
              ) : (
                "Sign In"
              )}
            </button>

            {/* Spinner keyframes */}
            <style>{`
              @keyframes login-spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
          </form>

          <AuthFooter />
        </AuthCard>
      </div>
    </div>
  );
}
