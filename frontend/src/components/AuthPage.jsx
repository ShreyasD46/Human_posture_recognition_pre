import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../services/AuthContext.jsx";
import { api } from "../services/api.js";

export default function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const [authMethod, setAuthMethod] = useState("password"); // "password" | "pin"
  const [form, setForm] = useState({ name: "", email: "", password: "", pin: "", role: "member" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isSignup) {
        await signup(form.name, form.email, form.password);
      } else if (authMethod === "pin") {
        const res = await api.pinLogin(form.email, form.pin);
        localStorage.setItem("sthira_token", res.token);
        localStorage.setItem("sthira_user", JSON.stringify(res.user));
        window.location.href = "/practice";
        return;
      } else {
        await login(form.email, form.password);
      }
      navigate("/practice");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 440, paddingTop: 40, margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8, letterSpacing: "-0.5px" }}>
          {isSignup ? "Create Member Profile" : "Kiosk Member Login"}
        </h1>
        <p className="muted" style={{ margin: 0, fontSize: 15 }}>
          {isSignup ? "Set up your profile to track workouts and PBs." : "Sign in to begin your coached workout."}
        </p>
      </div>

      {!isSignup && (
        <div style={{ display: "flex", background: "rgba(255,255,255,0.06)", borderRadius: 10, padding: 3, marginBottom: 20 }}>
          <button
            type="button"
            onClick={() => setAuthMethod("password")}
            style={{
              flex: 1,
              background: authMethod === "password" ? "var(--accent-soft, #E7B978)" : "transparent",
              color: authMethod === "password" ? "#0F172A" : "var(--text-muted)",
              border: "none",
              borderRadius: 8,
              padding: "8px 0",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            Password Login
          </button>
          <button
            type="button"
            onClick={() => setAuthMethod("pin")}
            style={{
              flex: 1,
              background: authMethod === "pin" ? "var(--accent-soft, #E7B978)" : "transparent",
              color: authMethod === "pin" ? "#0F172A" : "var(--text-muted)",
              border: "none",
              borderRadius: 8,
              padding: "8px 0",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            ⚡ Fast Touch PIN
          </button>
        </div>
      )}

      <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {isSignup && (
          <input
            name="name"
            placeholder="Full Name"
            value={form.name}
            onChange={onChange}
            required
            style={inputStyle}
          />
        )}

        <input
          name="email"
          type="email"
          placeholder="Member Email"
          value={form.email}
          onChange={onChange}
          required
          style={inputStyle}
        />

        {(!isSignup && authMethod === "pin") ? (
          <div>
            <input
              name="pin"
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              placeholder="Enter 4-6 Digit PIN"
              value={form.pin}
              onChange={onChange}
              required
              style={{ ...inputStyle, textAlign: "center", fontSize: 22, letterSpacing: 8 }}
            />
          </div>
        ) : (
          <input
            name="password"
            type="password"
            placeholder="Password (min 6 chars)"
            value={form.password}
            onChange={onChange}
            required
            minLength={6}
            style={inputStyle}
          />
        )}

        {error && (
          <div style={{ color: "#EF4444", fontSize: 14, background: "rgba(239,68,68,0.1)", padding: "8px 12px", borderRadius: 8 }}>
            {error}
          </div>
        )}

        <button className="btn btn-primary" type="submit" disabled={busy} style={{ marginTop: 8, padding: 14, fontSize: 16 }}>
          {busy ? "Authenticating…" : isSignup ? "Create Profile" : authMethod === "pin" ? "⚡ Unlock Session" : "Sign In"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 24, fontSize: 14, textAlign: "center" }}>
        {isSignup ? (
          <>Already registered? <Link to="/login" style={{ color: "var(--accent-soft)" }}>Sign in</Link></>
        ) : (
          <>New member? <Link to="/signup" style={{ color: "var(--accent-soft)" }}>Create account</Link></>
        )}
      </p>
    </div>
  );
}

const inputStyle = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10,
  padding: "12px 16px",
  color: "#FFF",
  fontSize: 15,
  outline: "none",
};
