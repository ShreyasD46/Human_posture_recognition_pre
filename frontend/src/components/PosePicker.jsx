import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

const DIFF_COLOR = { beginner: "#22c55e", intermediate: "#f59e0b", advanced: "#ef4444" };
const DIFF_LABEL = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" };

const CAT_EMOJI = { gym: "🏋️", yoga: "🧘" };
const MUSCLES_EMOJI = {
  chest: "💪", back: "🏃", shoulders: "🙆", arms: "💪", biceps: "💪",
  legs: "🦵", glutes: "🍑", core: "⚡", balance: "🎯", flexibility: "🌊", mindfulness: "🧠",
};

function getMuscleEmoji(m) {
  const key = Object.keys(MUSCLES_EMOJI).find((k) => m.toLowerCase().includes(k));
  return key ? MUSCLES_EMOJI[key] : "🎯";
}

function ExerciseCardSkeleton() {
  return (
    <div style={{ background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--r-lg)", padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <div className="shimmer" style={{ width: 80, height: 22 }} />
        <div className="shimmer" style={{ width: 60, height: 22 }} />
      </div>
      <div className="shimmer" style={{ width: "70%", height: 24, marginBottom: 12 }} />
      <div className="shimmer" style={{ width: "100%", height: 14, marginBottom: 8 }} />
      <div className="shimmer" style={{ width: "80%", height: 14, marginBottom: 24 }} />
      <div style={{ display: "flex", gap: 8 }}>
        <div className="shimmer" style={{ width: 60, height: 20, borderRadius: 999 }} />
        <div className="shimmer" style={{ width: 60, height: 20, borderRadius: 999 }} />
      </div>
    </div>
  );
}

function ExerciseCard({ item, onClick }) {
  const [hovered, setHovered] = useState(false);
  const isGym = item.category === "gym";
  const accent = isGym ? "var(--gym)" : "var(--yoga)";
  const accentDim = isGym ? "var(--gym-dim)" : "var(--yoga-dim)";
  const diff = item.difficulty || "intermediate";

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        all: "unset",
        display: "flex",
        flexDirection: "column",
        background: hovered ? "var(--bg-2)" : "var(--bg-1)",
        border: `1px solid ${hovered ? "var(--border-hover)" : "var(--border)"}`,
        borderRadius: "var(--r-lg)",
        padding: 24,
        cursor: "pointer",
        transition: "all 0.2s var(--ease-out)",
        transform: hovered ? "translateY(-4px)" : "translateY(0)",
        boxShadow: hovered ? "var(--shadow-md)" : "none",
        textAlign: "left",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Top accent bar */}
      <div style={{
        position: "absolute",
        top: 0, left: 0, right: 0,
        height: 2,
        background: hovered ? accent : "transparent",
        transition: "background 0.2s ease",
        borderRadius: "var(--r-lg) var(--r-lg) 0 0",
      }} />

      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 5,
          background: accentDim, color: accent,
          fontSize: 11, fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase",
          padding: "4px 10px", borderRadius: "var(--r-full)",
        }}>
          {CAT_EMOJI[item.category]} {isGym ? "Gym" : "Yoga"}
        </span>

        <span style={{
          fontSize: 11, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase",
          color: DIFF_COLOR[diff] || "#a1a1aa",
        }}>
          {DIFF_LABEL[diff] || diff}
        </span>
      </div>

      {/* Title */}
      <h3 style={{ fontSize: 18, fontWeight: 800, color: "var(--text)", marginBottom: 10, lineHeight: 1.3 }}>
        {item.name}
      </h3>

      {/* Instructions */}
      <p style={{
        color: "var(--text-2)", fontSize: 13, lineHeight: 1.6, margin: "0 0 20px",
        display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden",
        flex: 1,
      }}>
        {item.instructions || "No description available."}
      </p>

      {/* Muscle tags */}
      {item.muscle_groups?.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {item.muscle_groups.slice(0, 3).map((m) => (
            <span key={m} style={{
              display: "inline-flex", alignItems: "center", gap: 4,
              background: "var(--bg-3)", color: "var(--text-2)",
              fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: "var(--r-full)",
              border: "1px solid var(--border)",
            }}>
              {getMuscleEmoji(m)} {m}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        paddingTop: 14, borderTop: "1px solid var(--border)",
      }}>
        <span style={{ fontSize: 12, color: "var(--text-3)", fontWeight: 500 }}>
          {item.camera_view ? `📹 ${item.camera_view} view` : ""}
          {item.hold_time_target ? `⏱ ${item.hold_time_target}s hold` : ""}
        </span>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 4,
          color: hovered ? accent : "var(--brand)",
          fontWeight: 700, fontSize: 13,
          transition: "color 0.2s ease, transform 0.2s ease",
          transform: hovered ? "translateX(4px)" : "translateX(0)",
        }}>
          Start session →
        </span>
      </div>
    </button>
  );
}

export default function PosePicker() {
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [category, setCategory]   = useState("all");
  const [search, setSearch]       = useState("");
  const [error, setError]         = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    api.exercises()
      .then((data) => {
        if (data?.length > 0) {
          setExercises(data);
        } else {
          return api.poses().then((pList) =>
            setExercises(pList.map((p) => ({
              id: p.id, name: p.label, category: "yoga",
              instructions: p.instructions, hold_time_target: p.hold_time_target, camera_view: "front",
            })))
          );
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = exercises.filter((ex) => {
    const matchCat = category === "all" || ex.category?.toLowerCase() === category;
    const q = search.toLowerCase();
    const matchSearch = !q ||
      ex.name?.toLowerCase().includes(q) ||
      ex.muscle_groups?.some((m) => m.toLowerCase().includes(q));
    return matchCat && matchSearch;
  });

  const gymCount  = exercises.filter((e) => e.category === "gym").length;
  const yogaCount = exercises.filter((e) => e.category === "yoga").length;

  return (
    <div className="page">
      {/* Page header */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            background: "var(--brand-dim)", color: "var(--brand)",
            fontSize: 12, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
            padding: "5px 12px", borderRadius: "var(--r-full)",
          }}>
            ⚡ AI-Coached
          </span>
        </div>
        <h1 style={{ fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 800, marginBottom: 10 }}>
          Exercise Library
        </h1>
        <p className="muted" style={{ fontSize: 16 }}>
          Select an exercise — the AI coach will calibrate your camera and start your session.
        </p>
      </div>

      {/* Controls bar */}
      <div style={{
        display: "flex", gap: 12, marginBottom: 32,
        flexWrap: "wrap", alignItems: "center",
      }}>
        {/* Category pills */}
        <div style={{
          display: "inline-flex",
          background: "var(--bg-2)",
          borderRadius: "var(--r-sm)",
          padding: 4, gap: 2,
          border: "1px solid var(--border)",
        }}>
          {[
            { id: "all",  label: `All  (${exercises.length})` },
            { id: "gym",  label: `🏋️  Gym (${gymCount})` },
            { id: "yoga", label: `🧘  Yoga (${yogaCount})` },
          ].map((c) => (
            <button
              key={c.id}
              onClick={() => setCategory(c.id)}
              style={{
                padding: "8px 18px",
                borderRadius: "calc(var(--r-sm) - 2px)",
                border: "none",
                background: category === c.id ? "var(--bg-3)" : "transparent",
                color: category === c.id ? "var(--text)" : "var(--text-3)",
                fontWeight: 700, fontSize: 13,
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: category === c.id ? "var(--shadow-sm)" : "none",
                whiteSpace: "nowrap",
              }}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
          <span style={{
            position: "absolute", left: 14, top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-3)", pointerEvents: "none", fontSize: 15,
          }}>🔍</span>
          <input
            type="text"
            placeholder="Search by name or muscle (chest, bicep, knee…)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              borderRadius: "var(--r-sm)",
              padding: "10px 16px 10px 40px",
              color: "var(--text)",
              fontSize: 14,
              outline: "none",
              transition: "border-color 0.15s, box-shadow 0.15s",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "var(--brand)";
              e.target.style.boxShadow = "0 0 0 3px var(--brand-dim)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "var(--border)";
              e.target.style.boxShadow = "none";
            }}
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              style={{
                position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                background: "none", border: "none", color: "var(--text-3)", cursor: "pointer",
                fontSize: 16, padding: 0, lineHeight: 1,
              }}
            >✕</button>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: "var(--r-sm)", padding: "12px 16px",
          color: "var(--red)", fontSize: 14, marginBottom: 24,
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results count */}
      {!loading && (
        <p style={{ color: "var(--text-3)", fontSize: 13, marginBottom: 20, fontWeight: 500 }}>
          {filtered.length} exercise{filtered.length !== 1 ? "s" : ""}
          {search ? ` matching "${search}"` : ""}
          {category !== "all" ? ` in ${category}` : ""}
        </p>
      )}

      {/* Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 20,
      }}>
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <ExerciseCardSkeleton key={i} />)
          : filtered.length === 0
          ? (
            <div style={{
              gridColumn: "1 / -1", textAlign: "center",
              padding: "80px 20px", color: "var(--text-3)",
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
              <h3 style={{ fontSize: 20, marginBottom: 8, color: "var(--text-2)" }}>No exercises found</h3>
              <p style={{ fontSize: 14 }}>Try a different search term or category.</p>
            </div>
          )
          : filtered.map((item) => (
            <ExerciseCard
              key={item.id}
              item={item}
              onClick={() => navigate(`/session/${item.id}`)}
            />
          ))
        }
      </div>
    </div>
  );
}
