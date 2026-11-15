import { useEffect, useState } from "react";
import { api } from "../services/api";

const CATEGORY_COLORS = { gym: "#f97316", yoga: "#a78bfa", default: "var(--accent-soft)" };
const CATEGORY_ICONS  = { gym: "🏋️", yoga: "🧘", default: "⚡" };

export default function Dashboard() {
  const [data, setSummary]   = useState(null);
  const [sessions, setSessions] = useState([]);
  const [filter, setFilter]  = useState("all"); // all | gym | yoga

  useEffect(() => {
    api.dashboard().then(setSummary).catch(() => {});
    api.sessions().then(setSessions).catch(() => {});
  }, []);

  const visible = sessions.filter(
    (s) => filter === "all" || (s.category || "yoga") === filter
  );

  const totalReps = sessions.reduce((acc, s) => acc + (s.total_reps || 0), 0);
  const totalHold = sessions.reduce((acc, s) => acc + (s.hold_time_seconds || 0), 0);
  const avgScore  = sessions.length
    ? Math.round(sessions.reduce((a, s) => a + (s.avg_score || 0), 0) / sessions.length)
    : 0;

  return (
    <div className="page" style={{ paddingTop: 40 }}>
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>Your Progress</h1>
      <p className="muted" style={{ marginBottom: 28 }}>
        All workouts · {sessions.length} sessions total
      </p>

      {/* ── Stat cards ── */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
        gap: 14,
        marginBottom: 36,
      }}>
        <StatCard label="Sessions" value={data?.total_sessions ?? sessions.length} />
        <StatCard label="Total Reps" value={totalReps || "–"} accent="#f97316" />
        <StatCard label="Hold Time" value={totalHold ? `${Math.round(totalHold)}s` : "–"} accent="#a78bfa" />
        <StatCard label="Avg Form Score" value={avgScore ? `${avgScore}%` : "–"} accent="#34d399" />
        <StatCard
          label="Most Improved"
          value={data?.most_improved_pose ? fmt(data.most_improved_pose) : "Keep going!"}
          small
        />
      </div>

      {/* ── Filter tabs ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["all", "gym", "yoga"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: "6px 18px",
              borderRadius: 20,
              border: "1px solid var(--border)",
              background: filter === f ? "var(--accent-soft)" : "transparent",
              color: filter === f ? "#000" : "var(--text)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: 13,
            }}
          >
            {f === "all" ? "All" : f === "gym" ? "🏋️ Gym" : "🧘 Yoga"}
          </button>
        ))}
      </div>

      {/* ── Session list ── */}
      <h2 style={{ fontSize: 19, marginBottom: 14 }}>Session History</h2>
      {visible.length === 0 && (
        <p className="muted">No sessions yet — head to Practice to get started.</p>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {visible.map((s) => {
          const cat   = s.category || "yoga";
          const color = CATEGORY_COLORS[cat] || CATEGORY_COLORS.default;
          const icon  = CATEGORY_ICONS[cat]  || CATEGORY_ICONS.default;
          const isGym = cat === "gym";

          return (
            <div
              key={s.id}
              className="card"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderLeft: `3px solid ${color}`,
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>
                  {icon} {fmt(s.pose_name || s.exercise_id)}
                </div>
                <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
                  {s.started_at ? new Date(s.started_at).toLocaleDateString() : ""}
                  {isGym
                    ? ` · ${s.total_reps ?? 0} reps`
                    : ` · ${Math.round(s.hold_time_seconds ?? 0)}s held`}
                  {s.tempo_score != null ? ` · tempo ${Math.round(s.tempo_score)}%` : ""}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 22,
                    color,
                  }}
                >
                  {s.avg_score != null ? `${Math.round(s.avg_score)}%` : "–"}
                </div>
                <div className="muted" style={{ fontSize: 11 }}>form score</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatCard({ label, value, accent, small }) {
  return (
    <div className="card" style={{ minHeight: 90, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <div
        style={{
          fontFamily: "var(--font-display)",
          fontSize: small ? 16 : 28,
          color: accent || "var(--accent-soft)",
          lineHeight: 1.2,
        }}
      >
        {value}
      </div>
      <div className="muted" style={{ fontSize: 12, marginTop: 5 }}>{label}</div>
    </div>
  );
}

function fmt(id = "") {
  return id.split(/[_\s]+/).map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}
