import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function PosePicker() {
  const [exercises, setExercises] = useState([]);
  const [category, setCategory] = useState("all"); // "all" | "gym" | "yoga"
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.exercises()
      .then((data) => {
        if (data && data.length > 0) {
          setExercises(data);
        } else {
          // Fallback to poses if exercises endpoint empty
          api.poses().then((pList) => {
            setExercises(pList.map(p => ({
              id: p.id,
              name: p.label,
              category: "yoga",
              instructions: p.instructions,
              hold_time_target: p.hold_time_target,
              camera_view: "front"
            })));
          });
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  const filtered = exercises.filter((ex) => {
    const matchCat = category === "all" || ex.category.toLowerCase() === category.toLowerCase();
    const matchSearch =
      !search ||
      ex.name.toLowerCase().includes(search.toLowerCase()) ||
      (ex.muscle_groups && ex.muscle_groups.some((m) => m.toLowerCase().includes(search.toLowerCase())));
    return matchCat && matchSearch;
  });

  return (
    <div className="page" style={{ paddingTop: 30, maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 34, fontWeight: 800, margin: "0 0 8px 0", letterSpacing: "-0.5px" }}>
            Exercise & Pose Library
          </h1>
          <p className="muted" style={{ margin: 0, fontSize: 16 }}>
            Select an exercise to calibrate camera and launch your coaching session.
          </p>
        </div>
      </div>

      {/* Category Pills & Search */}
      <div style={{ display: "flex", gap: 14, marginBottom: 28, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ display: "inline-flex", background: "rgba(255,255,255,0.06)", borderRadius: 12, padding: 4 }}>
          {["all", "gym", "yoga"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              style={{
                background: category === cat ? "var(--accent-soft, #E7B978)" : "transparent",
                color: category === cat ? "#0F172A" : "var(--text-muted)",
                border: "none",
                borderRadius: 9,
                padding: "8px 20px",
                fontWeight: 700,
                fontSize: 14,
                cursor: "pointer",
                textTransform: "capitalize",
                transition: "all 0.2s ease",
              }}
            >
              {cat === "all" ? "All Exercises" : cat === "gym" ? "🏋️ Gym Training" : "🧘 Yoga Postures"}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Search by name or muscle (e.g. chest, biceps, knee)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            minWidth: 260,
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            padding: "10px 18px",
            color: "#FFF",
            fontSize: 14,
            outline: "none",
          }}
        />
      </div>

      {error && <p style={{ color: "var(--error)", marginBottom: 16 }}>{error}</p>}

      {/* Exercise Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 20,
        }}
      >
        {filtered.map((item) => (
          <button
            key={item.id}
            className="card"
            style={{
              textAlign: "left",
              color: "var(--text)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              padding: 22,
              borderRadius: 16,
              background: "rgba(18, 30, 24, 0.7)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "transform 0.15s ease, border-color 0.15s ease",
            }}
            onClick={() => navigate(`/session/${item.id}`)}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                <span
                  style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    fontWeight: 800,
                    letterSpacing: "0.8px",
                    color: item.category === "gym" ? "#60A5FA" : "#34D399",
                    background: item.category === "gym" ? "rgba(96,165,250,0.15)" : "rgba(52,211,153,0.15)",
                    padding: "3px 8px",
                    borderRadius: 6,
                  }}
                >
                  {item.category === "gym" ? "Gym (Reps)" : "Yoga (Hold)"}
                </span>

                {item.camera_view && (
                  <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>
                    📹 {item.camera_view} View
                  </span>
                )}
              </div>

              <h3 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 10px 0" }}>{item.name}</h3>
              <p
                className="muted"
                style={{
                  fontSize: 13,
                  lineHeight: 1.5,
                  margin: 0,
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {item.instructions}
              </p>
            </div>

            <div
              style={{
                marginTop: 20,
                paddingTop: 12,
                borderTop: "1px solid rgba(255,255,255,0.06)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: 13,
              }}
            >
              {item.muscle_groups && item.muscle_groups.length > 0 ? (
                <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
                  🎯 {item.muscle_groups.slice(0, 2).join(", ")}
                </span>
              ) : (
                <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
                  ⏱️ Hold: {item.hold_time_target}s
                </span>
              )}
              <span style={{ color: "var(--accent-soft, #E7B978)", fontWeight: 700 }}>Start →</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
