import { T } from "../../styles/theme";

export default function ConfidenceBadge({ score = 0 }) {
  const pct = Math.min(Math.max(score, 0), 100);
  const color = pct >= 80 ? T.success : pct >= 60 ? T.warning : pct >= 40 ? T.accent : T.danger;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10, padding: "8px 12px", background: `${color}08`, border: `1px solid ${color}22`, borderRadius: 8 }}>
      <span style={{ fontSize: 14 }}>🎯</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
          <span style={{ color: T.textSecondary, fontSize: 11 }}>AI Confidence</span>
          <span style={{ color, fontSize: 11, fontWeight: 700 }}>{pct}%</span>
        </div>
        <div style={{ height: 4, background: T.cardBorder, borderRadius: 2, overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
        </div>
      </div>
    </div>
  );
}
