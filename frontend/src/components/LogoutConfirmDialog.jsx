import { useState } from "react";
import { T } from "../styles/theme";
import Button from "./Button";

export default function LogoutConfirmDialog({ open, onCancel, onConfirm }) {
  const [confirmHover, setConfirmHover] = useState(false);

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.6)",
        backdropFilter: "blur(4px)",
      }}
      onClick={onCancel}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: T.card,
          border: `1px solid ${T.cardBorder}`,
          borderRadius: 16,
          padding: 28,
          width: 360,
          maxWidth: "90vw",
          boxShadow: "0 25px 50px rgba(0,0,0,0.4)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: "rgba(239,68,68,0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              fontSize: 24,
            }}
          >
            🚪
          </div>
          <h3
            style={{
              color: T.textPrimary,
              fontSize: 17,
              fontWeight: 700,
              margin: "0 0 6px",
            }}
          >
            Sign out
          </h3>
          <p
            style={{
              color: T.textSecondary,
              fontSize: 13,
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            Are you sure you want to sign out? You'll need to log in again to
            access the platform.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <Button
            variant="secondary"
            onClick={onCancel}
            style={{ flex: 1, justifyContent: "center" }}
          >
            Cancel
          </Button>
          <button
            onClick={onConfirm}
            onMouseEnter={() => setConfirmHover(true)}
            onMouseLeave={() => setConfirmHover(false)}
            style={{
              flex: 1,
              padding: "10px 20px",
              borderRadius: 10,
              border: "none",
              background: confirmHover ? "#dc2626" : T.danger,
              color: "#fff",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.2s",
              transform: confirmHover ? "translateY(-1px)" : "none",
              boxShadow: confirmHover
                ? "0 4px 12px rgba(239,68,68,0.4)"
                : "none",
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
