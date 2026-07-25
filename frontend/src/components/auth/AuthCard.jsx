import { T } from "../../styles/theme";

export default function AuthCard({ title, subtitle, children, isVertical = false }) {
  return (
    <div
      style={{
        flex: isVertical ? "none" : "45%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: isVertical ? "0 28px 48px" : 40,
        width: isVertical ? "100%" : "auto",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 440,
          background: T.card,
          border: `1px solid ${T.cardBorder}`,
          borderRadius: 20,
          padding: isVertical ? 28 : 40,
          boxShadow: "0 15px 60px rgba(0,0,0,0.3), 0 0 80px rgba(91,127,255,0.03)",
          backdropFilter: "blur(4px)",
        }}
      >
        {/* Title Section */}
        <div style={{ marginBottom: 32 }}>
          <h2
            style={{
              color: T.textPrimary,
              fontSize: 24,
              fontWeight: 700,
              margin: 0,
              letterSpacing: "-0.3px",
            }}
          >
            {title}
          </h2>
          {subtitle && (
            <p
              style={{
                color: T.textMuted,
                fontSize: 13,
                margin: "6px 0 0",
                lineHeight: 1.5,
              }}
            >
              {subtitle}
            </p>
          )}
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: T.cardBorder,
            marginBottom: 28,
          }}
        />

        {/* Content Area */}
        {children}
      </div>
    </div>
  );
}
