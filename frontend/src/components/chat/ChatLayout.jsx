import { T } from "../../styles/theme";

export default function ChatLayout({ sidebar, main, tools, showSidebar, showTools }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        height: "calc(100vh - 144px)",
        position: "relative",
        maxWidth: "1600px",
        margin: "0 auto",
        width: "100%",
      }}
    >
      {/* ── Left Sidebar: History ── */}
      <div
        style={{
          width: 260,
          flexShrink: 0,
          display: showSidebar ? "flex" : "none",
          flexDirection: "column",
        }}
      >
        {sidebar}
      </div>

      {/* ── Main Chat Area ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {main}
      </div>

      {/* ── Right Panel: AI Tools ── */}
      <div
        style={{
          width: 280,
          flexShrink: 0,
          display: showTools ? "flex" : "none",
          flexDirection: "column",
        }}
      >
        {tools}
      </div>
    </div>
  );
}
