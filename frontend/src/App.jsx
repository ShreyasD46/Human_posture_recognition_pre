import { Routes, Route, Navigate, Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./services/AuthContext.jsx";
import Landing from "./components/Landing.jsx";
import AuthPage from "./components/AuthPage.jsx";
import PosePicker from "./components/PosePicker.jsx";
import SessionView from "./components/SessionView.jsx";
import Dashboard from "./components/Dashboard.jsx";

function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? "active" : "";

  if (location.pathname.startsWith("/session")) {
    return null;
  }

  return (
    <div className="topbar-wrapper">
      <div className="floating-navbar">
        <Link to="/" className="wordmark">sthira<span>.</span></Link>
        
        <div className="nav-pill-group">
          <Link to="/" className={`nav-item ${isActive("/")}`}>Home</Link>
          {user && (
            <>
              <Link to="/practice" className={`nav-item ${isActive("/practice")}`}>Practice</Link>
              <Link to="/dashboard" className={`nav-item ${isActive("/dashboard")}`}>Progress</Link>
            </>
          )}
          
          {user ? (
            <button className="nav-btn-primary" onClick={() => { logout(); navigate("/"); }}>Sign out</button>
          ) : (
            <Link to="/login" className="nav-btn-primary">Sign in</Link>
          )}
        </div>
      </div>
    </div>
  );
}

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Topbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/signup" element={<AuthPage mode="signup" />} />
        <Route path="/practice" element={<Protected><PosePicker /></Protected>} />
        <Route path="/session/:poseId" element={<Protected><SessionView /></Protected>} />
        <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      </Routes>
    </>
  );
}
