import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function PosePicker() {
  const [poses, setPoses] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.poses().then(setPoses).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page" style={{ paddingTop: 40 }}>
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>Choose a pose</h1>
      <p className="muted" style={{ marginBottom: 32 }}>
        Stand where your camera can see your full body, front-facing, before you start.
      </p>
      {error && <p style={{ color: "var(--error)" }}>{error}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 18 }}>
        {poses.map((p) => (
          <button
            key={p.id}
            className="card"
            style={{ textAlign: "left", color: "var(--text)" }}
            onClick={() => navigate(`/session/${p.id}`)}
          >
            <h3 style={{ fontSize: 19, marginBottom: 10 }}>{p.label}</h3>
            <p className="muted" style={{ fontSize: 14, lineHeight: 1.5, margin: 0 }}>{p.instructions}</p>
            <div style={{ marginTop: 16, fontSize: 13, color: "var(--accent-soft)" }}>
              Target hold: {p.hold_time_target}s
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
