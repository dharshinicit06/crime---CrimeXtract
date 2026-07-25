import { useState, useEffect } from "react";
import { T } from "../../styles/theme";

const STAGES = [
  { text: "CrimeAI is thinking...", dots: 80 },
  { text: "Searching FIR Database...", dots: 60 },
  { text: "Searching Criminal Network...", dots: 45 },
  { text: "Analyzing Evidence...", dots: 30 },
  { text: "Generating Timeline...", dots: 15 },
];

export default function TypingIndicator({ loading }) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!loading) { setStage(0); return; }
    const interval = setInterval(() => {
      setStage((prev) => Math.min(prev + 1, STAGES.length - 1));
    }, 2000);
    return () => clearInterval(interval);
  }, [loading]);

  if (!loading) return null;

  const current = STAGES[Math.min(stage, STAGES.length - 1)];

  return (
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start", animation: "fadeIn 0.3s ease" }}>
      <div style={{ width: 32, height: 32, borderRadius: 10, background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 }}>🕵</div>
      <div style={{ padding: "12px 16px", background: T.inputBg, borderRadius: "4px 14px 14px 14px", border: `1px solid ${T.cardBorder}`, minWidth: 200 }}>
        <div style={{ display: "flex", gap: 3, marginBottom: 6 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: T.accent, animation: "bounce 1.4s ease-in-out infinite", animationDelay: `${i * 0.2}s` }} />
          ))}
        </div>
        <div style={{ color: T.textMuted, fontSize: 11 }}>{current.text}</div>
        <div style={{ marginTop: 6, height: 2, background: T.cardBorder, borderRadius: 1, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${current.dots}%`, background: `linear-gradient(90deg, ${T.accent}, ${T.purple})`, borderRadius: 1, transition: "width 1s ease" }} />
        </div>
      </div>
    </div>
  );
}
