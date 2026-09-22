import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../services/AuthContext.jsx";

export default function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isSignup) await signup(form.name, form.email, form.password);
      else await login(form.email, form.password);
      navigate("/practice");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 420, paddingTop: 60 }}>
      <h1 style={{ fontSize: 30, marginBottom: 8 }}>{isSignup ? "Create your account" : "Welcome back"}</h1>
      <p className="muted" style={{ marginBottom: 32 }}>
        {isSignup ? "A few seconds, then straight into your first pose." : "Sign in to pick up where you left off."}
      </p>
      <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {isSignup && (
          <input name="name" placeholder="Name" value={form.name} onChange={onChange} required />
        )}
        <input name="email" type="email" placeholder="Email" value={form.email} onChange={onChange} required />
        <input name="password" type="password" placeholder="Password" value={form.password} onChange={onChange} required minLength={6} />
        {error && <div style={{ color: "var(--error)", fontSize: 14 }}>{error}</div>}
        <button className="btn btn-primary" type="submit" disabled={busy} style={{ marginTop: 6 }}>
          {busy ? "Please wait…" : isSignup ? "Create account" : "Sign in"}
        </button>
      </form>
      <p className="muted" style={{ marginTop: 22, fontSize: 14 }}>
        {isSignup ? (
          <>Already have an account? <Link to="/login" style={{ color: "var(--accent-soft)" }}>Sign in</Link></>
        ) : (
          <>New here? <Link to="/signup" style={{ color: "var(--accent-soft)" }}>Create an account</Link></>
        )}
      </p>
    </div>
  );
}
