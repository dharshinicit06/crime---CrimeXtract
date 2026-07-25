import { useState } from "react";
import { T } from "../../styles/theme";

export default function ExportMenu({ messages, onExport }) {
  const [open, setOpen] = useState(false);

  const handleExport = (format) => {
    if (onExport) onExport(format, messages);
    setOpen(false);
  };

  return (
    <div style={{ position: "relative" }}>
      <button onClick={() => setOpen(!open)}
        style={{ background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 8, color: T.textSecondary, cursor: "pointer", fontSize: 12, padding: "6px 10px", transition: "all 0.15s" }}>
        📥 Export
      </button>
      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 99 }} />
          <div style={{ position: "absolute", top: "100%", right: 0, marginTop: 4, background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 10, overflow: "hidden", zIndex: 100, minWidth: 140, boxShadow: `0 8px 24px rgba(0,0,0,0.3)` }}>
            {[
              { label: "Markdown (.md)", format: "md" },
              { label: "Plain Text (.txt)", format: "txt" },
              { label: "JSON (.json)", format: "json" },
            ].map((opt, i) => (
              <button key={i} onClick={() => handleExport(opt.format)}
                style={{ display: "block", width: "100%", padding: "8px 14px", background: "transparent", border: "none", color: T.textSecondary, fontSize: 12, cursor: "pointer", textAlign: "left" }}
                onMouseEnter={(e) => e.currentTarget.style.background = T.accentGlow}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
