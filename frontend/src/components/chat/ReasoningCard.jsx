import { T } from "../../styles/theme";

export default function ReasoningCard({ reasoning, expanded, onToggle }) {
  if (!reasoning) return null;

  return (
    <div style={{ marginTop: 10 }}>
      <button onClick={onToggle}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 6, padding: "6px 10px", background: `${T.accent}08`, border: `1px solid ${T.accent}22`, borderRadius: 8, color: T.accent, fontSize: 11, fontWeight: 600, cursor: "pointer", transition: "all 0.15s" }}>
        <span style={{ fontSize: 14 }}>🧠</span>
        <span>Reasoning</span>
        <span style={{ marginLeft: "auto", fontSize: 10 }}>{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div style={{ marginTop: 4, padding: "10px 12px", background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 8, display: "flex", flexDirection: "column", gap: 6, animation: "fadeIn 0.2s ease" }}>
          {reasoning.sources && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {reasoning.sources.map((source, i) => (
                <span key={i} style={{ padding: "2px 8px", borderRadius: 4, background: `${T.accent}11`, color: T.textSecondary, fontSize: 10, fontWeight: 500 }}>{source.icon} {source.label}</span>
              ))}
            </div>
          )}
          {reasoning.matches && reasoning.matches.length > 0 && (
            <div style={{ color: T.textMuted, fontSize: 11 }}>
              <div style={{ fontWeight: 600, color: T.textSecondary, marginBottom: 2 }}>CrimeAI matched:</div>
              {reasoning.matches.map((match, i) => (
                <div key={i} style={{ display: "flex", gap: 4, padding: "2px 0" }}>
                  <span style={{ color: T.accent }}>•</span>
                  <span>{match.count} {match.label}</span>
                </div>
              ))}
            </div>
          )}
          {reasoning.probability !== undefined && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: T.textMuted, fontSize: 11 }}>Probability</span>
              <span style={{ color: reasoning.probability >= 80 ? T.success : reasoning.probability >= 60 ? T.warning : T.accent, fontSize: 12, fontWeight: 700 }}>{reasoning.probability}%</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
