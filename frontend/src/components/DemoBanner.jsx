import { useDemoMode } from "../context/DemoModeContext";

export default function DemoBanner() {
  const { isDemoMode, toggleDemoMode } = useDemoMode();

  if (!isDemoMode) return null;

  return (
    <div
      style={{
        background: "linear-gradient(90deg, #5B7FFF, #7C5CFF)",
        padding: "6px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        fontSize: 12,
        color: "#fff",
        fontWeight: 500,
        flexShrink: 0,
        position: "sticky",
        top: 0,
        zIndex: 200,
      }}
    >
      <span>&#x1F6A7;</span>
      <span>
        <strong>Demo Mode</strong> — Viewing sample Karnataka Police data.{" "}
        <button
          onClick={toggleDemoMode}
          style={{
            background: "rgba(255,255,255,0.2)",
            border: "none",
            color: "#fff",
            padding: "2px 10px",
            borderRadius: 4,
            fontSize: 11,
            cursor: "pointer",
            fontWeight: 600,
            marginLeft: 4,
          }}
        >
          Switch to Production
        </button>
      </span>
    </div>
  );
}
