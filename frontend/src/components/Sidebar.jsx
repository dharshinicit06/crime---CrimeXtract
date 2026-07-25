import { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { LogOut } from "lucide-react";
import { T } from "../styles/theme";
import { useAuth } from "../context/AuthContext";
import { NAV_ITEMS } from "../data/constants";
import Badge from "./Badge";
import LogoutConfirmDialog from "./LogoutConfirmDialog";

export default function Sidebar() {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [logoutHover, setLogoutHover] = useState(false);

  const handleLogout = () => {
    setShowLogoutDialog(true);
  };

  const confirmLogout = () => {
    logout();
    setShowLogoutDialog(false);
    navigate("/");
  };

  const cancelLogout = () => {
    setShowLogoutDialog(false);
  };

  return (
    <>
      <aside
        style={{
          width: T.sidebarWidth,
          background: T.surface,
          borderRight: `1px solid ${T.cardBorder}`,
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          position: "fixed",
          top: 0,
          left: 0,
          zIndex: 100,
          flexShrink: 0,
        }}
      >
        {/* ── Logo ── */}
        <div style={{ padding: "20px 20px 0" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 24,
              padding: "0 4px",
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 18,
              }}
            >
              🛡
            </div>
            <div>
              <div
                style={{
                  color: T.textPrimary,
                  fontWeight: 700,
                  fontSize: 15,
                  lineHeight: 1,
                }}
              >
                CrimeAI
              </div>
              <div style={{ color: T.textMuted, fontSize: 10, marginTop: 2 }}>
                KSP Intelligence Platform
              </div>
            </div>
          </div>

          {/* ── User profile card ── */}
          <div
            style={{
              padding: "12px",
              background: T.card,
              borderRadius: 12,
              marginBottom: 16,
              border: `1px solid ${T.cardBorder}`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 8,
                  background: `linear-gradient(135deg, ${T.accent}44, ${T.purple}44)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  fontWeight: 700,
                  color: T.accent,
                }}
              >
                {currentUser?.name?.[0] || "U"}
              </div>
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    color: T.textPrimary,
                    fontSize: 13,
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {currentUser?.name}
                </div>
                <div style={{ color: T.textMuted, fontSize: 10 }}>
                  {currentUser?.email}
                </div>
              </div>
              <Badge label={currentUser?.role} />
            </div>
          </div>
        </div>

        {/* ── Scrollable nav area ── */}
        <nav
          style={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            padding: "0 20px 8px",
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.id}
              to={item.path}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "9px 12px",
                borderRadius: 9,
                border: "none",
                cursor: "pointer",
                textAlign: "left",
                textDecoration: "none",
                background: isActive ? T.accentGlow : "transparent",
                color: isActive ? T.accent : T.textSecondary,
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                transition: "all 0.15s",
                borderLeft: isActive
                  ? `2px solid ${T.accent}`
                  : "2px solid transparent",
              })}
            >
              <span style={{ fontSize: 15, flexShrink: 0 }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* ── Logout button (always pinned to bottom) ── */}
        <div
          style={{
            padding: "12px 20px 16px",
            borderTop: `1px solid ${T.cardBorder}`,
            background: T.surface,
          }}
        >
          <button
            onClick={handleLogout}
            onMouseEnter={() => setLogoutHover(true)}
            onMouseLeave={() => setLogoutHover(false)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "100%",
              padding: "10px 12px",
              borderRadius: 9,
              border: "none",
              cursor: "pointer",
              background: logoutHover
                ? "rgba(239,68,68,0.15)"
                : "rgba(239,68,68,0.06)",
              color: logoutHover ? "#f87171" : T.danger,
              fontSize: 13,
              fontWeight: 500,
              transition: "all 0.2s",
              transform: logoutHover ? "translateY(-1px)" : "none",
            }}
          >
            <LogOut size={16} style={{ flexShrink: 0 }} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <LogoutConfirmDialog
        open={showLogoutDialog}
        onCancel={cancelLogout}
        onConfirm={confirmLogout}
      />
    </>
  );
}
