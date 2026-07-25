import { T } from "../../styles/theme";

const TOOLS = [
  { icon: "📋", label: "Summarize Case", action: "summarize" },
  { icon: "📅", label: "Generate Timeline", action: "timeline" },
  { icon: "👤", label: "Criminal Profile", action: "profile" },
  { icon: "🔗", label: "Find Similar FIR", action: "similar" },
  { icon: "🔬", label: "Evidence Correlation", action: "evidence" },
  { icon: "🕸", label: "Network Analysis", action: "network" },
  { icon: "📍", label: "Crime Heatmap", action: "heatmap" },
  { icon: "📈", label: "Predict Next Crime", action: "predict" },
  { icon: "📄", label: "Export Report", action: "export" },
];

export default function ToolPanel({ onToolSelect, currentCase }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%", overflow: "hidden" }}>
      {/* Investigation Context */}
      {currentCase && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 14 }}>
          <h4 style={{ color: T.textMuted, fontWeight: 600, margin: "0 0 8px", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>Current Investigation</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <ContextRow label="Case" value={currentCase.id || "—"} />
            <ContextRow label="Officer" value={currentCase.officer || "—"} />
            <ContextRow label="District" value={currentCase.district || "—"} />
            <ContextRow label="Priority" value={currentCase.priority || "—"} color={currentCase.priority === "High" ? T.danger : T.textSecondary} />
            <ContextRow label="Status" value={currentCase.status || "—"} color={currentCase.status === "Open" ? T.warning : T.success} />
          </div>
        </div>
      )}

      {/* Investigation Tools */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 14, flex: 1, overflowY: "auto" }}>
        <h4 style={{ color: T.textMuted, fontWeight: 600, margin: "0 0 8px", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>Investigation Tools</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {TOOLS.map((tool, i) => (
            <button key={i} onClick={() => onToolSelect(tool)}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 8px", borderRadius: 7, background: "transparent", border: "none", color: T.textSecondary, fontSize: 12, cursor: "pointer", transition: "all 0.15s", textAlign: "left", width: "100%" }}
              onMouseEnter={(e) => { e.currentTarget.style.background = T.accentGlow; e.currentTarget.style.color = T.accent; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = T.textSecondary; }}
            >
              <span style={{ fontSize: 14, flexShrink: 0 }}>{tool.icon}</span>
              {tool.label}
            </button>
          ))}
        </div>
      </div>

      {/* Memory / Status */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 14 }}>
        <h4 style={{ color: T.textMuted, fontWeight: 600, margin: "0 0 6px", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>System Status</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: T.textMuted, fontSize: 11 }}>AI Model</span>
            <span style={{ color: T.success, fontSize: 11, fontWeight: 600 }}>Online</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: T.textMuted, fontSize: 11 }}>Database</span>
            <span style={{ color: T.success, fontSize: 11, fontWeight: 600 }}>Connected</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: T.textMuted, fontSize: 11 }}>Memory</span>
            <span style={{ color: T.textSecondary, fontSize: 11 }}>Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ContextRow({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <span style={{ color: T.textMuted, fontSize: 11 }}>{label}</span>
      <span style={{ color: color || T.textPrimary, fontSize: 11, fontWeight: 600 }}>{value}</span>
    </div>
  );
}
