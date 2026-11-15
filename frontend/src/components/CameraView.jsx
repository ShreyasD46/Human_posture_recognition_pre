import { useEffect, useRef } from "react";
import { usePoseDetection } from "../hooks/usePoseDetection.js";

const CONNECTIONS = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
];
const FRAME_INTERVAL_MS = 1000 / 20; // 20 FPS high responsiveness

export default function CameraView({
  onFrame,
  statusColor,
  perJoint,
  jointColors,
  ghostLandmarks,
  problemJoints,
  feedbackCue,
  refinedLandmarks,
  enablePhysGNN = true,
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const lastSentRef = useRef(0);
  const { ready, error, detect, isFullyVisible } = usePoseDetection();

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

  useEffect(() => {
    if (!ready) return;
    const loop = (t) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (video && canvas && video.readyState >= 2) {
        const landmarks = detect(video);
        const displayLandmarks = enablePhysGNN && refinedLandmarks ? refinedLandmarks : landmarks;

        drawOverlay(
          canvas,
          video,
          displayLandmarks,
          ghostLandmarks,
          jointColors,
          problemJoints,
          feedbackCue,
          statusColor,
          perJoint
        );

        const visible = isFullyVisible(landmarks);

        if (t - lastSentRef.current >= FRAME_INTERVAL_MS) {
          lastSentRef.current = t;
          const payload = landmarks
            ? landmarks.map((lm) => ({
                x: lm.x,
                y: lm.y,
                z: lm.z ?? 0,
                visibility: lm.visibility ?? 1,
              }))
            : null;

          onFrame?.(payload, visible, null, performance.now());
        }
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, [ready, statusColor, perJoint, jointColors, ghostLandmarks, problemJoints, feedbackCue]);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        aspectRatio: "4 / 3",
        borderRadius: 20,
        overflow: "hidden",
        background: "#080F0D",
        boxShadow: "0 20px 40px rgba(0,0,0,0.6)",
      }}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: "scaleX(-1)",
        }}
      />
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
      {!ready && !error && <div style={overlayMsgStyle}>⚡ Initializing AI Vision Engine…</div>}
      {error && <div style={overlayMsgStyle}>{error}</div>}
    </div>
  );
}

const overlayMsgStyle = {
  position: "absolute",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#94A3B8",
  fontSize: 16,
  fontWeight: 600,
  background: "rgba(10, 15, 13, 0.85)",
  textAlign: "center",
  padding: 20,
};

function drawOverlay(
  canvas,
  video,
  landmarks,
  ghostLandmarks,
  jointColors,
  problemJoints,
  feedbackCue,
  statusColor,
  perJoint
) {
  const ctx = canvas.getContext("2d");
  const w = (canvas.width = video.clientWidth);
  const h = (canvas.height = video.clientHeight);
  ctx.clearRect(0, 0, w, h);

  if (!landmarks) return;

  ctx.save();
  ctx.translate(w, 0);
  ctx.scale(-1, 1); // Mirrored space to match webcam view

  // ── 1. Draw RETARGETED GHOST Skeleton (Ideal Reference Form) ───────────
  if (ghostLandmarks && ghostLandmarks.length >= 29) {
    ctx.save();
    ctx.strokeStyle = "rgba(78, 242, 187, 0.45)"; // Translucent cyan
    ctx.lineWidth = 3.0;
    ctx.setLineDash([8, 6]);

    CONNECTIONS.forEach(([a, b]) => {
      const g1 = ghostLandmarks[a];
      const g2 = ghostLandmarks[b];
      if (g1 && g2) {
        ctx.beginPath();
        ctx.moveTo(g1.x * w, g1.y * h);
        ctx.lineTo(g2.x * w, g2.y * h);
        ctx.stroke();
      }
    });

    // Ghost joints
    ctx.fillStyle = "rgba(78, 242, 187, 0.75)";
    [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28].forEach((idx) => {
      const g = ghostLandmarks[idx];
      if (g) {
        ctx.beginPath();
        ctx.arc(g.x * w, g.y * h, 4.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });
    ctx.restore();
  }

  // ── 2. Draw USER Skeleton (Color-Coded by Biomechanical Deviation) ─────
  CONNECTIONS.forEach(([a, b]) => {
    const p1 = landmarks[a];
    const p2 = landmarks[b];
    if (!p1 || !p2) return;

    ctx.beginPath();
    ctx.moveTo(p1.x * w, p1.y * h);
    ctx.lineTo(p2.x * w, p2.y * h);
    ctx.strokeStyle = statusColor || "#E7B978";
    ctx.lineWidth = 4.0;
    ctx.stroke();
  });

  // ── 3. Draw Joints & Highlight Deviations ──────────────────────────────
  const keyJoints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28];
  keyJoints.forEach((i) => {
    const p = landmarks[i];
    if (!p) return;

    let dotColor = "#8FAE8B"; // default green
    if (jointColors) {
      if (jointColors[i] === "red" || jointColors["left_elbow"] === "red") dotColor = "#EF4444";
      else if (jointColors[i] === "amber") dotColor = "#F59E0B";
    }

    ctx.beginPath();
    ctx.arc(p.x * w, p.y * h, 6.0, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.fill();
    ctx.lineWidth = 2.0;
    ctx.strokeStyle = "#FFFFFF";
    ctx.stroke();
  });

  ctx.restore();

  // ── 4. On-Screen Target Angle Callouts & Problem Arcs ──────────────────
  if (problemJoints && Object.keys(problemJoints).length > 0) {
    let yOffset = 40;
    ctx.font = "bold 15px Inter, system-ui, sans-serif";

    Object.entries(problemJoints).forEach(([jointName, info]) => {
      const text = `${jointName.replace("_", " ")}: ${info.measured}° → target ${info.ideal}°`;
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.fillRect(16, yOffset - 20, 260, 30);
      ctx.fillStyle = info.severity === "major" ? "#EF4444" : "#F59E0B";
      ctx.fillText(text, 24, yOffset);
      yOffset += 38;
    });
  }

  // ── 5. Signature Ghost Label in Top Right Corner ───────────────────────
  if (ghostLandmarks && ghostLandmarks.length > 0) {
    ctx.fillStyle = "rgba(15, 23, 42, 0.75)";
    ctx.fillRect(w - 200, 16, 184, 28);
    ctx.fillStyle = "#4EF2BB";
    ctx.font = "600 13px Inter, sans-serif";
    ctx.fillText("--- Ghost Reference Form", w - 190, 35);
  }
}
