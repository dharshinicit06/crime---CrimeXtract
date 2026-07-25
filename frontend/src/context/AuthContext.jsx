import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { loginAPI, registerAPI, getStoredUser, clearAuth } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCurrentUser(getStoredUser());
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await loginAPI(email, password);
    setCurrentUser(getStoredUser());
    return data;
  }, []);

  const signup = useCallback(async (form) => {
    const data = await registerAPI(form);
    setCurrentUser(getStoredUser());
    return data;
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setCurrentUser(null);
  }, []);

  const value = {
    currentUser,
    login,
    logout,
    signup,
    loading,
    isAuthenticated: !!currentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
