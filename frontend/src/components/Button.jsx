import { useState } from "react";
import { T } from "../styles/theme";

const VARIANTS = {
  primary: { background: T.accent, color: "#fff", border: "none" },
  secondary: {
    background: "transparent",
    color: T.textSecondary,
    border: `1px solid ${T.cardBorder}`,
  },
  danger: {
    background: "rgba(239,68,68,0.15)",
    color: T.danger,
    border: "1px solid rgba(239,68,68,0.3)",
  },
};

export default function Button({
  children,
  onClick,
  variant = "primary",
  style: extStyle = {},
  disabled,
}) {
  const [hover, setHover] = useState(false);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        ...VARIANTS[variant],
        padding: "10px 20px",
        borderRadius: 10,
        fontSize: 14,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.2s",
        opacity: disabled ? 0.5 : 1,
        transform: hover && !disabled ? "translateY(-1px)" : "none",
        ...extStyle,
      }}
    >
      {children}
    </button>
  );
}
