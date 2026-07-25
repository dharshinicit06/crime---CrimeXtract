import { Outlet } from "react-router-dom";
import { T } from "../styles/theme";
import Sidebar from "../components/Sidebar";
import DemoBanner from "../components/DemoBanner";

export default function MainLayout() {
  return (
    <div
      style={{
        display: "flex",
        fontFamily: "Inter, -apple-system, sans-serif",
        minHeight: "100vh",
        background: T.bg,
      }}
    >
      <Sidebar />
      <div style={{ flex: 1, overflowX: "hidden", marginLeft: T.sidebarWidth, display: "flex", flexDirection: "column" }}>
        <DemoBanner />
        <Outlet />
      </div>
    </div>
  );
}
