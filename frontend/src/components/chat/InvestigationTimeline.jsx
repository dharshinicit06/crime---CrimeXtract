import { useState } from "react";
import { T } from "../../styles/theme";

const ICON_MAP = {
  clipboard: "📋",
  document: "📄",
  search: "🔍",
  person: "👤",
  microscope: "🔬",
  warning: "🚨",
  money: "💰",
  link: "🔗",
  shield: "👮",
  check: "✅",
  locked: "📌",
  chart: "📊",
  file: "📝",
  refresh: "🔄",
  flame: "🔥",
  circle: "⚪",
};

const STATUS_COLORS = {
  completed: T.success,
  pending: T.warning,
  cancelled: T.danger,
};

function TimelineIcon({ icon }) {
  return (
    <span style={{ fontSize: 16, flexShrink: 0, width: 28, textAlign: "center" }}>
      {ICON_MAP[icon] || "⚪"}
    </span>
  );
}

export default function InvestigationTimeline({ events = [], title = "Investigation Timeline" }) {
  const [expanded, setExpanded] = useState(false);
  const displayEvents = expanded ? events : events.slice(0, 5);
  const hasMore = events.length > 5;

  if (!events || events.length === 0) return null;

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
        <span style={{ fontSize: 14 }}>📅</span>
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
          {events.length} event{events.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Timeline */}
      <div style={{ position: "relative", paddingLeft: 8 }}>
        {displayEvents.map((event, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              gap: 10,
              paddingBottom: i < displayEvents.length - 1 ? 16 : 0,
              position: "relative",
            }}
          >
            {/* Timeline line */}
            {i < displayEvents.length - 1 && (
              <div
                style={{
                  position: "absolute",
                  left: 15,
                  top: 22,
                  bottom: -2,
                  width: 2,
                  background: `${STATUS_COLORS[event.status] || T.textMuted}33`,
                }}
              />
            )}

            {/* Icon circle */}
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: `${STATUS_COLORS[event.status] || T.textMuted}18`,
                border: `2px solid ${STATUS_COLORS[event.status] || T.textMuted}44`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                zIndex: 1,
              }}
            >
              <TimelineIcon icon={event.icon} />
            </div>

            {/* Content */}
            <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
                  {event.event}
                </span>
                {event.date && (
                  <span
                    style={{
                      color: T.textMuted,
                      fontSize: 10,
                      background: T.inputBg,
                      padding: "1px 6px",
                      borderRadius: 4,
                    }}
                  >
                    {new Date(event.date).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                )}
              </div>
              <div
                style={{
                  color: T.textSecondary,
                  fontSize: 11,
                  marginTop: 2,
                  lineHeight: 1.5,
                }}
              >
                {event.description}
              </div>
            </div>
          </div>
        ))}

        {/* Show more / less */}
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: "none",
              border: "none",
              color: T.accent,
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              padding: "6px 0 0 42px",
              fontFamily: "inherit",
            }}
          >
            {expanded ? `Show less ▲` : `Show ${events.length - 5} more ▼`}
          </button>
        )}
      </div>
    </div>
  );
}
