"""Write frontend/src/styles/shared.js"""
import os

target = os.path.join("frontend", "src", "styles", "shared.js")

content = """/* Shared UI Utilities — standardized patterns across all pages */

import { useCallback, useEffect, useState } from "react";
import { T } from "./theme";

export const ANIM_STYLES = `
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
`;

export function Skeleton({ width = "100%", height = 16, borderRadius = 6, delay = 0 }) {
  return (
    <div
      style={{
        width, height, borderRadius,
        background: `linear-gradient(90deg, $` + `{T.card} 25%, $` + `{T.cardBorder} 50%, $` + `{T.card} 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s ease-in-out infinite",
        animationDelay: `$` + `{delay}s`,
      }}
    />
  );
}

export function TableSkeleton({ rows = 6, cols = 5 }) {
  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 16, alignItems: "center" }}>
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} height={14} delay={i * 0.05 + j * 0.05} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ count = 4 }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ background: T.card, border: `1px solid $` + `{T.cardBorder}`, borderRadius: 16, padding: 24 }}>
          <Skeleton width="60%" height={14} delay={i * 0.1} />
          <div style={{ marginTop: 12 }}><Skeleton width="40%" height={28} delay={i * 0.15} /></div>
          <div style={{ marginTop: 8 }}><Skeleton width="80%" height={12} delay={i * 0.2} /></div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ icon = "\ud83d\udced", title, message, action }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 20px", textAlign: "center", animation: "fadeIn 0.3s ease" }}>
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.6 }}>{icon}</div>
      {title && <h3 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: "0 0 6px" }}>{title}</h3>}
      <p style={{ color: T.textMuted, fontSize: 13, margin: "0 0 16px", maxWidth: 360, lineHeight: 1.5 }}>{message || "No data available"}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message = "Something went wrong", onRetry }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 20px", textAlign: "center", animation: "fadeIn 0.3s ease" }}>
      <span style={{ fontSize: 40, marginBottom: 12 }}>\u26a0\ufe0f</span>
      <p style={{ color: T.danger, fontSize: 14, margin: "0 0 4px", fontWeight: 500 }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} style={{ marginTop: 12, padding: "8px 20px", borderRadius: 8, border: `1px solid $` + `{T.cardBorder}`, background: T.inputBg, color: T.accent, fontSize: 13, cursor: "pointer" }}>
          Retry
        </button>
      )}
    </div>
  );
}

export function useToast() {
  const [toast, setToast] = useState(null);
  const showToast = useCallback((message, type = "success") => setToast({ message, type }), []);
  const hideToast = useCallback(() => setToast(null), []);
  useEffect(() => { if (toast) { const t = setTimeout(hideToast, 3500); return () => clearTimeout(t); } }, [toast, hideToast]);
  return { toast, showToast, hideToast };
}

export function Toast({ toast, onClose }) {
  if (!toast) return null;
  const bg = toast.type === "success" ? T.success : toast.type === "warning" ? T.warning : T.danger;
  const icon = toast.type === "success" ? "\u2705" : toast.type === "warning" ? "\u26a0\ufe0f" : "\u274c";
  return (
    <div style={{ position: "fixed", top: 20, right: 20, zIndex: 2000, padding: "12px 20px", borderRadius: 10, background: bg, color: "#fff", fontSize: 13, fontWeight: 600, boxShadow: `0 4px 20px $` + `{bg}66`, animation: "slideDown 0.25s ease", display: "flex", alignItems: "center", gap: 8, cursor: "pointer", maxWidth: 400 }}
      onClick={onClose}>
      <span>{icon}</span>
      <span style={{ flex: 1 }}>{toast.message}</span>
    </div>
  );
}

export function Pagination({ page, totalPages, total, onChange }) {
  if (totalPages <= 1 && !total) return null;
  const pages = [];
  for (let i = 1; i <= totalPages; i++) pages.push(i);
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderTop: `1px solid $` + `{T.cardBorder}`, flexWrap: "wrap", gap: 8 }}>
      {total !== undefined && <span style={{ color: T.textMuted, fontSize: 12 }}>{total} total</span>}
      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}
          style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid $` + `{T.cardBorder}`, background: T.inputBg, color: page <= 1 ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page <= 1 ? "default" : "pointer", opacity: page <= 1 ? 0.5 : 1 }}>
          \u2190 Prev
        </button>
        {pages.map((p) => (
          <button key={p} onClick={() => onChange(p)}
            style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: p === page ? T.accent : "transparent", color: p === page ? "#fff" : T.textSecondary, fontSize: 12, cursor: "pointer", fontWeight: p === page ? 600 : 400, minWidth: 28 }}>
            {p}
          </button>
        ))}
        <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}
          style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid $` + `{T.cardBorder}`, background: T.inputBg, color: page >= totalPages ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page >= totalPages ? "default" : "pointer", opacity: page >= totalPages ? 0.5 : 1 }}>
          Next \u2192
        </button>
      </div>
    </div>
  );
}

export const MODAL_STYLES = {
  overlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: 20, backdropFilter: "blur(4px)" },
  content: { background: T.card, border: `1px solid $` + `{T.cardBorder}`, borderRadius: 16, width: "100%", maxWidth: 520, maxHeight: "90vh", overflow: "auto", animation: "scaleIn 0.2s ease" },
  input: { width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid $` + `{T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box" },
  label: { display: "block", color: T.textSecondary, fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" },
  select: { width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid $` + `{T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none", cursor: "pointer", boxSizing: "border-box" },
};

export const FIELD_STYLES = {
  group: { marginBottom: 16 },
  label: { display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 },
  row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 },
  error: { color: T.danger, fontSize: 12, margin: "4px 0 0" },
};

export function PageHeader({ title, subtitle, action }) {
  return (
    <div style={{ marginBottom: 24, animation: "fadeIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>{title}</h1>
          {subtitle && <p style={{ color: T.textMuted, fontSize: 13, margin: 0 }}>{subtitle}</p>}
        </div>
        {action}
      </div>
    </div>
  );
}

export const STATUS_COLORS = {
  Open: { bg: "rgba(239,68,68,0.15)", color: "#ef4444" },
  "Under Investigation": { bg: "rgba(245,158,11,0.15)", color: "#f59e0b" },
  Closed: { bg: "rgba(34,197,94,0.15)", color: "#22c55e" },
  Solved: { bg: "rgba(34,197,94,0.15)", color: "#22c55e" },
  Pending: { bg: "rgba(148,163,184,0.15)", color: "#94a3b8" },
  High: { bg: "rgba(239,68,68,0.15)", color: "#ef4444" },
  Medium: { bg: "rgba(245,158,11,0.15)", color: "#f59e0b" },
  Low: { bg: "rgba(34,197,94,0.15)", color: "#22c55e" },
  Critical: { bg: "rgba(239,68,68,0.15)", color: "#ef4444" },
};
"""

with open(target, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Written {os.path.getsize(target)} bytes to {target}")
