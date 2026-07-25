import { useState, useMemo } from "react";
import { T } from "../../styles/theme";

function timeGroup(dateStr) {
  if (!dateStr) return "Older";
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now - d;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return "This Week";
  if (diffDays < 30) return "This Month";
  return "Older";
}

const GROUP_ORDER = ["Today", "Yesterday", "This Week", "This Month", "Older"];

export default function ChatHistory({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onRename,
  onNew,
  searchQuery,
  onSearchChange,
  loading,
}) {
  const [collapsedGroups, setCollapsedGroups] = useState({});
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState("");

  const grouped = useMemo(() => {
    const groups = {};
    conversations.forEach((c) => {
      const g = timeGroup(c.updated_at || c.created_at);
      if (!groups[g]) groups[g] = [];
      groups[g].push(c);
    });
    return groups;
  }, [conversations]);

  const toggleGroup = (group) => {
    setCollapsedGroups((prev) => ({ ...prev, [group]: !prev[group] }));
  };

  const startRename = (c) => {
    setRenamingId(c.id);
    setRenameValue(c.title);
  };

  const confirmRename = (c) => {
    if (renameValue.trim() && onRename) onRename(c.id, renameValue.trim());
    setRenamingId(null);
  };

  return (
    <div
      style={{
        background: T.card,
        border: `1px solid ${T.cardBorder}`,
        borderRadius: 16,
        padding: 12,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
        }}
      >
        <h4
          style={{
            color: T.textPrimary,
            fontSize: 13,
            fontWeight: 600,
            margin: 0,
          }}
        >
          Investigations
        </h4>
        <span
          style={{
            color: T.textMuted,
            fontSize: 10,
            background: T.inputBg,
            padding: "2px 6px",
            borderRadius: 4,
          }}
        >
          {conversations.length}
        </span>
      </div>

      {/* Search */}
      <div style={{ position: "relative", marginBottom: 10 }}>
        <span
          style={{
            position: "absolute",
            left: 8,
            top: "50%",
            transform: "translateY(-50%)",
            fontSize: 12,
            color: T.textMuted,
            pointerEvents: "none",
          }}
        >
          🔍
        </span>
        <input
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search investigations..."
          style={{
            width: "100%",
            padding: "7px 8px 7px 28px",
            background: T.inputBg,
            border: `1px solid ${T.inputBorder}`,
            borderRadius: 8,
            color: T.textPrimary,
            fontSize: 11,
            outline: "none",
            boxSizing: "border-box",
          }}
        />
      </div>

      {/* New Chat Button */}
      <button
        onClick={onNew}
        style={{
          width: "100%",
          padding: "7px 12px",
          borderRadius: 8,
          background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
          border: "none",
          color: "#fff",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          marginBottom: 10,
          transition: "opacity 0.15s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.9")}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
      >
        + New Investigation
      </button>

      {/* Conversation List */}
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 0 }}>
        {loading ? (
          <div style={{ padding: 20, textAlign: "center" }}>
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                style={{
                  height: 14,
                  background: T.inputBg,
                  borderRadius: 4,
                  marginBottom: 10,
                  animation: "shimmer 1.5s ease-in-out infinite",
                  backgroundImage: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`,
                  backgroundSize: "200% 100%",
                }}
              />
            ))}
          </div>
        ) : Object.keys(grouped).length === 0 ? (
          <div
            style={{
              padding: 20,
              textAlign: "center",
              color: T.textMuted,
              fontSize: 12,
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 8 }}>📭</div>
            No conversations yet
          </div>
        ) : (
          GROUP_ORDER.filter((g) => grouped[g]).map((group) => (
            <div key={group}>
              <div
                onClick={() => toggleGroup(group)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  padding: "6px 4px",
                  cursor: "pointer",
                  color: T.textMuted,
                  fontSize: 10,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                <span style={{ fontSize: 8 }}>{collapsedGroups[group] ? "▶" : "▼"}</span>
                {group}
                <span style={{ marginLeft: "auto" }}>{grouped[group].length}</span>
              </div>
              {!collapsedGroups[group] &&
                grouped[group].map((c) => {
                  const isActive = String(c.id) === String(activeId);
                  return (
                    <div
                      key={c.id}
                      onClick={() => onSelect(c.id)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "7px 8px",
                        borderRadius: 8,
                        cursor: "pointer",
                        background: isActive ? T.accentGlow : "transparent",
                        borderLeft: isActive ? `2px solid ${T.accent}` : "2px solid transparent",
                        transition: "all 0.15s",
                        marginBottom: 2,
                      }}
                    >
                      <span style={{ fontSize: 14 }}>💬</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        {renamingId === c.id ? (
                          <input
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onBlur={() => confirmRename(c)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") confirmRename(c);
                              if (e.key === "Escape") setRenamingId(null);
                            }}
                            autoFocus
                            style={{
                              width: "100%",
                              padding: "2px 4px",
                              background: T.inputBg,
                              border: `1px solid ${T.accent}`,
                              borderRadius: 4,
                              color: T.textPrimary,
                              fontSize: 11,
                              outline: "none",
                              boxSizing: "border-box",
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <div
                            style={{
                              color: isActive ? T.accent : T.textSecondary,
                              fontSize: 11,
                              fontWeight: isActive ? 600 : 400,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {c.title}
                          </div>
                        )}
                        <div style={{ color: T.textMuted, fontSize: 9, marginTop: 1 }}>
                          {c.message_count || 0} messages
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 1, flexShrink: 0 }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startRename(c);
                          }}
                          title="Rename"
                          style={{
                            background: "none",
                            border: "none",
                            color: T.textMuted,
                            cursor: "pointer",
                            fontSize: 10,
                            padding: 2,
                            opacity: 0,
                            transition: "opacity 0.15s",
                          }}
                        >
                          ✏️
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onDelete) onDelete(c.id);
                          }}
                          title="Delete"
                          style={{
                            background: "none",
                            border: "none",
                            color: T.textMuted,
                            cursor: "pointer",
                            fontSize: 10,
                            padding: 2,
                            opacity: 0,
                            transition: "opacity 0.15s",
                          }}
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  );
                })}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
