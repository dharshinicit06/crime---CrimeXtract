/* Shared UI Utilities — standardized patterns across all pages */

import { useCallback, useEffect, useState } from "react";
import { T } from "./theme";

/* ── Global Animation Keyframes ───────────────────────────── */
export const ANIM_STYLES = `
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
`;

/* ── Skeleton Loader ──────────────────────────────────────── */
export function Skeleton({ width = "100%", height = 16, borderRadius = 6, delay = 0 }) {
  return (
    <div
      style={{
        width, height, borderRadius,
        background: `linear-gradient(90deg, ${T.card} 25%, ${T.cardBorder} 50%, ${T.card} 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s ease-in-out infinite",
        animationDelay: `${delay}s`,
      }}
    />
  );
}

/* ── Empty State ──────────────────────────────────────────── */
export function EmptyState({ icon, title, message, action }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      padding: "60px 20px", textAlign: "center", animation: "fadeIn 0.3s ease",
    }}>
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.6 }}>{icon || String.fromCodePoint(0x1F4ED)}</div>
      {title && <h3 style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600, margin: "0 0 6px" }}>{title}</h3>}
      <p style={{ color: T.textMuted, fontSize: 13, margin: "0 0 16px", maxWidth: 360, lineHeight: 1.5 }}>
        {message || "No data available"}
      </p>
      {action}
    </div>
  );
}

/* ── Error State ──────────────────────────────────────────── */
export function ErrorState({ message = "Something went wrong", onRetry }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      padding: "60px 20px", textAlign: "center", animation: "fadeIn 0.3s ease",
    }}>
      <span style={{ fontSize: 40, marginBottom: 12 }} role="img" aria-label="warning">&#x26A0;&#xFE0F;</span>
      <p style={{ color: T.danger, fontSize: 14, margin: "0 0 4px", fontWeight: 500 }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} style={{
          marginTop: 12, padding: "8px 20px", borderRadius: 8,
          border: `1px solid ${T.cardBorder}`, background: T.inputBg,
          color: T.accent, fontSize: 13, cursor: "pointer",
        }}>
          Retry
        </button>
      )}
    </div>
  );
}

/* ── Toast Hook ───────────────────────────────────────────── */
export function useToast() {
  const [toast, setToast] = useState(null);
  const showToast = useCallback((message, type = "success") => setToast({ message, type }), []);
  const hideToast = useCallback(() => setToast(null), []);
  useEffect(() => { if (toast) { const t = setTimeout(hideToast, 3500); return () => clearTimeout(t); } }, [toast, hideToast]);
  return { toast, showToast, hideToast };
}

/* ── Toast Component ──────────────────────────────────────── */
export function Toast({ toast, onClose }) {
  if (!toast) return null;
  const bg = toast.type === "success" ? T.success : toast.type === "warning" ? T.warning : T.danger;
  return (
    <div onClick={onClose} style={{
      position: "fixed", top: 20, right: 20, zIndex: 2000,
      padding: "12px 20px", borderRadius: 10, background: bg,
      color: "#fff", fontSize: 13, fontWeight: 600,
      boxShadow: `0 4px 20px ${bg}66`,
      animation: "slideDown 0.25s ease",
      display: "flex", alignItems: "center", gap: 8,
      cursor: "pointer", maxWidth: 400,
    }}>
      <span>{toast.type === "success" ? String.fromCodePoint(0x2705) : toast.type === "warning" ? String.fromCodePoint(0x26A0, 0xFE0F) : String.fromCodePoint(0x274C)}</span>
      <span style={{ flex: 1 }}>{toast.message}</span>
    </div>
  );
}

/* ── Pagination ───────────────────────────────────────────── */
export function Pagination({ page, totalPages, total, onChange }) {
  if (totalPages <= 1 && !total) return null;
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "12px 20px", borderTop: `1px solid ${T.cardBorder}`,
      flexWrap: "wrap", gap: 8,
    }}>
      {total !== undefined && <span style={{ color: T.textMuted, fontSize: 12 }}>{total} total</span>}
      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}
          style={{
            padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`,
            background: T.inputBg, color: page <= 1 ? T.textMuted : T.textPrimary,
            fontSize: 12, cursor: page <= 1 ? "default" : "pointer", opacity: page <= 1 ? 0.5 : 1,
          }}>
          &#x2190; Prev
        </button>
        {pages.map((p) => (
          <button key={p} onClick={() => onChange(p)}
            style={{
              padding: "4px 10px", borderRadius: 6, border: "none",
              background: p === page ? T.accent : "transparent",
              color: p === page ? "#fff" : T.textSecondary,
              fontSize: 12, cursor: "pointer", fontWeight: p === page ? 600 : 400, minWidth: 28,
            }}>
            {p}
          </button>
        ))}
        <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}
          style={{
            padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`,
            background: T.inputBg, color: page >= totalPages ? T.textMuted : T.textPrimary,
            fontSize: 12, cursor: page >= totalPages ? "default" : "pointer", opacity: page >= totalPages ? 0.5 : 1,
          }}>
          Next &#x2192;
        </button>
      </div>
    </div>
  );
}

/* ── Shared Styles ────────────────────────────────────────── */
export const TABLE_STYLES = {
  wrapper: { background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" },
  header: { color: T.textMuted, fontSize: 10, fontWeight: 600, textAlign: "left", padding: "14px 20px", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" },
  cell: { padding: "14px 20px", color: T.textSecondary, fontSize: 13 },
  cellPrimary: { padding: "14px 20px", color: T.textPrimary, fontSize: 13, fontWeight: 600 },
  cellAccent: { padding: "14px 20px", color: T.accent, fontSize: 13, fontWeight: 600 },
};

/* ── Modal Overlay ────────────────────────────────────────── */
export const MODAL_STYLES = {
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000, padding: 20, backdropFilter: "blur(4px)",
  },
  content: {
    background: T.card, border: `1px solid ${T.cardBorder}`,
    borderRadius: 16, width: "100%", maxWidth: 520,
    maxHeight: "90vh", overflow: "auto", animation: "scaleIn 0.2s ease",
  },
  input: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box",
  },
  label: { display: "block", color: T.textSecondary, fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" },
};

/* ── Page Header ──────────────────────────────────────────── */
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

/* ── Card Wrapper ─────────────────────────────────────────── */
export function Card({ children, style, padding = 24 }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`,
      borderRadius: 16, padding, ...style,
    }}>
      {children}
    </div>
  );
}

/* ── Status Badge Map ─────────────────────────────────────── */
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
