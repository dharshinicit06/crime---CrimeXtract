const COLORS = {
  Open: { bg: "rgba(239,68,68,0.15)", color: "#ef4444" },
  "Under Investigation": { bg: "rgba(245,158,11,0.15)", color: "#f59e0b" },
  Closed: { bg: "rgba(34,197,94,0.15)", color: "#22c55e" },
  Investigator: { bg: "rgba(59,130,246,0.15)", color: "#3b82f6" },
  Supervisor: { bg: "rgba(139,92,246,0.15)", color: "#8b5cf6" },
  Analyst: { bg: "rgba(20,184,166,0.15)", color: "#14b8a6" },
  Policymaker: { bg: "rgba(245,158,11,0.15)", color: "#f59e0b" },
};

export default function Badge({ label, color }) {
  const c = COLORS[label] || {
    bg: "rgba(148,163,184,0.15)",
    color: "#94a3b8",
  };

  return (
    <span
      style={{
        background: c.bg,
        color: c.color,
        padding: "3px 10px",
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.5px",
      }}
    >
      {label}
    </span>
  );
}
