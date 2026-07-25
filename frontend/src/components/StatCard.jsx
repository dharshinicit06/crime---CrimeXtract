import { T } from "../styles/theme";

export default function StatCard({ icon, label, value, sub, color = T.accent }) {
  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: "20px 24px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        flex: 1,
        minWidth: 160,
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: `${color}22`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: T.textPrimary,
            lineHeight: 1,
          }}
        >
          {value}
        </div>
        <div style={{ fontSize: 12, color: T.textSecondary, marginTop: 4 }}>
          {label}
        </div>
        {sub && (
          <div style={{ fontSize: 11, color, marginTop: 2 }}>{sub}</div>
        )}
      </div>
    </div>
  );
}
