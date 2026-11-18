import { useEffect, useState } from "react";
import { api } from "../services/api";

const STAT_CONFIG = [
  { key: "total_sessions", label: "Sessions",        icon: "📅", color: "var(--brand)" },
  { key: "total_reps",     label: "Total Reps",      icon: "🔁", color: "var(--gym)"   },
  { key: "total_hold",     label: "Hold Time",       icon: "⏱", color: "var(--yoga)",  format: (v) => v ? `${Math.round(v)}s` : "–" },
  { key: "avg_score",      label: "Avg Form Score",  icon: "⭐", color: "var(--green)", format: (v) => v ? `${Math.round(v)}%` : "–" },
];

function StatCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: "var(--bg-1)", border: "1px solid var(--border)",
      borderRadius: "var(--r-lg)", padding: "24px 20px",
      display: "flex", flexDirection: "column", gap: 6,
      position: "relative", overflow: "hidden",
      transition: "border-color 0.2s, transform 0.2s",
    }}
    onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-hover)"; e.currentTarget.style.transform = "translateY(-2px)"; }}
    onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.transform = "none"; }}
    >
      <div style={{
        position: "absolute", top: 0, right: 0, left: 0, height: 2,
        background: `linear-gradient(90deg, ${color}, transparent)`,
        borderRadius: "var(--r-lg) var(--r-lg) 0 0",
      }} />
      <div style={{ fontSize: 22 }}>{icon}</div>
      <div style={{
        fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 800,
        color, lineHeight: 1,
      }}>{value}</div>
      <div style={{ color: "var(--text-3)", fontSize: 12, fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase" }}>
        {label}
      </div>
    </div>
  );
}

function SessionRow({ s }) {
  const isGym = (s.category || "yoga") === "gym";
  const accent = isGym ? "var(--gym)" : "var(--yoga)";
  const score = s.avg_score != null ? Math.round(s.avg_score) : null;
  const scoreColor = score == null ? "var(--text-3)" : score >= 80 ? "var(--green)" : score >= 50 ? "var(--amber)" : "var(--red)";

  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      background: "var(--bg-1)", border: "1px solid var(--border)",
      borderRadius: "var(--r-md)", padding: "16px 20px",
      borderLeft: `3px solid ${accent}`,
      transition: "border-color 0.15s, background 0.15s",
    }}
    onMouseEnter={(e) => { e.currentTarget.style.background = "var(--bg-2)"; }}
    onMouseLeave={(e) => { e.currentTarget.style.background = "var(--bg-1)"; }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{
          width: 42, height: 42, borderRadius: "var(--r-sm)",
          background: isGym ? "var(--gym-dim)" : "var(--yoga-dim)",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0,
        }}>
          {isGym ? "🏋️" : "🧘"}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
            {fmt(s.pose_name || s.exercise_id || "Unknown")}
          </div>
          <div style={{ color: "var(--text-3)", fontSize: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <span>{s.started_at ? new Date(s.started_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "2-digit" }) : "—"}</span>
            {isGym
              ? <span style={{ color: "var(--gym)", fontWeight: 600 }}>🔁 {s.total_reps ?? 0} reps</span>
              : <span style={{ color: "var(--yoga)", fontWeight: 600 }}>⏱ {Math.round(s.hold_time_seconds ?? 0)}s hold</span>
            }
            {s.tempo_score != null && <span>🎵 Tempo {Math.round(s.tempo_score)}%</span>}
          </div>
        </div>
      </div>

      <div style={{ textAlign: "right", flexShrink: 0 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 800, color: scoreColor }}>
          {score != null ? `${score}%` : "—"}
        </div>
        <div style={{ color: "var(--text-3)", fontSize: 11, fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase" }}>
          form score
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData]       = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState("all");

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([api.dashboard(), api.sessions()])
      .then(([d, s]) => {
        if (d.status === "fulfilled") setData(d.value);
        if (s.status === "fulfilled") setSessions(s.value);
      })
      .finally(() => setLoading(false));
  }, []);

  const visible = sessions.filter((s) => filter === "all" || (s.category || "yoga") === filter);
  const totalReps = sessions.reduce((a, s) => a + (s.total_reps || 0), 0);
  const totalHold = sessions.reduce((a, s) => a + (s.hold_time_seconds || 0), 0);
  const avgScore  = sessions.length
    ? Math.round(sessions.reduce((a, s) => a + (s.avg_score || 0), 0) / sessions.length)
    : null;

  const stats = [
    { icon: "📅", label: "Sessions",       value: data?.total_sessions ?? sessions.length, color: "var(--brand)" },
    { icon: "🔁", label: "Total Reps",     value: totalReps || "–",                        color: "var(--gym)"   },
    { icon: "⏱",  label: "Hold Time",      value: totalHold ? `${Math.round(totalHold)}s` : "–", color: "var(--yoga)" },
    { icon: "⭐", label: "Avg Form Score", value: avgScore ? `${avgScore}%` : "–",         color: "var(--green)" },
  ];

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{
            background: "var(--brand-dim)", color: "var(--brand)",
            fontSize: 12, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
            padding: "5px 12px", borderRadius: "var(--r-full)",
          }}>
            📊 Progress
          </span>
        </div>
        <h1 style={{ fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 800, marginBottom: 10 }}>
          Your Training History
        </h1>
        <p className="muted" style={{ fontSize: 16 }}>
          Track your form scores, reps, hold times and personal bests across all workouts.
        </p>
      </div>

      {/* Stat cards */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 16, marginBottom: 40,
      }}>
        {stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      {/* Most improved banner */}
      {data?.most_improved_pose && (
        <div style={{
          background: "linear-gradient(135deg, var(--brand-dim), rgba(167,139,250,0.1))",
          border: "1px solid rgba(99,102,241,0.25)",
          borderRadius: "var(--r-lg)", padding: "20px 24px",
          display: "flex", alignItems: "center", gap: 16,
          marginBottom: 32,
        }}>
          <div style={{ fontSize: 32 }}>🏆</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text)" }}>Most Improved</div>
            <div style={{ color: "var(--brand)", fontWeight: 800, fontSize: 18 }}>
              {fmt(data.most_improved_pose)}
            </div>
          </div>
        </div>
      )}

      {/* Filter + history */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
        <h2 style={{ fontSize: 20, fontWeight: 800 }}>Session History</h2>
        <div style={{
          display: "inline-flex", background: "var(--bg-2)",
          borderRadius: "var(--r-sm)", padding: 3, gap: 2,
          border: "1px solid var(--border)",
        }}>
          {["all", "gym", "yoga"].map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "7px 16px", borderRadius: "calc(var(--r-sm) - 1px)",
              border: "none", cursor: "pointer",
              background: filter === f ? "var(--bg-3)" : "transparent",
              color: filter === f ? "var(--text)" : "var(--text-3)",
              fontWeight: 600, fontSize: 13,
              transition: "all 0.15s ease",
            }}>
              {f === "all" ? "All" : f === "gym" ? "🏋️ Gym" : "🧘 Yoga"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="shimmer" style={{ height: 72, borderRadius: "var(--r-md)" }} />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 20px", color: "var(--text-3)" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🏋️</div>
          <h3 style={{ fontSize: 20, marginBottom: 8, color: "var(--text-2)" }}>No sessions yet</h3>
          <p style={{ fontSize: 14 }}>Head to Practice to start your first coached workout.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {visible.map((s) => <SessionRow key={s.id} s={s} />)}
        </div>
      )}
    </div>
  );
}

function fmt(id = "") {
  return id.split(/[_\s]+/).map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}
