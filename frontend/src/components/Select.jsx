import { useState } from "react";
import { T } from "../styles/theme";

export default function Select({
  label,
  value,
  onChange,
  options = [],
  placeholder = "— None —",
  icon,
  error,
  helper,
  required,
  disabled,
  getLabel,
  getValue,
}) {
  const [focus, setFocus] = useState(false);

  const selectStyle = {
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
    cursor: disabled ? "not-allowed" : "pointer",
    appearance: "auto",
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
              zIndex: 1,
            }}
          >
            {icon}
          </span>
        )}
        <select
          value={value}
          onChange={onChange}
          disabled={disabled}
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          style={selectStyle}
        >
          {placeholder !== false && (
            <option value="">{placeholder}</option>
          )}
          {options.map((opt, i) => {
            const optValue = getValue ? getValue(opt) : (typeof opt === "object" ? opt.value ?? opt.id ?? i : opt);
            const optLabel = getLabel ? getLabel(opt) : (typeof opt === "object" ? opt.label ?? opt.name ?? String(optValue) : opt);
            return (
              <option key={optValue} value={optValue}>
                {optLabel}
              </option>
            );
          })}
        </select>
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
