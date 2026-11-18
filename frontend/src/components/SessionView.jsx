import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CameraView from "./CameraView.jsx";
import PoseDemo from "./PoseDemo.jsx";
import { connectSocket, disconnectSocket } from "../services/socket.js";
import { useVoiceFeedback } from "../hooks/useVoiceFeedback.js";
import { api } from "../services/api.js";
import "./SessionView.css";

/* ── Score ring ──────────────────────────────────────── */
function ScoreRing({ score }) {
  const clamp  = Math.max(0, Math.min(100, score ?? 0));
  const color  = clamp >= 80 ? "var(--green)" : clamp >= 50 ? "var(--amber)" : "var(--red)";
  const r      = 22;
  const circ   = 2 * Math.PI * r;
  const filled = (clamp / 100) * circ;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <svg width="56" height="56" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="5" />
        <circle
          cx="28" cy="28" r={r} fill="none"
          stroke={color} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={`${filled} ${circ}`}
          strokeDashoffset={circ * 0.25}
          style={{ transition: "stroke-dasharray 0.4s ease, stroke 0.4s ease" }}
        />
      </svg>
      <div>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 900, color, lineHeight: 1 }}>
          {Math.round(clamp)}
        </div>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", color: "var(--text-3)", textTransform: "uppercase" }}>
          form
        </div>
      </div>
    </div>
  );
}

/* ── HUD metric card ─────────────────────────────────── */
function HudCard({ label, value, unit, color = "var(--text)", accent, pulse }) {
  return (
    <div className="hud-card" style={{ borderColor: accent ? `${color}33` : undefined }}>
      <div className="hud-label">{label}</div>
      <div className="hud-value" style={{ color, fontSize: typeof value === "string" && value.length > 5 ? 28 : 44 }}>
        {pulse ? (
          <span style={{ animation: "pulse-dot 1.5s ease infinite", display: "inline-block" }}>{value}</span>
        ) : value}
        {unit && <span style={{ fontSize: 18, fontWeight: 500, color: "var(--text-3)", marginLeft: 4 }}>{unit}</span>}
      </div>
    </div>
  );
}

/* ── Session summary screen ──────────────────────────── */
function SessionSummary({ summary, onDone, onRetry }) {
  if (!summary) return null;
  const isGym = summary.category === "gym";
  const score = summary.avg_score ?? summary.accuracy_pct ?? 0;
  const scoreColor = score >= 80 ? "var(--green)" : score >= 50 ? "var(--amber)" : "var(--red)";

  return (
    <div style={{ maxWidth: 760, margin: "40px auto", padding: "0 20px" }}>
      <div className="card summary-card" style={{ padding: "36px 40px" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
              color: isGym ? "var(--gym)" : "var(--yoga)", marginBottom: 8 }}>
              {isGym ? "🏋️ Gym Workout" : "🧘 Yoga Session"} · Complete
            </div>
            <h2 style={{ fontSize: 32, margin: 0, fontWeight: 900 }}>Session Complete! 🏅</h2>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 48, fontWeight: 900, color: scoreColor, lineHeight: 1 }}>
              {Math.round(score)}
            </div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", color: "var(--text-3)", textTransform: "uppercase" }}>
              avg score
            </div>
          </div>
        </div>

        {/* AI summary text */}
        {summary.summary && (
          <p style={{ color: "var(--text-2)", fontSize: 16, lineHeight: 1.7, marginBottom: 28,
            padding: "16px 20px", background: "var(--bg-2)", borderRadius: "var(--r-md)", borderLeft: "3px solid var(--brand)" }}>
            {summary.summary}
          </p>
        )}

        {/* Stat grid */}
        <div className="summary-stats">
          {isGym ? (
            <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-2)", borderRadius: "var(--r-md)" }}>
              <div className="stat-num" style={{ color: "var(--gym)" }}>{summary.total_reps ?? 0}</div>
              <div className="stat-cap">Total Reps</div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-2)", borderRadius: "var(--r-md)" }}>
              <div className="stat-num" style={{ color: "var(--yoga)" }}>{Math.round(summary.hold_time_seconds ?? 0)}s</div>
              <div className="stat-cap">Hold Time</div>
            </div>
          )}
          <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-2)", borderRadius: "var(--r-md)" }}>
            <div className="stat-num" style={{ color: scoreColor }}>{Math.round(score)}%</div>
            <div className="stat-cap">Form Score</div>
          </div>
          <div style={{ textAlign: "center", padding: "16px", background: "var(--bg-2)", borderRadius: "var(--r-md)" }}>
            <div className="stat-num" style={{ color: "var(--yoga)" }}>
              {summary.score_trend > 0 ? `+${summary.score_trend}` : summary.score_trend ?? "—"}
            </div>
            <div className="stat-cap">Momentum</div>
          </div>
        </div>

        {/* Tips */}
        {summary.tips?.length > 0 && (
          <div style={{ marginBottom: 28 }}>
            <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12, color: "var(--text-2)",
              textTransform: "uppercase", letterSpacing: "0.06em", fontSize: 12 }}>
              🤖 AI Coach Recommendations
            </h3>
            <ul className="tip-list">
              {summary.tips.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          </div>
        )}

        {summary.caveat && <p className="clinical-caveat">{summary.caveat}</p>}

        {/* CTA */}
        <div className="controls-row" style={{ marginTop: 8 }}>
          <button className="btn btn-primary" onClick={onDone} style={{ flex: 1, padding: "14px" }}>
            View Progress →
          </button>
          <button className="btn btn-ghost" onClick={onRetry} style={{ flex: 1, padding: "14px" }}>
            🔁 Another Set
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main SessionView ────────────────────────────────── */
export default function SessionView() {
  const { poseId } = useParams();
  const navigate   = useNavigate();
  const { speakNow, speakAll, cancel } = useVoiceFeedback();

  const [phase, setPhase]           = useState("demo");
  const [exerciseInfo, setExerciseInfo] = useState(null);
  const [feedback, setFeedback]     = useState(null);
  const [summary, setSummary]       = useState(null);
  const [elapsed, setElapsed]       = useState(0);
  const [visibleOk, setVisibleOk]   = useState(false);
  const [cameraDenied, setCameraDenied] = useState(false);
  const [category, setCategory]     = useState("gym");
  const [voiceMode, setVoiceMode]   = useState("default");
  const [toastMsg, setToastMsg]     = useState(null);

  const socketRef           = useRef(null);
  const timerRef            = useRef(null);
  const calibrationStreakRef = useRef(0);
  const spokenIntroRef      = useRef(false);
  const phaseRef            = useRef(phase);
  const toastTimerRef       = useRef(null);

  useEffect(() => { phaseRef.current = phase; }, [phase]);

  useEffect(() => {
    api.exercise(poseId)
      .then((d) => { setExerciseInfo(d); if (d.category) setCategory(d.category); })
      .catch(() =>
        api.poses().then((list) => {
          const found = list.find((p) => p.id === poseId);
          if (found) { setExerciseInfo(found); setCategory("yoga"); }
        })
      );
  }, [poseId]);

  useEffect(() => {
    const socket = connectSocket();
    socketRef.current = socket;

    socket.on("session_started", (d) => {
      setPhase("monitoring");
      if (d?.category) setCategory(d.category);
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    });
    socket.on("feedback", (d) => {
      setFeedback(d);
      if (d.speak?.length) { speakAll(d.speak); showToast(d.speak[0]); }
    });
    socket.on("session_summary", (d) => { setSummary(d); setPhase("complete"); });
    socket.on("session_error",   (d) => console.warn(d.message));
    socket.on("reconnect", () => {
      if (phaseRef.current === "monitoring")
        socket.emit("start_session", { exercise_id: poseId, pose_name: poseId, voice_mode: voiceMode });
    });

    return () => {
      clearInterval(timerRef.current);
      cancel();
      ["session_started","feedback","session_summary","session_error","reconnect"].forEach((e) => socket.off(e));
      disconnectSocket();
    };
  }, []);

  const showToast = useCallback((msg) => {
    if (!msg) return;
    clearTimeout(toastTimerRef.current);
    setToastMsg(msg);
    toastTimerRef.current = setTimeout(() => setToastMsg(null), 3200);
  }, []);

  const handleFrame = (landmarks, visible, err) => {
    if (err === "camera-denied") { setCameraDenied(true); return; }
    setVisibleOk(visible);
    if (phaseRef.current === "calibrating") {
      calibrationStreakRef.current = visible ? calibrationStreakRef.current + 1 : 0;
      if (calibrationStreakRef.current >= 20) startSession();
      return;
    }
    if (phaseRef.current === "monitoring" && landmarks)
      socketRef.current.emit("frame", { landmarks, capturedAt: performance.now() });
  };

  const startSession = () => {
    if (!spokenIntroRef.current) {
      spokenIntroRef.current = true;
      speakNow(`Starting ${exerciseInfo?.name ?? "workout"}. Follow the ghost reference.`);
    }
    socketRef.current.emit("start_session", { exercise_id: poseId, pose_name: poseId, voice_mode: voiceMode });
  };

  const endSession = () => { clearInterval(timerRef.current); cancel(); socketRef.current.emit("end_session"); };

  /* Derived values */
  const isGym         = category === "gym";
  const score         = feedback?.score ?? null;
  const repCount      = feedback?.rep_count ?? 0;
  const currentPhase  = feedback?.current_phase ?? "ready";
  const isOnBreak     = feedback?.is_on_break ?? false;
  const breakLeft     = feedback?.break_seconds_left ?? 0;
  const holdSecs      = feedback?.good_hold_seconds ?? elapsed;
  const breathPhase   = feedback?.breath_phase ?? "Breathe steady";
  const statusColor   = score != null
    ? score >= 80 ? "var(--green)" : score >= 50 ? "var(--amber)" : "var(--red)"
    : "var(--brand)";

  /* Phase badge text */
  const phaseAccent = isGym ? "var(--gym)" : "var(--yoga)";
  const phaseDim    = isGym ? "var(--gym-dim)" : "var(--yoga-dim)";

  return (
    <div className="session-layout">

      {/* ── Header ── */}
      <div className="session-header">
        <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
          <span style={{
            background: phaseDim, color: phaseAccent,
            fontSize: 11, fontWeight: 800, letterSpacing: "0.07em", textTransform: "uppercase",
            padding: "5px 12px", borderRadius: "var(--r-full)", flexShrink: 0,
          }}>
            {isGym ? "🏋️ Gym" : "🧘 Yoga"}
          </span>
          <h1 style={{ fontSize: 20, fontWeight: 800, margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {exerciseInfo?.name ?? exerciseInfo?.label ?? "Loading…"}
          </h1>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16, flexShrink: 0 }}>
          {phase === "monitoring" && score !== null && <ScoreRing score={score} />}
          {phase === "monitoring" && (
            <div style={{
              display: "flex", alignItems: "center", gap: 7,
              background: "var(--bg-2)", border: "1px solid var(--border)",
              borderRadius: "var(--r-full)", padding: "6px 14px",
            }}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--green)", display: "inline-block",
                animation: "pulse-dot 2s ease infinite" }} />
              <span style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 700 }}>
                {formatTime(elapsed)}
              </span>
            </div>
          )}
          <button className="btn btn-ghost" onClick={() => navigate("/practice")}
            style={{ padding: "8px 16px", fontSize: 13 }}>
            ← Exit
          </button>
        </div>
      </div>

      {/* ── Voice mode row (demo phase only) ── */}
      {phase === "demo" && (
        <div className="voice-mode-row">
          <span className="voice-mode-label">Audio coaching:</span>
          {["beginner", "default", "advanced"].map((m) => (
            <button key={m} className={`voice-mode-btn${voiceMode === m ? " active" : ""}`}
              onClick={() => setVoiceMode(m)}>
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* ── Body ── */}
      {phase === "demo" ? (
        <div style={{ padding: "20px 24px" }}>
          <PoseDemo poseId={poseId} poseInfo={exerciseInfo} onReady={() => setPhase("calibrating")} />
        </div>
      ) : cameraDenied ? (
        <div style={{ padding: "40px 24px" }}>
          <div className="calibration-note" style={{ color: "var(--red)" }}>
            🚫 Camera access was blocked. Allow camera permissions in your browser and reload.
          </div>
        </div>
      ) : phase !== "complete" ? (
        <div className="session-body">

          {/* Camera feed */}
          <div>
            <CameraView
              onFrame={handleFrame}
              statusColor={statusColor}
              perJoint={feedback?.per_joint ?? null}
              jointColors={feedback?.joint_colors}
              ghostLandmarks={feedback?.ghost_landmarks}
              problemJoints={feedback?.problem_joints}
              feedbackCue={feedback?.speak?.[0]}
              refinedLandmarks={feedback?.refined_landmarks}
            />

            {/* Calibrating overlay */}
            {phase === "calibrating" && (
              <div className="calibration-note" style={{ marginTop: 14 }}>
                {visibleOk
                  ? "✅ Full body detected! Hold steady — starting in 3… 2… 1…"
                  : exerciseInfo?.camera_view === "side"
                  ? "↩️ Turn sideways to the camera until your full side profile is visible."
                  : "⬅️ Step back until your shoulders, hips, knees and ankles are all in frame."}
              </div>
            )}

            {/* Error feedback */}
            {phase === "monitoring" && feedback?.errors?.length > 0 && (
              <div className="live-feedback-panel" style={{ marginTop: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.07em", textTransform: "uppercase",
                  color: "var(--text-3)", marginBottom: 10 }}>
                  Live Corrections
                </div>
                <div className="feedback-errors-list">
                  {feedback.errors.map((e, i) => (
                    <div key={i} className={`feedback-error-item severity-${e.severity ?? "minor"}`}>
                      <span className="error-dot" />
                      {e.feedback || e.direction}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* End workout button */}
            {phase === "monitoring" && (
              <div className="controls-row" style={{ marginTop: 20 }}>
                <button className="btn btn-primary" onClick={endSession}
                  style={{ flex: 1, padding: "15px", fontSize: 16 }}>
                  ✅ Complete Workout
                </button>
              </div>
            )}
          </div>

          {/* ── Sidebar HUD ── */}
          <div className="session-sidebar">
            {isGym ? (
              <>
                <HudCard label="Reps" value={repCount} color="var(--gym)" accent />
                <HudCard
                  label="Phase"
                  value={currentPhase.toUpperCase()}
                  color="var(--amber)"
                />
                <HudCard
                  label="Form Score"
                  value={score != null ? Math.round(score) : "—"}
                  unit="%"
                  color={score != null ? (score >= 80 ? "var(--green)" : score >= 50 ? "var(--amber)" : "var(--red)") : "var(--text-3)"}
                  accent
                />
                <HudCard
                  label="Status"
                  value={isOnBreak ? `Rest ${breakLeft}s` : "Active"}
                  color={isOnBreak ? "var(--red)" : "var(--green)"}
                  pulse={!isOnBreak}
                />
              </>
            ) : (
              <>
                <HudCard label="Hold Time" value={Math.round(holdSecs)} unit="s" color="var(--yoga)" accent />
                <HudCard label="Breath" value={breathPhase} color="var(--cyan)" />
                <HudCard
                  label="Alignment"
                  value={score != null ? Math.round(score) : "—"}
                  unit="%"
                  color={score != null ? (score >= 80 ? "var(--green)" : "var(--amber)") : "var(--text-3)"}
                  accent
                />
              </>
            )}

            {/* Timer card */}
            {phase === "monitoring" && (
              <div className="hud-card" style={{ background: "var(--bg-2)" }}>
                <div className="hud-label">Session Time</div>
                <div style={{
                  fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 800,
                  letterSpacing: "0.04em", color: "var(--text-2)",
                }}>
                  {formatTime(elapsed)}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <SessionSummary
          summary={summary}
          onDone={() => navigate("/dashboard")}
          onRetry={() => window.location.reload()}
        />
      )}

      {/* Voice toast */}
      {toastMsg && (
        <div className="voice-toast" key={toastMsg}>
          <span className="toast-icon">🗣</span>
          {toastMsg}
        </div>
      )}
    </div>
  );
}

function formatTime(s) {
  return `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;
}
