import { useState } from "react";
import AdminWatermark from "./components/AdminWatermark";
import Dashboard from "./components/Dashboard";
import LoginScreen from "./components/LoginScreen";
import { ApiError, adminLogin } from "./api";

// JWT drzimo u sessionStorage (ne localStorage) - prezivi osvjezavanje
// stranice, ali nestaje kad se kartica zatvori. Sam token vec ima
// ugradjeno vrijeme isteka (8-12h, poglavlje 34.4).
const SESSION_KEY = "evoting_admin_token";

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(SESSION_KEY) || "");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleLogin = async (username, password) => {
    setLoading(true);
    setErrorMessage("");
    try {
      const data = await adminLogin(username, password);
      sessionStorage.setItem(SESSION_KEY, data.access_token);
      setToken(data.access_token);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Neočekivana greška pri prijavi.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem(SESSION_KEY);
    setToken("");
  };

  if (!token) {
    return (
      <>
        {/* Fiksni vodeni žig kao na terminalu - ekran za prijavu nema
            vlastitu naslovnu traku pa nema s čime da se preklapa. */}
        <AdminWatermark />
        <LoginScreen onLogin={handleLogin} loading={loading} errorMessage={errorMessage} />
      </>
    );
  }

  return <Dashboard key={token} token={token} onLogout={handleLogout} />;
}
