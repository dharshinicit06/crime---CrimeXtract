import { T } from "../../styles/theme";
import Badge from "../Badge";

export default function ChatHeader({
  user,
  onToggleSidebar,
  onToggleTools,
  showSidebar,
  showTools,
  currentCase,
  onExportPdf,
  hasMessages = false,
}) {
  const firstName = user?.name?.split(" ")[0] || "Officer";
  const userRole = user?.role || "Officer";

  return (
    <header
      style={{
        padding: "14px 20px",
        borderBottom: `1px solid ${T.cardBorder}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        background: T.card,
        borderRadius: "16px 16px 0 0",
        flexShrink: 0,
      }}
    >
      {/* Left: Toggle + Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button
          onClick={onToggleSidebar}
          title="Toggle history"
          style={{
            background: T.inputBg,
            border: `1px solid ${T.inputBorder}`,
            borderRadius: 8,
            color: T.textSecondary,
            cursor: "pointer",
            fontSize: 16,
            padding: "6px 8px",
            lineHeight: 1,
            transition: "all 0.15s",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          ☰
        </button>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            flexShrink: 0,
          }}
        >
          🕵
        </div>
        <div>
          <div style={{ color: T.textPrimary, fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>
            CrimeAI Investigation Assistant
          </div>
          <div style={{ color: T.textMuted, fontSize: 10 }}>
            Case-aware Intelligence Engine
          </div>
        </div>
      </div>

      {/* Center: Case Context */}
      {currentCase && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: T.inputBg,
            padding: "6px 12px",
            borderRadius: 8,
            border: `1px solid ${T.cardBorder}`,
            flex: "0 1 auto",
          }}
        >
          <span style={{ fontSize: 14 }}>📁</span>
          <div>
            <div style={{ color: T.textMuted, fontSize: 10 }}>Current Case</div>
            <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
              {currentCase}
            </div>
          </div>
        </div>
      )}

      {/* Right: Export PDF + User + Tools Toggle */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {/* Export PDF Button */}
        {onExportPdf && hasMessages && (
          <button
            onClick={onExportPdf}
            title="Export conversation as PDF"
            style={{
              background: T.inputBg,
              border: `1px solid ${T.inputBorder}`,
              borderRadius: 8,
              color: T.textSecondary,
              cursor: "pointer",
              fontSize: 13,
              padding: "6px 10px",
              lineHeight: 1,
              transition: "all 0.15s",
              display: "flex",
              alignItems: "center",
              gap: 5,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = T.accent + "44";
              e.currentTarget.style.color = T.accent;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = T.inputBorder;
              e.currentTarget.style.color = T.textSecondary;
            }}
          >
            <span>📄</span>
            <span style={{ fontSize: 11, fontWeight: 600 }}>PDF</span>
          </button>
        )}


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 10px",
            borderRadius: 8,
            background: T.inputBg,
            border: `1px solid ${T.cardBorder}`,
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: `linear-gradient(135deg, ${T.accent}44, ${T.purple}44)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 700,
              color: T.accent,
            }}
          >
            {firstName[0]}
          </div>
          <div>
            <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600, lineHeight: 1.2 }}>
              {user?.name || "Officer"}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: T.success,
                  display: "inline-block",
                }}
              />
              <span style={{ color: T.success, fontSize: 10 }}>Connected</span>
            </div>
          </div>
          <Badge label={userRole} />
        </div>

        <button
          onClick={onToggleTools}
          title="Toggle AI tools"
          style={{
            background: showTools ? T.accentGlow : T.inputBg,
            border: `1px solid ${showTools ? T.accent + "44" : T.inputBorder}`,
            borderRadius: 8,
            color: showTools ? T.accent : T.textSecondary,
            cursor: "pointer",
            fontSize: 16,
            padding: "6px 8px",
            lineHeight: 1,
            transition: "all 0.15s",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          🛠
        </button>
      </div>
    </header>
  );
}
