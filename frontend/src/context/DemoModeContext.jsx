import { createContext, useContext, useState, useCallback, useEffect } from "react";

const DEMO_KEY = "crimeai_demo_mode";

const DemoModeContext = createContext(null);

export function DemoModeProvider({ children }) {
  const [isDemoMode, setIsDemoMode] = useState(() => {
    try { return localStorage.getItem(DEMO_KEY) === "true"; }
    catch { return false; }
  });

  useEffect(() => {
    try {
      if (isDemoMode) localStorage.setItem(DEMO_KEY, "true");
      else localStorage.removeItem(DEMO_KEY);
    } catch {}
  }, [isDemoMode]);

  const toggleDemoMode = useCallback(() => setIsDemoMode((p) => !p), []);
  const enableDemoMode = useCallback(() => setIsDemoMode(true), []);
  const disableDemoMode = useCallback(() => setIsDemoMode(false), []);

  return (
    <DemoModeContext.Provider value={{ isDemoMode, toggleDemoMode, enableDemoMode, disableDemoMode }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  const ctx = useContext(DemoModeContext);
  if (!ctx) throw new Error("useDemoMode must be used within DemoModeProvider");
  return ctx;
}
