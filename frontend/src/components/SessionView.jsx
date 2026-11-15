import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CameraView from "./CameraView.jsx";
import PoseDemo from "./PoseDemo.jsx";
import { connectSocket, disconnectSocket } from "../services/socket.js";
import { useVoiceFeedback } from "../hooks/useVoiceFeedback.js";
import { api } from "../services/api.js";
import "./SessionView.css";

export default function SessionView() {
  const { poseId } = useParams();
  const navigate = useNavigate();
  const { speakNow, speakAll, cancel } = useVoiceFeedback();

  const [phase, setPhase] = useState("demo"); // "demo" | "calibrating" | "monitoring" | "complete"
  const [exerciseInfo, setExerciseInfo] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [summary, setSummary] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [visibleOk, setVisibleOk] = useState(false);
  const [cameraDenied, setCameraDenied] = useState(false);
  const [category, setCategory] = useState("gym");

  // Architecture toggle
  const [enablePhysGNN, setEnablePhysGNN] = useState(true);
  const [voiceMode, setVoiceMode] = useState("default");

  const [toastMsg, setToastMsg] = useState(null);
  const toastTimerRef = useRef(null);

  const socketRef = useRef(null);
  const timerRef = useRef(null);
  const calibrationStreakRef = useRef(0);
  const spokenIntroRef = useRef(false);
  const phaseRef = useRef(phase);

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    api.exercise(poseId)
      .then((data) => {
        setExerciseInfo(data);
        if (data.category) setCategory(data.category);
      })
      .catch(() => {
        // Fallback to poses API
        api.poses().then((list) => {
          const found = list.find((p) => p.id === poseId);
          if (found) {
            setExerciseInfo(found);
            setCategory("yoga");
          }
        });
      });
  }, [poseId]);

  useEffect(() => {
    const socket = connectSocket();
    socketRef.current = socket;

    socket.on("session_started", (data) => {
      setPhase("monitoring");
      if (data?.category) setCategory(data.category);
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    });

    socket.on("feedback", (data) => {
      setFeedback(data);
      if (data.speak?.length) {
        speakAll(data.speak);
        showToast(data.speak[0]);
      }
    });

    socket.on("session_summary", (data) => {
      setSummary(data);
      setPhase("complete");
    });

    socket.on("session_error", (data) => console.warn(data.message));

    socket.on("reconnect", () => {
      if (phaseRef.current === "monitoring") {
        socket.emit("start_session", { exercise_id: poseId, pose_name: poseId, voice_mode: voiceMode });
      }
    });

    return () => {
      clearInterval(timerRef.current);
      cancel();
      socket.off("session_started");
      socket.off("feedback");
      socket.off("session_summary");
      socket.off("session_error");
      socket.off("reconnect");
      disconnectSocket();
    };
  }, []);

  const showToast = useCallback((msg) => {
    if (!msg) return;
    clearTimeout(toastTimerRef.current);
    setToastMsg(msg);
    toastTimerRef.current = setTimeout(() => setToastMsg(null), 3200);
  }, []);

  const handleFrame = (landmarks, visible, err, capturedAt) => {
    if (err === "camera-denied") {
      setCameraDenied(true);
      return;
    }
    setVisibleOk(visible);

    if (phaseRef.current === "calibrating") {
      calibrationStreakRef.current = visible ? calibrationStreakRef.current + 1 : 0;
      if (calibrationStreakRef.current >= 20) {
        startSession();
      }
      return;
    }

    if (phaseRef.current === "monitoring" && landmarks) {
      socketRef.current.emit("frame", { landmarks, capturedAt, enable_physgnn: enablePhysGNN });
    }
  };

  const startSession = () => {
    if (!spokenIntroRef.current) {
      spokenIntroRef.current = true;
      const title = exerciseInfo?.name || exerciseInfo?.label || "your workout";
      speakNow(`Starting ${title}. Maintain steady form and follow the reference ghost.`);
    }
    socketRef.current.emit("start_session", {
      exercise_id: poseId,
      pose_name: poseId,
      voice_mode: voiceMode,
    });
  };

  const endSession = () => {
    clearInterval(timerRef.current);
    cancel();
    socketRef.current.emit("end_session");
  };

  const handleDemoReady = useCallback(() => {
    setPhase("calibrating");
  }, []);

  const score = feedback?.score ?? null;
  const statusColor =
    score !== null
      ? score >= 80
        ? "#8FAE8B"
        : score >= 50
        ? "#D9A257"
        : "#EF4444"
      : feedback?.status === "correct"
      ? "#8FAE8B"
      : "#E7B978";

  const isGym = category === "gym";
  const repCount = feedback?.rep_count ?? 0;
  const currentPhase = feedback?.current_phase ?? "ready";
  const isOnBreak = feedback?.is_on_break ?? false;
  const breakSecondsLeft = feedback?.break_seconds_left ?? 0;

  return (
    <div className="session-layout">
      {/* Kiosk Header */}
      <div className="session-header">
        <div>
          <span
            style={{
              fontSize: 12,
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "0.8px",
              color: isGym ? "#60A5FA" : "#34D399",
              background: isGym ? "rgba(96,165,250,0.15)" : "rgba(52,211,153,0.15)",
              padding: "4px 10px",
              borderRadius: 6,
              marginRight: 8,
            }}
          >
            {isGym ? "🏋️ Gym Training" : "🧘 Yoga Posture"}
          </span>
          <h1 style={{ display: "inline-block", fontSize: 26, margin: "6px 0 0 0" }}>
            {exerciseInfo?.name || exerciseInfo?.label || "Loading exercise…"}
          </h1>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {phase === "monitoring" && score !== null && <ScoreGauge score={score} />}
          {phase === "monitoring" && (
            <span className={`pill ${feedback?.status || ""}`}>
              <span className="dot" /> {formatTime(elapsed)}
            </span>
          )}
        </div>
      </div>

      {/* Voice mode toggle */}
      {phase === "demo" && (
        <div className="voice-mode-row">
          <span className="voice-mode-label">Audio Coaching Cues:</span>
          {["beginner", "default", "advanced"].map((m) => (
            <button
              key={m}
              className={`voice-mode-btn${voiceMode === m ? " active" : ""}`}
              onClick={() => setVoiceMode(m)}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      )}

      {phase === "demo" ? (
        <PoseDemo poseId={poseId} poseInfo={exerciseInfo} onReady={handleDemoReady} />
      ) : cameraDenied ? (
        <div className="calibration-note">
          Camera access was blocked. Allow camera permissions in your browser and reload this page to continue.
        </div>
      ) : phase !== "complete" ? (
        <>
          {/* Main Dual Skeleton Camera View */}
          <CameraView
            onFrame={handleFrame}
            statusColor={statusColor}
            perJoint={feedback?.per_joint ?? null}
            jointColors={feedback?.joint_colors}
            ghostLandmarks={feedback?.ghost_landmarks}
            problemJoints={feedback?.problem_joints}
            feedbackCue={feedback?.speak?.[0]}
            refinedLandmarks={feedback?.refined_landmarks}
            enablePhysGNN={enablePhysGNN}
          />

          {/* Kiosk Workout HUD (Gym Reps vs Yoga Hold) */}
          {phase === "monitoring" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: isGym ? "repeat(4, 1fr)" : "repeat(3, 1fr)",
                gap: 12,
                marginTop: 16,
              }}
            >
              {isGym ? (
                <>
                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>REPS</div>
                    <div style={{ fontSize: 36, fontWeight: 900, color: "#38BDF8" }}>{repCount}</div>
                  </div>

                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>PHASE</div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#FCD34D", marginTop: 8, textTransform: "uppercase" }}>
                      {currentPhase}
                    </div>
                  </div>

                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>FORM SCORE</div>
                    <div style={{ fontSize: 36, fontWeight: 900, color: score >= 80 ? "#34D399" : score >= 50 ? "#FBBF24" : "#F87171" }}>
                      {score ? Math.round(score) : "--"}
                    </div>
                  </div>

                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>STATUS</div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: isOnBreak ? "#F87171" : "#34D399", marginTop: 8 }}>
                      {isOnBreak ? `Rest: ${breakSecondsLeft}s` : "ACTIVE"}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>HOLD TIME</div>
                    <div style={{ fontSize: 36, fontWeight: 900, color: "#34D399" }}>
                      {Math.round(feedback?.good_hold_seconds ?? elapsed)}s
                    </div>
                  </div>

                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>BREATH</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: "#38BDF8", marginTop: 6, textTransform: "capitalize" }}>
                      {feedback?.breath_phase || "Breathe Steady"}
                    </div>
                  </div>

                  <div className="card" style={{ padding: 14, textAlign: "center", background: "rgba(15,23,42,0.7)" }}>
                    <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, textTransform: "uppercase" }}>ALIGNMENT</div>
                    <div style={{ fontSize: 36, fontWeight: 900, color: score >= 80 ? "#34D399" : "#FBBF24" }}>
                      {score ? `${Math.round(score)}%` : "--"}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {phase === "calibrating" && (
            <div className="calibration-note" style={{ fontSize: 18, padding: 24 }}>
              {visibleOk
                ? "✓ Full body locked! Stand steady, starting workout in 3… 2… 1…"
                : exerciseInfo?.camera_view === "side"
                ? "Turn sideways to the camera until your full side profile is in frame."
                : "Step back until your shoulders, hips, knees and ankles are all visible in frame."}
            </div>
          )}

          {phase === "monitoring" && feedback?.errors?.length > 0 && (
            <div className="live-feedback-panel" style={{ marginTop: 14 }}>
              <div className="feedback-errors-list">
                {feedback.errors.map((e, i) => (
                  <div key={i} className={`feedback-error-item severity-${e.severity}`}>
                    <span className="error-dot" />
                    {e.feedback || e.direction}
                  </div>
                ))}
              </div>
            </div>
          )}

          {phase === "monitoring" && (
            <div className="controls-row" style={{ marginTop: 20 }}>
              <button className="btn btn-primary" style={{ padding: "14px 40px", fontSize: 16 }} onClick={endSession}>
                Complete Workout
              </button>
            </div>
          )}
        </>
      ) : (
        <SessionSummary
          summary={summary}
          onDone={() => navigate("/dashboard")}
          onRetry={() => window.location.reload()}
        />
      )}

      {toastMsg && (
        <div className="voice-toast" key={toastMsg}>
          <span className="toast-icon">🗣</span> {toastMsg}
        </div>
      )}
    </div>
  );
}

function ScoreGauge({ score }) {
  const clamp = Math.max(0, Math.min(100, score));
  const color = clamp >= 80 ? "#34D399" : clamp >= 50 ? "#FBBF24" : "#EF4444";
  const radius = 18;
  const circ = 2 * Math.PI * radius;
  const dash = (clamp / 100) * circ;

  return (
    <div className="score-gauge" title={`Pose score: ${score}`}>
      <svg width="48" height="48" viewBox="0 0 48 48">
        <circle cx="24" cy="24" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          strokeDashoffset={circ * 0.25}
          style={{ transition: "stroke-dasharray 0.3s ease, stroke 0.3s ease" }}
        />
      </svg>
      <span className="score-num" style={{ color }}>
        {Math.round(clamp)}
      </span>
    </div>
  );
}

function SessionSummary({ summary, onDone, onRetry }) {
  if (!summary) return null;

  const isGym = summary.category === "gym";

  return (
    <div className="card summary-card" style={{ maxWidth: 700, margin: "0 auto", padding: 32 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: 28, margin: 0 }}>Workout Complete! 🏅</h2>
        <span
          style={{
            background: isGym ? "rgba(96,165,250,0.2)" : "rgba(52,211,153,0.2)",
            color: isGym ? "#60A5FA" : "#34D399",
            fontWeight: 800,
            fontSize: 12,
            textTransform: "uppercase",
            padding: "4px 12px",
            borderRadius: 8,
          }}
        >
          {isGym ? "Gym Workout" : "Yoga Session"}
        </span>
      </div>

      <p className="muted" style={{ fontSize: 16, lineHeight: 1.6, marginBottom: 24 }}>
        {summary.summary}
      </p>

      <div className="summary-stats" style={{ marginBottom: 28 }}>
        {isGym ? (
          <div>
            <div className="stat-num" style={{ color: "#38BDF8" }}>{summary.total_reps || 0}</div>
            <div className="stat-cap">Total Reps Completed</div>
          </div>
        ) : (
          <div>
            <div className="stat-num" style={{ color: "#34D399" }}>{Math.round(summary.hold_time_seconds || 0)}s</div>
            <div className="stat-cap">of a {summary.target_hold_seconds}s target hold</div>
          </div>
        )}

        <div>
          <div className="stat-num" style={{ color: summary.avg_score >= 80 ? "#34D399" : "#FBBF24" }}>
            {summary.avg_score || summary.accuracy_pct || 0}
          </div>
          <div className="stat-cap">Average Form Score</div>
        </div>

        <div>
          <div className="stat-num" style={{ color: "#A78BFA" }}>
            {summary.score_trend > 0 ? `+${summary.score_trend}` : summary.score_trend || "Stable"}
          </div>
          <div className="stat-cap">Session Momentum</div>
        </div>
      </div>

      {summary.tips?.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 17, marginBottom: 12 }}>AI Coach Recommendations:</h3>
          <ul className="tip-list">
            {summary.tips.map((t, i) => (
              <li key={i} style={{ fontSize: 15, lineHeight: 1.5 }}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.caveat && (
        <p className="clinical-caveat" style={{ fontSize: 12, opacity: 0.75, marginBottom: 24 }}>
          {summary.caveat}
        </p>
      )}

      <div className="controls-row">
        <button className="btn btn-primary" onClick={onDone} style={{ padding: "12px 30px" }}>
          View History & PBs
        </button>
        <button className="btn btn-ghost" onClick={onRetry} style={{ padding: "12px 24px" }}>
          Do Another Set
        </button>
      </div>
    </div>
  );
}

function formatTime(s) {
  const m = Math.floor(s / 60)
    .toString()
    .padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}
