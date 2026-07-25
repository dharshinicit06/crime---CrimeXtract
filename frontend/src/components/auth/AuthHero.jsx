import { T } from "../../styles/theme";
import AuthFeatures from "./AuthFeatures";

export default function AuthHero({ isVertical = false }) {
  return (
    <div
      style={{
        flex: isVertical ? "none" : "55%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: isVertical ? "48px 28px 24px" : "60px 48px 60px 60px",
        maxWidth: isVertical ? "100%" : 640,
      }}
    >
      {/* Logo + Badge */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 32 }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 14,
            background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 22,
            flexShrink: 0,
            boxShadow: `0 8px 24px ${T.accentGlow}`,
          }}
          aria-hidden="true"
        >
          🛡
        </div>
        <div>
          <div style={{ color: T.textPrimary, fontWeight: 800, fontSize: 20, letterSpacing: "-0.5px" }}>
            CrimeAI
          </div>
          <div style={{ color: T.textMuted, fontSize: 12, fontWeight: 500, letterSpacing: "0.3px" }}>
            Karnataka State Police
          </div>
        </div>
      </div>

      {/* Main Heading */}
      <h1
        style={{
          color: T.textPrimary,
          fontSize: isVertical ? 32 : 40,
          fontWeight: 800,
          lineHeight: 1.15,
          letterSpacing: "-0.8px",
          margin: 0,
        }}
      >
        Intelligence Platform
        <br />
        <span style={{ background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          for Modern Policing
        </span>
      </h1>

      {/* Description */}
      <p
        style={{
          color: T.textSecondary,
          fontSize: 15,
          lineHeight: 1.7,
          marginTop: 16,
          maxWidth: 480,
        }}
      >
        AI-powered crime analytics, conversational investigation support,
        criminal intelligence, predictive policing and real-time insights
        for Karnataka State Police officers.
      </p>

      {/* Features Grid */}
      <AuthFeatures />
    </div>
  );
}
