import { T } from "../../styles/theme";

const FEATURES = [
  { icon: "🤖", label: "AI Investigation", desc: "LLM-powered case analysis" },
  { icon: "🕸", label: "Network Analysis", desc: "Criminal link mapping" },
  { icon: "📊", label: "Crime Prediction", desc: "Predictive policing models" },
  { icon: "🕵️", label: "Offender Profiling", desc: "Behavioral pattern analysis" },
  { icon: "🔬", label: "Evidence Intelligence", desc: "Cross-reference evidence" },
  { icon: "📈", label: "Analytics Dashboard", desc: "Real-time crime metrics" },
];

function FeatureCard({ icon, label, desc }) {
  return (
    <div
      tabIndex={0}
      role="listitem"
      aria-label={`${label}: ${desc}`}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 12px",
        borderRadius: 10,
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.05)",
        transition: "all 0.2s ease",
        cursor: "default",
        outline: "none",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(91,127,255,0.06)";
        e.currentTarget.style.borderColor = "rgba(91,127,255,0.15)";
        e.currentTarget.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.03)";
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.05)";
        e.currentTarget.style.transform = "none";
      }}
      onFocus={(e) => {
        e.currentTarget.style.background = "rgba(91,127,255,0.06)";
        e.currentTarget.style.borderColor = "rgba(91,127,255,0.25)";
        e.currentTarget.style.boxShadow = "0 0 0 2px rgba(91,127,255,0.2)";
      }}
      onBlur={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.03)";
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.05)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <span style={{ fontSize: 16, flexShrink: 0 }} aria-hidden="true">{icon}</span>
      <div>
        <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
          {label}
        </div>
        <div style={{ color: T.textMuted, fontSize: 10.5, marginTop: 1 }}>
          {desc}
        </div>
      </div>
    </div>
  );
}

export default function AuthFeatures() {
  return (
    <div
      role="list"
      aria-label="Platform features"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: 10,
        marginTop: 32,
      }}
    >
      {FEATURES.map((f) => (
        <FeatureCard key={f.label} {...f} />
      ))}
    </div>
  );
}
