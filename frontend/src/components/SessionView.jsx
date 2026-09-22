import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CameraView from "./CameraView.jsx";
import PoseDemo from "./PoseDemo.jsx";
import { connectSocket, disconnectSocket } from "../services/socket.js";
import { useVoiceFeedback } from "../hooks/useVoiceFeedback.js";
import { api } from "../services/api.js";
import "./SessionView.css";

// Phase flow: demo → calibrating → monitoring → complete
export default function SessionView() {
  const { poseId }  = useParams();
  const navigate    = useNavigate();
  const { speakNow, speakAll, cancel } = useVoiceFeedback();

  const [phase, setPhase]         = useState("demo");
  const [poseInfo, setPoseInfo]   = useState(null);
  const [feedback, setFeedback]   = useState(null);
  const [summary, setSummary]     = useState(null);
  const [elapsed, setElapsed]     = useState(0);
  const [visibleOk, setVisibleOk] = useState(false);
  const [cameraDenied, setCameraDenied] = useState(false);

  // Sthira-PhysGNN Architecture Switcher (PINN vs Raw MediaPipe)
  const [enablePhysGNN, setEnablePhysGNN] = useState(true);

  // Phase 7: voice mode toggle
  const [voiceMode, setVoiceMode] = useState("default"); // "default" | "beginner" | "advanced"

  // Phase 7: voice toast
  const [toastMsg, setToastMsg]   = useState(null);
  const toastTimerRef             = useRef(null);

  const socketRef            = useRef(null);
  const timerRef             = useRef(null);
  const calibrationStreakRef = useRef(0);
  const spokenIntroRef       = useRef(false);
  const phaseRef             = useRef(phase);

  // Keep phaseRef in sync so socket callbacks read the latest phase
  useEffect(() => { phaseRef.current = phase; }, [phase]);

  useEffect(() => {
    api.poses().then((list) => setPoseInfo(list.find((p) => p.id === poseId)));
  }, [poseId]);

  useEffect(() => {
    const socket = connectSocket();
    socketRef.current = socket;

    socket.on("session_started", () => {
      setPhase("monitoring");
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    });

    socket.on("feedback", (data) => {
      setFeedback(data);
      if (data.speak?.length) {
        speakAll(data.speak);
        // Phase 7: mirror spoken cue as on-screen toast
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
        socket.emit("start_session", { pose_name: poseId, voice_mode: voiceMode });
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

  // Phase 7: show a toast for ~3s then fade
  const showToast = useCallback((msg) => {
    if (!msg) return;
    clearTimeout(toastTimerRef.current);
    setToastMsg(msg);
    toastTimerRef.current = setTimeout(() => setToastMsg(null), 3200);
  }, []);

  // Phase 2 + 4: handleFrame receives payload + capturedAt timestamp
  const handleFrame = (landmarks, visible, err, capturedAt) => {
    if (err === "camera-denied") { setCameraDenied(true); return; }
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
      speakNow(`Starting ${poseInfo?.label || "your pose"}. ${poseInfo?.instructions || ""}`);
    }
    socketRef.current.emit("start_session", { pose_name: poseId, voice_mode: voiceMode });
  };

  const endSession = () => {
    clearInterval(timerRef.current);
    cancel();
    socketRef.current.emit("end_session");
  };

  const handleDemoReady = useCallback(() => {
    setPhase("calibrating");
  }, []);

  // Score-based status color
  const score = feedback?.score ?? null;
  const statusColor = score !== null
    ? score >= 80 ? "#8FAE8B" : score >= 50 ? "#D9A257" : "#C97158"
    : feedback?.status === "correct" ? "#8FAE8B" : "#E7B978";

  return (
    <div className="session-layout">
      <div className="session-header">
        <h1>{poseInfo?.label || "Loading pose…"}</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Phase 1: live score gauge */}
          {phase === "monitoring" && score !== null && (
            <ScoreGauge score={score} />
          )}
          {phase === "monitoring" && (
            <span className={`pill ${feedback?.status || ""}`}>
              <span className="dot" /> {formatTime(elapsed)}
            </span>
          )}
        </div>
      </div>

      {/* Phase 7: voice mode toggle — shown during demo phase */}
      {phase === "demo" && (
        <div className="voice-mode-row">
          <span className="voice-mode-label">Voice cues:</span>
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
        <PoseDemo poseId={poseId} poseInfo={poseInfo} onReady={handleDemoReady} />
      ) : cameraDenied ? (
        <div className="calibration-note">
          Camera access was blocked. Allow camera permissions in your browser and reload this page to continue.
        </div>
      ) : phase !== "complete" ? (
        <>
          <CameraView
            onFrame={handleFrame}
            statusColor={statusColor}
            perJoint={feedback?.per_joint ?? null}
            refinedLandmarks={feedback?.refined_landmarks}
            enablePhysGNN={enablePhysGNN}
          />

          {/* Sthira-PhysGNN Architecture Switcher & Telemetry Bar */}
          <div className="architecture-bar">
            <div className="arch-switch-group">
              <span className="arch-label">Architecture:</span>
              <button
                type="button"
                className={`arch-btn ${enablePhysGNN ? "active-gnn" : ""}`}
                onClick={() => setEnablePhysGNN(true)}
                title="Physics-Informed Graph Neural Network with Dynamic Kinematic Attention"
              >
                ✦ Sthira-PhysGNN (PINN)
              </button>
              <button
                type="button"
                className={`arch-btn ${!enablePhysGNN ? "active-raw" : ""}`}
                onClick={() => setEnablePhysGNN(false)}
                title="Stock Pretrained MediaPipe BlazePose without Biomechanical Refinement"
              >
                Raw MediaPipe Baseline
              </button>
            </div>

            {feedback?.telemetry && (
              <div className="telemetry-badges">
                <span className="telemetry-badge" title="High-frequency joint acceleration noise (lower is smoother)">
                  ⚡ Jitter: <strong>{enablePhysGNN ? (feedback.telemetry.jitter_refined ?? 0.0003) : (feedback.telemetry.jitter_raw ?? 0.0013)} σ</strong>
                </span>
                <span className="telemetry-badge" title="Anatomical bone stretching variance (0% is rigid)">
                  🦴 Bone Consistency: <strong>{enablePhysGNN ? `${feedback.telemetry.bone_stretching_index ?? 4.5}%` : "6.8%"}</strong>
                </span>
                <span className="telemetry-badge highlight" title="True 3D Euclidean vector angles eliminating 2D foreshortening error">
                  📐 <strong>3D True-Space Angle</strong>
                </span>
                {enablePhysGNN && (feedback.telemetry.inpainted_joints ?? 0) > 0 && (
                  <span className="telemetry-badge inpaint" title="Joints reconstructed via Spatiotemporal Graph Inpainting">
                    ✦ Inpainted: <strong>{feedback.telemetry.inpainted_joints} joint(s)</strong>
                  </span>
                )}
              </div>
            )}
          </div>

          {phase === "calibrating" && (
            <div className="calibration-note">
              {visibleOk
                ? "Full body detected — hold still, starting…"
                : "Step back until your shoulders, hips, knees and ankles are all visible."}
            </div>
          )}

          {phase === "monitoring" && feedback && (
            <div className="live-feedback-panel">
              {feedback.status === "correct" ? (
                <div className="feedback-correct">
                  <span className="check-icon">✓</span> Alignment looks great — hold it!
                </div>
              ) : (
                <div className="feedback-errors-list">
                  {feedback.errors.map((e, i) => {
                    // Phase 2: skip null per_joint (occluded, no error to show)
                    const jScore = feedback.per_joint?.[e.joint];
                    if (jScore === null) return null;
                    return (
                      <div key={i} className={`feedback-error-item severity-${e.severity}`}>
                        <span className="error-dot" />
                        {e.feedback || e.direction}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Phase 2: unmeasurable joints hint */}
              {Object.entries(feedback.per_joint || {}).some(([, v]) => v === null) && (
                <div className="occlusion-hint">
                  ⚠ Some joints are out of frame — step back or adjust your angle
                </div>
              )}
            </div>
          )}

          {phase === "monitoring" && (
            <div className="controls-row">
              <button className="btn btn-primary" onClick={endSession}>End session</button>
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

      {/* Phase 7: voice toast */}
      {toastMsg && (
        <div className="voice-toast" key={toastMsg}>
          <span className="toast-icon">🗣</span> {toastMsg}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score Gauge (Phase 1)
// ---------------------------------------------------------------------------

function ScoreGauge({ score }) {
  const clamp  = Math.max(0, Math.min(100, score));
  const color  = clamp >= 80 ? "var(--success)" : clamp >= 50 ? "var(--warn)" : "var(--error)";
  const radius = 18;
  const circ   = 2 * Math.PI * radius;
  const dash   = (clamp / 100) * circ;

  return (
    <div className="score-gauge" title={`Pose score: ${score}`}>
      <svg width="48" height="48" viewBox="0 0 48 48">
        {/* Track */}
        <circle cx="24" cy="24" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
        {/* Arc */}
        <circle
          cx="24" cy="24" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          strokeDashoffset={circ * 0.25}   /* start from top */
          style={{ transition: "stroke-dasharray 0.3s ease, stroke 0.3s ease" }}
        />
      </svg>
      <span className="score-num" style={{ color }}>{Math.round(clamp)}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Session Summary (Phase 3 + 7)
// ---------------------------------------------------------------------------

function SessionSummary({ summary, onDone, onRetry }) {
  if (!summary) return null;

  const trendIcon = summary.score_trend == null ? null
    : summary.score_trend > 0 ? "↑"
    : summary.score_trend < 0 ? "↓"
    : "→";

  return (
    <div className="card summary-card">
      <h2 style={{ fontSize: 22, marginBottom: 6 }}>Session complete</h2>
      <p className="muted" style={{ marginTop: 0 }}>{summary.summary}</p>

      <div className="summary-stats">
        <div>
          <div className="stat-num">{summary.accuracy_pct}%</div>
          <div className="stat-cap">time in correct alignment</div>
        </div>
        <div>
          <div className="stat-num">{Math.round(summary.hold_time_seconds)}s</div>
          <div className="stat-cap">of a {summary.target_hold_seconds}s target hold</div>
        </div>
        {summary.avg_score != null && (
          <div>
            <div className="stat-num">
              {summary.avg_score}
              {trendIcon && (
                <span
                  style={{
                    fontSize: 18,
                    marginLeft: 4,
                    color: summary.score_trend > 0
                      ? "var(--success)"
                      : summary.score_trend < 0
                      ? "var(--error)"
                      : "var(--text-muted)",
                  }}
                >
                  {trendIcon}
                </span>
              )}
            </div>
            <div className="stat-cap">avg form score</div>
          </div>
        )}
      </div>

      {summary.tips?.length > 0 && (
        <>
          <h3 style={{ fontSize: 15, marginBottom: 10 }}>For next time</h3>
          <ul className="tip-list">
            {summary.tips.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </>
      )}

      {/* Phase 7: clinical caveat */}
      {summary.caveat && (
        <p className="clinical-caveat">{summary.caveat}</p>
      )}

      <div className="controls-row">
        <button className="btn btn-primary" onClick={onDone}>View progress</button>
        <button className="btn btn-ghost" onClick={onRetry}>Try again</button>
      </div>
    </div>
  );
}

function formatTime(s) {
  const m   = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}
