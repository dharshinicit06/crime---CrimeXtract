import { T } from "../../styles/theme";

const SUGGESTIONS = [
  { icon: "🔍", label: "Find suspects near MG Road" },
  { icon: "📋", label: "Summarize FIR 2026-134" },
  { icon: "👤", label: "Generate offender profile" },
  { icon: "🔗", label: "Find similar crimes" },
  { icon: "📍", label: "Crime hotspot this week" },
  { icon: "📅", label: "Timeline reconstruction" },
  { icon: "🚗", label: "Vehicle search" },
  { icon: "👥", label: "Missing person analysis" },
];

export default function PromptSuggestions({ onSelect, visible }) {
  if (!visible) return null;

  return (
    <div style={{ padding: "16px 20px", textAlign: "center", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 16, animation: "fadeIn 0.5s ease" }}>
      <div style={{ width: 80, height: 80, borderRadius: 20, background: `linear-gradient(135deg, ${T.accent}22, ${T.purple}22)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36, marginBottom: 4 }}>🕵️‍♂️</div>
      <div>
        <h2 style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>Start a New Investigation</h2>
        <p style={{ color: T.textMuted, fontSize: 13, margin: 0, maxWidth: 400 }}>Ask CrimeAI anything about cases, FIRs, offenders, victims, evidence, locations, or criminal networks</p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8, maxWidth: 500, width: "100%" }}>
        {SUGGESTIONS.map((s, i) => (
          <button key={i} onClick={() => onSelect(s.label)}
            style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: 10, background: T.card, border: `1px solid ${T.cardBorder}`, color: T.textSecondary, fontSize: 12, cursor: "pointer", transition: "all 0.2s", textAlign: "left" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = T.accent + "44"; e.currentTarget.style.background = T.accentGlow; e.currentTarget.style.color = T.accent; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.cardBorder; e.currentTarget.style.background = T.card; e.currentTarget.style.color = T.textSecondary; }}
          >
            <span style={{ fontSize: 14, flexShrink: 0 }}>{s.icon}</span>
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
