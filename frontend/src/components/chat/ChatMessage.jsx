import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { T } from "../../styles/theme";
import ConfidenceBadge from "./ConfidenceBadge";
import ReasoningCard from "./ReasoningCard";
import InvestigationTimeline from "./InvestigationTimeline";
import RecommendationCards from "./RecommendationCards";

const mdC = {
  h1: ({ children, ...p }) => (
    <h1 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: "12px 0 6px" }} {...p}>
      {children}
    </h1>
  ),
  h2: ({ children, ...p }) => (
    <h2 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: "10px 0 5px" }} {...p}>
      {children}
    </h2>
  ),
  h3: ({ children, ...p }) => (
    <h3 style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600, margin: "8px 0 4px" }} {...p}>
      {children}
    </h3>
  ),
  p: ({ children, ...p }) => (
    <p
      style={{ color: T.textSecondary, fontSize: 13, margin: "4px 0", lineHeight: 1.7 }}
      {...p}
    >
      {children}
    </p>
  ),
  strong: ({ children, ...p }) => (
    <strong style={{ color: T.textPrimary, fontWeight: 600 }} {...p}>
      {children}
    </strong>
  ),
  ul: ({ children, ...p }) => (
    <ul
      style={{ margin: "4px 0", paddingLeft: 20, color: T.textSecondary, fontSize: 13, lineHeight: 1.9 }}
      {...p}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...p }) => (
    <ol
      style={{ margin: "4px 0", paddingLeft: 20, color: T.textSecondary, fontSize: 13, lineHeight: 1.9 }}
      {...p}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...p }) => <li style={{ margin: "2px 0" }} {...p}>{children}</li>,
  code: ({ children, inline, ...p }) =>
    inline ? (
      <code
        style={{
          background: T.inputBg,
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 12,
          color: T.accent,
          fontFamily: "monospace",
        }}
        {...p}
      >
        {children}
      </code>
    ) : (
      <pre
        style={{
          background: T.inputBg,
          padding: 12,
          borderRadius: 8,
          overflow: "auto",
          fontSize: 12,
          border: `1px solid ${T.cardBorder}`,
        }}
      >
        <code style={{ color: T.textPrimary, fontFamily: "monospace" }}>{children}</code>
      </pre>
    ),
  table: ({ children, ...p }) => (
    <div style={{ overflowX: "auto", margin: "8px 0" }}>
      <table
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}
        {...p}
      >
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...p }) => (
    <th
      style={{
        border: `1px solid ${T.cardBorder}`,
        padding: "6px 10px",
        color: T.textPrimary,
        fontWeight: 600,
        background: T.inputBg,
        textAlign: "left",
      }}
      {...p}
    >
      {children}
    </th>
  ),
  td: ({ children, ...p }) => (
    <td
      style={{
        border: `1px solid ${T.cardBorder}`,
        padding: "6px 10px",
        color: T.textSecondary,
      }}
      {...p}
    >
      {children}
    </td>
  ),
};

export default function ChatMessage({
  message,
  userInitial,
  onCopy,
  onRegenerate,
  onFeedback,
  showActions = true,
}) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const isUser = message.role === "user";
  const timeStr = message.time
    ? new Date(message.time).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      })
    : "";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
    if (onCopy) onCopy(message.text);
  };

  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
        animation: "msgIn 0.3s ease",
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 10,
          flexShrink: 0,
          background: isUser
            ? `linear-gradient(135deg, ${T.accent}44, ${T.purple}44)`
            : `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: isUser ? 13 : 16,
          fontWeight: isUser ? 700 : 400,
          color: isUser ? T.accent : "#fff",
        }}
      >
        {isUser ? userInitial || "U" : "🕵"}
      </div>

      {/* Message Content */}
      <div
        style={{
          maxWidth: "80%",
          minWidth: 120,
        }}
      >
        {/* Role Label */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            marginBottom: 4,
            justifyContent: isUser ? "flex-end" : "flex-start",
          }}
        >
          <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
            {isUser ? "You" : "CrimeAI"}
          </span>
          {isUser ? null : (
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: T.success,
                display: "inline-block",
              }}
            />
          )}
          <span style={{ color: T.textMuted, fontSize: 10 }}>{timeStr}</span>
        </div>

        {/* Bubble */}
        <div
          style={{
            padding: "12px 16px",
            background: isUser ? `${T.accent}18` : T.inputBg,
            borderRadius: isUser ? "14px 4px 14px 14px" : "4px 14px 14px 14px",
            border: `1px solid ${isUser ? T.accent + "22" : T.cardBorder}`,
          }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdC}>
            {message.text}
          </ReactMarkdown>

          {/* Attachment card */}
          {message.attachment && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 12px",
                background: T.card,
                borderRadius: 8,
                border: `1px solid ${T.cardBorder}`,
                marginTop: 8,
              }}
            >
              <span style={{ fontSize: 20 }}>
                {message.attachment.mime?.startsWith("image/")
                  ? "🖼"
                  : message.attachment.mime?.includes("pdf")
                  ? "📄"
                  : "📎"}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    color: T.textPrimary,
                    fontSize: 12,
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {message.attachment.name}
                </div>
                <div style={{ color: T.textMuted, fontSize: 10 }}>
                  {message.attachment.size
                    ? `${(message.attachment.size / 1024).toFixed(1)} KB`
                    : ""}
                </div>
              </div>
            </div>
          )}

          {/* Confidence Badge */}
          {!isUser && message.confidence && <ConfidenceBadge score={message.confidence} />}

          {/* Reasoning Card */}
          {!isUser && message.reasoning && (
            <ReasoningCard
              reasoning={message.reasoning}
              expanded={showReasoning}
              onToggle={() => setShowReasoning(!showReasoning)}
            />
          )}

          {/* Investigation Cards */}
          {!isUser && message.cards?.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
              {message.cards.map((card, i) => (
                <div
                  key={i}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 8,
                    background: `${card.color || T.accent}11`,
                    border: `1px solid ${card.color || T.accent}33`,
                    fontSize: 11,
                    color: T.textPrimary,
                    fontWeight: 500,
                  }}
                >
                  {card.icon} {card.label}
                </div>
              ))}
            </div>
          )}

          {/* Prediction Dashboard Button */}
          {!isUser && message.showPredictionDashboard && (
            <div style={{ marginTop: 12 }}>
              <button
                onClick={() => navigate("/forecast")}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "10px 18px",
                  background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
                  color: "#fff",
                  border: "none",
                  borderRadius: 10,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  boxShadow: `0 4px 14px ${T.accent}44`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = `0 6px 20px ${T.accent}66`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.boxShadow = `0 4px 14px ${T.accent}44`;
                }}
              >
                <span>📊</span>
                Open Forecast Dashboard
                <span style={{ fontSize: 10, opacity: 0.8 }}>→</span>
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        {showActions && !isUser && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              marginTop: 4,
              justifyContent: "flex-start",
            }}
          >
            <ActionButton icon="📋" label={copied ? "Copied!" : "Copy"} onClick={handleCopy} />
            <ActionButton icon="🔄" label="Regenerate" onClick={() => onRegenerate?.()} />
            <ActionButton icon="👍" label="Helpful" onClick={() => onFeedback?.(5, message.messageId)} />
            <ActionButton icon="👎" label="Not helpful" onClick={() => onFeedback?.(1, message.messageId)} />
            {message.explanation?.evidence?.length > 0 && (
              <ActionButton
                icon="❓"
                label={showExplanation ? "Hide Why" : "Why?"}
                onClick={() => setShowExplanation(!showExplanation)}
                active={showExplanation}
              />
            )}
            {message.reasoning && (
              <ActionButton
                icon="🧠"
                label={showReasoning ? "Hide" : "Reasoning"}
                onClick={() => setShowReasoning(!showReasoning)}
                active={showReasoning}
              />
            )}
          </div>
        )}

        {/* Investigation Timeline */}
        {!isUser && message.timeline?.length > 0 && (
          <InvestigationTimeline events={message.timeline} />
        )}

        {/* Smart Recommendations */}
        {!isUser && message.recommendations?.length > 0 && (
          <RecommendationCards recommendations={message.recommendations} />
        )}

        {/* Explainable AI Panel */}
        {!isUser && showExplanation && message.explanation?.evidence?.length > 0 && (
          <div
            style={{
              marginTop: 8,
              padding: "12px 16px",
              background: `${T.accent}08`,
              border: `1px solid ${T.accent}22`,
              borderRadius: 10,
              animation: "fadeIn 0.2s ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 14 }}>❓</span>
              <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>Why?</span>
            </div>
            {message.explanation.answer && (
              <div style={{ color: T.accent, fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                {message.explanation.answer}
              </div>
            )}
            {message.explanation.explanation && (
              <div style={{ color: T.textSecondary, fontSize: 12, marginBottom: 8, lineHeight: 1.6 }}>
                {message.explanation.explanation}
              </div>
            )}
            <div style={{ borderTop: `1px solid ${T.accent}22`, paddingTop: 8, marginTop: 4 }}>
              <div style={{ color: T.textMuted, fontSize: 11, fontWeight: 500, marginBottom: 4 }}>
                Evidence from database:
              </div>
              {message.explanation.evidence.map((ev, i) => (
                <div
                  key={i}
                  style={{
                    color: T.textSecondary,
                    fontSize: 12,
                    padding: "3px 0",
                    lineHeight: 1.5,
                    display: "flex",
                    gap: 6,
                  }}
                >
                  <span style={{ color: T.accent, flexShrink: 0 }}>▸</span>
                  <span>{ev}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({ icon, label, onClick, active }) {
  return (
    <button
      onClick={onClick}
      title={label}
      style={{
        background: active ? T.accentGlow : "transparent",
        border: "none",
        color: active ? T.accent : T.textMuted,
        cursor: "pointer",
        fontSize: 11,
        padding: "3px 6px",
        borderRadius: 4,
        display: "flex",
        alignItems: "center",
        gap: 3,
        transition: "all 0.15s",
      }}
    >
      <span>{icon}</span>
    </button>
  );
}
