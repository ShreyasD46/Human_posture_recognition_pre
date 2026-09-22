import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.dashboard().then(setData);
    api.sessions().then(setSessions);
  }, []);

  return (
    <div className="page" style={{ paddingTop: 40 }}>
      <h1 style={{ fontSize: 32, marginBottom: 28 }}>Your progress</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 32 }}>
        <div className="card">
          <div style={{ fontFamily: "var(--font-display)", fontSize: 30, color: "var(--accent-soft)" }}>
            {data?.total_sessions ?? "–"}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>sessions logged</div>
        </div>
        <div className="card">
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, color: "var(--accent-soft)" }}>
            {data?.most_improved_pose ? formatPoseName(data.most_improved_pose) : "Keep going"}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>most improved pose</div>
        </div>
      </div>

      <h2 style={{ fontSize: 19, marginBottom: 14 }}>Session history</h2>
      {sessions.length === 0 && <p className="muted">No sessions yet — head to Practice to get started.</p>}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {sessions.map((s) => (
          <div key={s.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{formatPoseName(s.pose_name)}</div>
              <div className="muted" style={{ fontSize: 13 }}>
                {new Date(s.started_at).toLocaleDateString()} · {Math.round(s.hold_time_seconds)}s held
              </div>
            </div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 22, color: "var(--accent-soft)" }}>
              {s.accuracy_pct}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatPoseName(id) {
  return id.split("_").map((w) => w[0]?.toUpperCase() + w.slice(1)).join(" ");
}
