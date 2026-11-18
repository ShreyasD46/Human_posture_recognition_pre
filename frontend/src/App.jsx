import { Routes, Route, Navigate, Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./services/AuthContext.jsx";
import Landing    from "./components/Landing.jsx";
import AuthPage   from "./components/AuthPage.jsx";
import PosePicker from "./components/PosePicker.jsx";
import SessionView from "./components/SessionView.jsx";
import Dashboard  from "./components/Dashboard.jsx";

function Topbar() {
  const { user, logout } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();
  const isActive  = (p) => location.pathname === p ? "active" : "";

  /* Hide navbar during live session */
  if (location.pathname.startsWith("/session")) return null;

  return (
    <div className="topbar-wrapper">
      <nav className="floating-navbar">
        {/* Wordmark */}
        <Link to="/" className="wordmark">
          sthira<span>.</span>
        </Link>

        {/* Nav links */}
        <div className="nav-pill-group">
          <Link to="/" className={`nav-item ${isActive("/")}`}>Home</Link>
          {user && (
            <>
              <Link to="/practice"  className={`nav-item ${isActive("/practice")}`}>Practice</Link>
              <Link to="/dashboard" className={`nav-item ${isActive("/dashboard")}`}>Progress</Link>
            </>
          )}
        </div>

        {/* Auth button */}
        {user ? (
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginLeft: 8 }}>
            <span style={{ fontSize: 13, color: "var(--text-3)", fontWeight: 500 }}>
              {user.name?.split(" ")[0] ?? user.email}
            </span>
            <button
              className="nav-btn-primary"
              onClick={() => { logout(); navigate("/"); }}
              style={{ background: "rgba(239,68,68,0.15)", color: "var(--red)", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              Sign out
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", gap: 8, marginLeft: 8 }}>
            <Link to="/login" style={{
              padding: "9px 18px", borderRadius: "var(--r-full)", fontSize: 14, fontWeight: 600,
              color: "var(--text-2)", border: "1px solid var(--border)", borderRadius: "var(--r-full)",
              textDecoration: "none", transition: "all 0.15s ease",
            }}>
              Sign in
            </Link>
            <Link to="/signup" className="nav-btn-primary">
              Get started
            </Link>
          </div>
        )}
      </nav>
    </div>
  );
}

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
      <div style={{ color: "var(--text-3)", fontSize: 15 }}>⚡ Loading…</div>
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Topbar />
      <Routes>
        <Route path="/"          element={<Landing />} />
        <Route path="/login"     element={<AuthPage mode="login"  />} />
        <Route path="/signup"    element={<AuthPage mode="signup" />} />
        <Route path="/practice"  element={<Protected><PosePicker /></Protected>} />
        <Route path="/session/:poseId" element={<Protected><SessionView /></Protected>} />
        <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
        <Route path="*"          element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
