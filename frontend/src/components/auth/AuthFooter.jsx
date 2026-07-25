import { useState } from "react";
import { Link } from "react-router-dom";
import { T } from "../../styles/theme";

export default function AuthFooter() {
  const [linkFocus, setLinkFocus] = useState(false);

  return (
    <div style={{ marginTop: 24, textAlign: "center" }}>
      <p style={{ color: T.textMuted, fontSize: 12, margin: 0, lineHeight: 1.6 }}>
        Don't have an account?{" "}
        <Link
          to="/signup"
          style={{
            color: linkFocus ? T.accentHover : T.accent,
            textDecoration: "none",
            fontWeight: 600,
            fontSize: 12,
            outline: "none",
            borderRadius: 4,
            padding: "2px 4px",
            transition: "color 0.2s ease, box-shadow 0.2s ease",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = T.accentHover; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = T.accent; }}
          onFocus={() => setLinkFocus(true)}
          onBlur={() => setLinkFocus(false)}
        >
          Register as Officer →
        </Link>
      </p>

    </div>
  );
}
