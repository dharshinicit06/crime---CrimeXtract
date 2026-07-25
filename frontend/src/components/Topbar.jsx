import { T } from "../styles/theme";
import { useDemoMode } from "../context/DemoModeContext";

export default function Topbar({ title, user }) {
  const { isDemoMode, toggleDemoMode } = useDemoMode();

  return (
    <header
      style={{
        height: 60,
        background: T.surface,
        borderBottom: `1px solid ${T.cardBorder}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        position: "sticky",
        top: 0,
        zIndex: 50,
        width: "100%",
      }}
    >
      <div style={{ flexShrink: 0 }}>
        <div style={{ color: T.textPrimary, fontWeight: 700, fontSize: 18 }}>
          {title}
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1, justifyContent: "flex-end", marginLeft: 16 }}>
        <div
          style={{
            background: T.inputBg,
            border: `1px solid ${T.inputBorder}`,
            borderRadius: 20,
            padding: "6px 14px",
            display: "flex",
            alignItems: "center",
            gap: 8,
            flex: "0 1 320px",
            maxWidth: 400,
          }}
        >
          <span style={{ fontSize: 14, flexShrink: 0 }}>🔍</span>
          <input
            placeholder="Search records…"
            style={{
              background: "none",
              border: "none",
              outline: "none",
              color: T.textPrimary,
              fontSize: 13,
              width: "100%",
            }}
          />
        </div>

        {/* Demo Mode Toggle */}
        <button
          onClick={toggleDemoMode}
          title={isDemoMode ? "Switch to Production" : "Switch to Demo"}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: isDemoMode
              ? "linear-gradient(135deg, #5B7FFF, #7C5CFF)"
              : T.inputBg,
            border: `1px solid ${isDemoMode ? "transparent" : T.inputBorder}`,
            borderRadius: 20,
            padding: "6px 14px",
            cursor: "pointer",
            color: isDemoMode ? "#fff" : T.textMuted,
            fontSize: 12,
            fontWeight: 600,
            transition: "all 0.2s",
          }}
        >
          <span>{isDemoMode ? "🧪" : "🔬"}</span>
          <span>{isDemoMode ? "Demo ON" : "Demo"}</span>
        </button>

        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            background: `linear-gradient(135deg, ${T.accent}44, ${T.purple}44)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: T.accent,
            fontWeight: 700,
            fontSize: 14,
            flexShrink: 0,
          }}
        >
          {user?.name?.[0]}
        </div>
      </div>
    </header>
  );
}
