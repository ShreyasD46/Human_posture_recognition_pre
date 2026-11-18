import { useEffect, useRef } from "react";
import { usePoseDetection } from "../hooks/usePoseDetection.js";

const CONNECTIONS = [
  [11,12],[11,13],[13,15],[12,14],[14,16],
  [11,23],[12,24],[23,24],
  [23,25],[25,27],[24,26],[26,28],
];

const FRAME_MS = 1000 / 20; // 20 FPS

export default function CameraView({
  onFrame, statusColor,
  perJoint, jointColors,
  ghostLandmarks, problemJoints,
  feedbackCue, refinedLandmarks,
}) {
  const videoRef  = useRef(null);
  const canvasRef = useRef(null);
  const rafRef    = useRef(null);
  const lastSent  = useRef(0);
  const { ready, error, detect, isFullyVisible } = usePoseDetection();

  /* Camera init */
  useEffect(() => {
    let stream;
    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        });
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch {
        onFrame?.(null, false, "camera-denied");
      }
    })();
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, []);

  /* Render loop */
  useEffect(() => {
    if (!ready) return;
    const loop = (t) => {
      const video  = videoRef.current;
      const canvas = canvasRef.current;
      if (video && canvas && video.readyState >= 2) {
        const rawLm  = detect(video);
        const dispLm = refinedLandmarks ?? rawLm;
        draw(canvas, video, dispLm, ghostLandmarks, jointColors, problemJoints, feedbackCue, statusColor);
        const visible = isFullyVisible(rawLm);
        if (t - lastSent.current >= FRAME_MS) {
          lastSent.current = t;
          onFrame?.(
            rawLm ? rawLm.map((lm) => ({ x: lm.x, y: lm.y, z: lm.z ?? 0, visibility: lm.visibility ?? 1 })) : null,
            visible, null, t
          );
        }
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, [ready, statusColor, perJoint, jointColors, ghostLandmarks, problemJoints, feedbackCue, refinedLandmarks]);

  return (
    <div style={{
      position: "relative",
      width: "100%",
      aspectRatio: "4/3",
      borderRadius: "var(--r-xl)",
      overflow: "hidden",
      background: "var(--bg-1)",
      border: "1px solid var(--border)",
      boxShadow: "var(--shadow-lg)",
    }}>
      <video
        ref={videoRef} autoPlay playsInline muted
        style={{
          position: "absolute", inset: 0,
          width: "100%", height: "100%",
          objectFit: "cover",
          transform: "scaleX(-1)",
        }}
      />
      <canvas
        ref={canvasRef}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}
      />

      {/* Loading overlay */}
      {!ready && !error && (
        <div style={overlayStyle}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 40, marginBottom: 12, animation: "pulse-dot 1.5s ease infinite" }}>⚡</div>
            <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text-2)" }}>
              Initializing AI Vision Engine…
            </div>
          </div>
        </div>
      )}
      {error && (
        <div style={overlayStyle}>
          <div style={{ color: "var(--red)", fontWeight: 600 }}>{error}</div>
        </div>
      )}
    </div>
  );
}

const overlayStyle = {
  position: "absolute", inset: 0,
  display: "flex", alignItems: "center", justifyContent: "center",
  background: "rgba(9,9,11,0.88)",
  backdropFilter: "blur(8px)",
  padding: 20,
};

/* ── Canvas drawing ── */
function draw(canvas, video, landmarks, ghost, jointColors, problemJoints, cue, statusColor) {
  const ctx = canvas.getContext("2d");
  const w   = canvas.width  = video.clientWidth;
  const h   = canvas.height = video.clientHeight;
  ctx.clearRect(0, 0, w, h);
  if (!landmarks) return;

  ctx.save();
  ctx.translate(w, 0);
  ctx.scale(-1, 1); // mirror to match video

  /* 1. Ghost skeleton (ideal reference form) */
  if (ghost?.length >= 29) {
    ctx.save();
    ctx.globalAlpha = 0.55;
    ctx.strokeStyle = "#22d3ee";
    ctx.lineWidth   = 3;
    ctx.setLineDash([9, 7]);
    CONNECTIONS.forEach(([a, b]) => {
      const g1 = ghost[a], g2 = ghost[b];
      if (!g1 || !g2) return;
      ctx.beginPath();
      ctx.moveTo(g1.x * w, g1.y * h);
      ctx.lineTo(g2.x * w, g2.y * h);
      ctx.stroke();
    });
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(34,211,238,0.8)";
    [11,12,13,14,15,16,23,24,25,26,27,28].forEach((i) => {
      const g = ghost[i];
      if (!g) return;
      ctx.beginPath();
      ctx.arc(g.x * w, g.y * h, 4, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();
  }

  /* 2. User skeleton — color-coded bones */
  CONNECTIONS.forEach(([a, b]) => {
    const p1 = landmarks[a], p2 = landmarks[b];
    if (!p1 || !p2) return;
    ctx.beginPath();
    ctx.moveTo(p1.x * w, p1.y * h);
    ctx.lineTo(p2.x * w, p2.y * h);
    ctx.strokeStyle = statusColor ?? "#6366f1";
    ctx.lineWidth   = 4.5;
    ctx.stroke();
  });

  /* 3. Joint dots */
  const KEY_JOINTS = [11,12,13,14,15,16,23,24,25,26,27,28];
  KEY_JOINTS.forEach((i) => {
    const p = landmarks[i];
    if (!p) return;
    let col = "#22c55e";
    if (jointColors) {
      const v = jointColors[i] ?? jointColors[Object.keys(jointColors)[0]];
      if (v === "red")   col = "#ef4444";
      else if (v === "amber") col = "#f59e0b";
    }
    ctx.beginPath();
    ctx.arc(p.x * w, p.y * h, 6.5, 0, Math.PI * 2);
    ctx.fillStyle = col;
    ctx.fill();
    ctx.lineWidth   = 2.5;
    ctx.strokeStyle = "rgba(255,255,255,0.9)";
    ctx.stroke();
  });

  ctx.restore(); // end mirror

  /* 4. Problem joint callouts (in normal space — already mirrored by canvas) */
  if (problemJoints && Object.keys(problemJoints).length > 0) {
    let yOff = 44;
    ctx.font = "bold 14px 'Inter', system-ui";
    Object.entries(problemJoints).forEach(([name, info]) => {
      const text = `${name.replace(/_/g, " ")}: ${info.measured}° → ${info.ideal}°`;
      const tw   = ctx.measureText(text).width + 24;
      const col  = info.severity === "major" ? "#ef4444" : "#f59e0b";
      ctx.fillStyle = "rgba(9,9,11,0.88)";
      ctx.beginPath();
      ctx.roundRect(12, yOff - 20, tw, 30, 6);
      ctx.fill();
      ctx.fillStyle = col;
      ctx.fillText(text, 24, yOff);
      yOff += 40;
    });
  }

  /* 5. Ghost badge */
  if (ghost?.length > 0) {
    const label = "--- Ghost Reference";
    ctx.font      = "600 12px 'Inter', system-ui";
    const tw      = ctx.measureText(label).width + 24;
    ctx.fillStyle = "rgba(9,9,11,0.82)";
    ctx.beginPath();
    ctx.roundRect(w - tw - 12, 12, tw, 28, 6);
    ctx.fill();
    ctx.fillStyle = "#22d3ee";
    ctx.fillText(label, w - tw - 2, 31);
  }
}
