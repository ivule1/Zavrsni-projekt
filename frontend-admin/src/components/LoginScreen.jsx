import { useState } from "react";

export default function LoginScreen({ onLogin, loading, errorMessage }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (username.trim() && password) {
      onLogin(username.trim(), password);
    }
  };

  return (
    <div className="admin-login-wrap">
      <form className="admin-login-card" onSubmit={handleSubmit}>
        <h1 className="admin-title mb-1">E-Glasanje</h1>
        <p className="text-muted mb-4">Admin nadzor</p>

        <label className="form-label" htmlFor="username">
          Korisničko ime
        </label>
        <input
          id="username"
          className="form-control mb-3"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
          disabled={loading}
        />

        <label className="form-label" htmlFor="password">
          Lozinka
        </label>
        <input
          id="password"
          type="password"
          className="form-control mb-3"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
        />

        {errorMessage && <div className="alert alert-danger py-2">{errorMessage}</div>}

        <button
          type="submit"
          className="btn admin-btn text-white w-100"
          disabled={loading || !username.trim() || !password}
        >
          {loading ? "Prijava u tijeku..." : "Prijavi se"}
        </button>
      </form>
    </div>
  );
}
