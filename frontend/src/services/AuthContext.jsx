import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("sthira_token");
    if (!token) { setLoading(false); return; }
    api.me().then(setUser).catch(() => localStorage.removeItem("sthira_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { token, user } = await api.login({ email, password });
    localStorage.setItem("sthira_token", token);
    setUser(user);
  };

  const signup = async (name, email, password) => {
    const { token, user } = await api.signup({ name, email, password });
    localStorage.setItem("sthira_token", token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("sthira_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
