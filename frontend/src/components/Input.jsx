import { useState } from "react";
import { T } from "../styles/theme";

export default function Input({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  icon,
  error,
  helper,
  required,
  disabled,
  min,
  max,
  step,
  maxLength,
}) {
  const [focus, setFocus] = useState(false);

  const inputStyle = {
    width: "100%",
    padding: icon ? "12px 14px 12px 42px" : "12px 14px",
    background: T.inputBg,
    border: `1px solid ${error ? T.danger : focus ? T.inputBorderFocus : T.inputBorder}`,
    borderRadius: 10,
    color: T.textPrimary,
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
    transition: "border 0.2s",
    boxShadow: error
      ? `0 0 0 3px rgba(239,68,68,0.15)`
      : focus
        ? `0 0 0 3px ${T.accentGlow}`
        : "none",
    opacity: disabled ? 0.6 : 1,
    cursor: disabled ? "not-allowed" : "text",
  };

  return (
    <div style={{ marginBottom: 16 }}>
      {label && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 6 }}>
          <label
            style={{
              display: "block",
              fontSize: 13,
              color: T.textSecondary,
              fontWeight: 500,
            }}
          >
            {label}
          </label>
          {required && (
            <span style={{ color: T.danger, fontSize: 13 }}>*</span>
          )}
        </div>
      )}
      <div style={{ position: "relative" }}>
        {icon && (
          <span
            style={{
              position: "absolute",
              left: 14,
              top: "50%",
              transform: "translateY(-50%)",
              fontSize: 16,
              color: T.textMuted,
              pointerEvents: "none",
            }}
          >
            {icon}
          </span>
        )}
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          min={min}
          max={max}
          step={step}
          maxLength={maxLength}
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          style={inputStyle}
        />
      </div>
      {helper && !error && (
        <p style={{ color: T.textMuted, fontSize: 11, margin: "4px 0 0", lineHeight: 1.4 }}>
          {helper}
        </p>
      )}
      {error && (
        <p style={{ color: T.danger, fontSize: 11, margin: "4px 0 0", lineHeight: 1.4 }}>
          {error}
        </p>
      )}
    </div>
  );
}
