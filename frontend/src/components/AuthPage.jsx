import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../services/AuthContext.jsx";
import { api } from "../services/api.js";

/* ── Icons (inline SVG, no deps) ── */
const IconMail  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>;
const IconLock  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>;
const IconUser  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>;
const IconPin   = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="10" x2="8" y2="10"/><line x1="12" y1="10" x2="12" y2="10"/><line x1="16" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="12" y1="14" x2="12" y2="14"/><line x1="16" y1="14" x2="16" y2="14"/></svg>;

function InputField({ icon: Icon, ...props }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{
      position: "relative",
      display: "flex",
      alignItems: "center",
    }}>
      <span style={{
        position: "absolute",
        left: 16,
        color: focused ? "var(--brand)" : "var(--text-3)",
        transition: "color 0.15s ease",
        display: "flex",
        pointerEvents: "none",
      }}>
        <Icon />
      </span>
      <input
        {...props}
        onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
        onBlur={(e)  => { setFocused(false); props.onBlur?.(e); }}
        style={{
          width: "100%",
          background: "var(--bg-2)",
          border: `1px solid ${focused ? "var(--brand)" : "var(--border)"}`,
          boxShadow: focused ? "0 0 0 3px var(--brand-dim)" : "none",
          borderRadius: "var(--r-sm)",
          padding: "14px 16px 14px 44px",
          color: "var(--text)",
          fontSize: 15,
          outline: "none",
          transition: "border-color 0.15s ease, box-shadow 0.15s ease",
          ...props.style,
        }}
      />
    </div>
  );
}

export default function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const [authMethod, setAuthMethod] = useState("password");
  const [form, setForm] = useState({ name: "", email: "", password: "", pin: "", role: "member" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isSignup) {
        await signup(form.name, form.email, form.password);
        setSuccess(true);
        setTimeout(() => navigate("/practice"), 900);
      } else if (authMethod === "pin") {
        const res = await api.pinLogin(form.email, form.pin);
        localStorage.setItem("sthira_token", res.token);
        localStorage.setItem("sthira_user", JSON.stringify(res.user));
        setSuccess(true);
        setTimeout(() => { window.location.href = "/practice"; }, 900);
      } else {
        await login(form.email, form.password);
        setSuccess(true);
        setTimeout(() => navigate("/practice"), 900);
      }
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px",
      position: "relative",
    }}>
      {/* Background gradient */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0,
        background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(99,102,241,0.1) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div style={{
        position: "relative",
        zIndex: 1,
        width: "100%",
        maxWidth: 440,
      }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <Link to="/" style={{
            fontFamily: "var(--font-display)",
            fontSize: 28,
            fontWeight: 800,
            color: "var(--text)",
            letterSpacing: "-0.03em",
            textDecoration: "none",
          }}>
            sthira<span style={{ color: "var(--brand)" }}>.</span>
          </Link>
        </div>

        {/* Card */}
        <div style={{
          background: "var(--bg-1)",
          border: "1px solid var(--border)",
          borderRadius: "var(--r-xl)",
          padding: "40px 36px",
          boxShadow: "var(--shadow-lg)",
        }}>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 6 }}>
            {isSignup ? "Create your account" : "Welcome back"}
          </h1>
          <p className="muted" style={{ fontSize: 14, marginBottom: 28 }}>
            {isSignup
              ? "Set up your profile to track workouts and personal bests."
              : "Sign in to begin your coached session."}
          </p>

          {/* Auth method toggle (login only) */}
          {!isSignup && (
            <div style={{
              display: "flex",
              background: "var(--bg-2)",
              borderRadius: "var(--r-sm)",
              padding: 4,
              marginBottom: 24,
              gap: 4,
            }}>
              {[
                { id: "password", label: "Password", icon: "🔑" },
                { id: "pin",      label: "⚡ Quick PIN", icon: null },
              ].map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setAuthMethod(m.id)}
                  style={{
                    flex: 1,
                    background: authMethod === m.id ? "var(--bg-3)" : "transparent",
                    color: authMethod === m.id ? "var(--text)" : "var(--text-3)",
                    border: authMethod === m.id ? "1px solid var(--border-hover)" : "1px solid transparent",
                    borderRadius: "calc(var(--r-sm) - 2px)",
                    padding: "9px 0",
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    boxShadow: authMethod === m.id ? "var(--shadow-sm)" : "none",
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {isSignup && (
              <InputField
                icon={IconUser}
                name="name"
                placeholder="Full name"
                value={form.name}
                onChange={onChange}
                required
                autoComplete="name"
              />
            )}

            <InputField
              icon={IconMail}
              name="email"
              type="email"
              placeholder="Email address"
              value={form.email}
              onChange={onChange}
              required
              autoComplete="email"
            />

            {authMethod === "pin" && !isSignup ? (
              <InputField
                icon={IconPin}
                name="pin"
                type="password"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="4–6 digit PIN"
                value={form.pin}
                onChange={onChange}
                required
                style={{ textAlign: "center", letterSpacing: 8, fontSize: 20 }}
              />
            ) : (
              <InputField
                icon={IconLock}
                name="password"
                type="password"
                placeholder="Password (min 6 chars)"
                value={form.password}
                onChange={onChange}
                required
                minLength={6}
                autoComplete={isSignup ? "new-password" : "current-password"}
              />
            )}

            {/* Error */}
            {error && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.25)",
                borderRadius: "var(--r-sm)",
                padding: "12px 14px",
                color: "var(--red)",
                fontSize: 14,
                fontWeight: 500,
              }}>
                <span>⚠️</span> {error}
              </div>
            )}

            {/* Submit */}
            <button
              className={`btn btn-primary${success ? " btn-success" : ""}`}
              type="submit"
              disabled={busy || success}
              style={{
                marginTop: 6,
                padding: "15px",
                fontSize: 15,
                fontWeight: 700,
                width: "100%",
                background: success ? "var(--green)" : undefined,
                boxShadow: success ? "0 4px 20px rgba(34,197,94,0.3)" : undefined,
                transition: "all 0.3s ease",
              }}
            >
              {success
                ? "✓ Signed in!"
                : busy
                ? "Authenticating…"
                : isSignup
                ? "Create account"
                : authMethod === "pin"
                ? "⚡ Unlock session"
                : "Sign in"}
            </button>
          </form>

          {/* Divider */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            margin: "24px 0",
          }}>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
            <span style={{ color: "var(--text-3)", fontSize: 12 }}>or</span>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          </div>

          <p style={{ textAlign: "center", fontSize: 14, color: "var(--text-2)", margin: 0 }}>
            {isSignup ? (
              <>Already have an account?{" "}
                <Link to="/login" style={{ color: "var(--brand)", fontWeight: 600 }}>Sign in</Link>
              </>
            ) : (
              <>New member?{" "}
                <Link to="/signup" style={{ color: "var(--brand)", fontWeight: 600 }}>Create account</Link>
              </>
            )}
          </p>
        </div>

        {/* Footer note */}
        <p style={{ textAlign: "center", color: "var(--text-3)", fontSize: 12, marginTop: 20 }}>
          🔒 Privacy-first — no video stored, edge inference only.
        </p>
      </div>
    </div>
  );
}
