import { T } from "../styles/theme";
import { ANIM_STYLES } from "../styles/shared";
import Topbar from "./Topbar";

export default function PageShell({ title, user, children }) {
  return (
    <>
      <style>{ANIM_STYLES}</style>
      <div style={{ width: "100%", minHeight: "100vh", background: T.bg, display: "flex", flexDirection: "column" }}>
        <Topbar title={title} user={user} />
        <main style={{ padding: "24px", flex: 1, width: "100%", maxWidth: "none", overflowX: "hidden" }}>
          {children}
        </main>
      </div>
    </>
  );
}
