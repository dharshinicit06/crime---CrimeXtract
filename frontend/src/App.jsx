import { lazy, Suspense } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { T } from "./styles/theme";
import { useAuth } from "./context/AuthContext";
import { DemoModeProvider } from "./context/DemoModeContext";
import ProtectedRoute from "./routes/ProtectedRoute";
import MainLayout from "./layouts/MainLayout";
import ErrorBoundary from "./components/ErrorBoundary";

// ── Lazy-loaded pages for route-based code splitting ────────────
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const AIChat = lazy(() => import("./pages/AIChat"));
const FIRManagement = lazy(() => import("./pages/FIRManagement"));
const Settings = lazy(() => import("./pages/Settings"));
const Analytics = lazy(() => import("./pages/Analytics"));
const CrimeHotspots = lazy(() => import("./pages/CrimeHotspots"));
const CriminalNetwork = lazy(() => import("./pages/CriminalNetwork"));
const OffenderProfile = lazy(() => import("./pages/OffenderProfile"));
const AIPrediction = lazy(() => import("./pages/AIPrediction"));
const Reports = lazy(() => import("./pages/Reports"));
const Users = lazy(() => import("./pages/Users"));
const Victims = lazy(() => import("./pages/Victims"));
const Accused = lazy(() => import("./pages/Accused"));
const Evidence = lazy(() => import("./pages/Evidence"));
const CrimeHistory = lazy(() => import("./pages/CrimeHistory"));
const FinancialTransactions = lazy(() => import("./pages/FinancialTransactions"));
const Locations = lazy(() => import("./pages/Locations"));
const PredictionDashboard = lazy(() => import("./pages/PredictionDashboard"));
const AuditLogs = lazy(() => import("./pages/AuditLogs"));

function PageLoader() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: T.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ color: T.textMuted, fontSize: 14 }}>Loading…</div>
    </div>
  );
}

const GLOBAL_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
  input::placeholder { color: #475569; }
  select option { background: #141A26; color: #f1f5f9; }
  button { font-family: inherit; }
  input { font-family: inherit; }
  body { font-family: Inter, -apple-system, sans-serif; overflow-x: hidden; }
  :focus-visible { outline: 2px solid #5B7FFF; outline-offset: 2px; }
  a { color: inherit; text-decoration: none; }
`;

export default function App() {
  const { isAuthenticated, loading, currentUser } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: T.bg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ color: T.textMuted, fontSize: 14 }}>Loading…</div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <HashRouter>
        <DemoModeProvider>
        <style>{GLOBAL_STYLES}</style>
        <div style={{ minHeight: "100vh", background: T.bg }}>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route
                path="/"
                element={
                  isAuthenticated ? (
                    <Navigate to="/dashboard" replace />
                  ) : (
                    <LoginPage />
                  )
                }
              />
              <Route
                path="/signup"
                element={
                  isAuthenticated ? (
                    <Navigate to="/dashboard" replace />
                  ) : (
                    <SignupPage />
                  )
                }
              />

              <Route element={<ProtectedRoute />}>
                <Route element={<MainLayout />}>
                  <Route path="/dashboard" element={<Dashboard user={currentUser} />} />
                  <Route path="/chat" element={<AIChat user={currentUser} />} />
                  <Route path="/fir" element={<FIRManagement user={currentUser} />} />
                  <Route path="/settings" element={<Settings user={currentUser} />} />
                  <Route path="/analytics" element={<Analytics user={currentUser} />} />
                  <Route path="/hotspots" element={<CrimeHotspots user={currentUser} />} />
                  <Route path="/network" element={<CriminalNetwork user={currentUser} />} />
                  <Route path="/offender" element={<OffenderProfile user={currentUser} />} />
                  <Route path="/prediction" element={<AIPrediction user={currentUser} />} />
                  <Route path="/reports" element={<Reports user={currentUser} />} />
                  <Route path="/users" element={<Users user={currentUser} />} />
                  <Route path="/victims" element={<Victims user={currentUser} />} />
                  <Route path="/accused" element={<Accused user={currentUser} />} />
                  <Route path="/evidence" element={<Evidence user={currentUser} />} />
                  <Route path="/crime-history" element={<CrimeHistory user={currentUser} />} />
                  <Route path="/transactions" element={<FinancialTransactions user={currentUser} />} />
                  <Route path="/forecast" element={<PredictionDashboard user={currentUser} />} />
                  <Route path="/locations" element={<Locations user={currentUser} />} />
                  <Route path="/audit-logs" element={<AuditLogs user={currentUser} />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </div>
        </DemoModeProvider>
      </HashRouter>
    </ErrorBoundary>
  );
}
