import { T } from "../../styles/theme";

const PRIORITY_COLORS = {
  high: { bg: "#FF4444", label: "High" },
  medium: { bg: "#FF9F43", label: "Medium" },
  standard: { bg: T.textMuted, label: "Standard" },
};

export default function RecommendationCards({ recommendations = [], title = "Investigation Recommendations" }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div
      style={{
        marginTop: 12,
        padding: "12px 16px",
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 12,
        animation: "fadeIn 0.3s ease",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 14 }}>💡</span>
        <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{title}</span>
        <span
          style={{
            marginLeft: "auto",
            color: T.textMuted,
            fontSize: 11,
            background: T.inputBg,
            padding: "2px 8px",
            borderRadius: 10,
          }}
        >
          {recommendations.length} suggestion{recommendations.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {recommendations.map((rec, i) => {
          const priorityInfo = PRIORITY_COLORS[rec.priority] || PRIORITY_COLORS.standard;
          return (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 10,
                padding: "10px 12px",
                background: T.inputBg,
                borderRadius: 8,
                border: `1px solid ${T.cardBorder}`,
                transition: "all 0.2s",
                cursor: "default",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = `${priorityInfo.bg}44`;
                e.currentTarget.style.background = `${priorityInfo.bg}08`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = T.cardBorder;
                e.currentTarget.style.background = T.inputBg;
              }}
            >
              {/* Icon */}
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: `${priorityInfo.bg}15`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  fontSize: 14,
                }}
              >
                {rec.icon || "💡"}
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                  <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
                    {rec.action}
                  </span>
                  <span
                    style={{
                      fontSize: 9,
                      fontWeight: 600,
                      color: "#fff",
                      background: priorityInfo.bg,
                      padding: "1px 6px",
                      borderRadius: 4,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    {priorityInfo.label}
                  </span>
                </div>
                <div
                  style={{
                    color: T.textMuted,
                    fontSize: 11,
                    marginTop: 3,
                    lineHeight: 1.5,
                  }}
                >
                  {rec.reason}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
