import { useEffect, useRef } from "react";
import { usePoseDetection } from "../hooks/usePoseDetection.js";

const CONNECTIONS = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
];
const FRAME_INTERVAL_MS = 1000 / 15; // throttle to ~15fps

export default function CameraView({ onFrame, statusColor, perJoint, refinedLandmarks, enablePhysGNN = true }) {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const rafRef     = useRef(null);
  const lastSentRef = useRef(0);
  const { ready, error, detect, isFullyVisible } = usePoseDetection();

  useEffect(() => {
    let stream;
    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
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
      const video  = videoRef.current;
      const canvas = canvasRef.current;
      if (video && canvas && video.readyState >= 2) {
        const landmarks = detect(video);
        const displayLandmarks = (enablePhysGNN && refinedLandmarks) ? refinedLandmarks : landmarks;
        drawOverlay(canvas, video, displayLandmarks, statusColor, perJoint, enablePhysGNN);
        const visible = isFullyVisible(landmarks);

        if (t - lastSentRef.current >= FRAME_INTERVAL_MS) {
          lastSentRef.current = t;

          // Phase 2: include visibility; Phase 4: attach capturedAt timestamp
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
  }, [ready, statusColor, perJoint]);

  return (
    <div style={{
      position: "relative", width: "100%", aspectRatio: "4 / 3",
      borderRadius: 18, overflow: "hidden", background: "#0A1712",
    }}>
      <video
        ref={videoRef}
        autoPlay playsInline muted
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%",
                 objectFit: "cover", transform: "scaleX(-1)" }}
      />
      <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
      {!ready && !error && <div style={overlayMsgStyle}>Loading pose model…</div>}
      {error    && <div style={overlayMsgStyle}>{error}</div>}
    </div>
  );
}

const overlayMsgStyle = {
  position: "absolute", inset: 0, display: "flex", alignItems: "center",
  justifyContent: "center", color: "var(--text-muted)", fontSize: 14,
  textAlign: "center", padding: 20,
};

// ---------------------------------------------------------------------------
// Overlay drawing — colours joints by per-joint score, greys-out unmeasurable
// ---------------------------------------------------------------------------

/**
 * jointColor: returns a CSS color based on per-joint score value.
 *  null  → occluded (grey/dashed handled separately)
 *  0-49  → error red
 *  50-79 → warn amber
 *  80+   → good green
 */
function jointColor(score, defaultColor) {
  if (score === null || score === undefined) return "rgba(160,160,160,0.5)";
  if (score >= 80) return "var(--success, #8FAE8B)";
  if (score >= 50) return "var(--warn, #D9A257)";
  return "var(--error, #C97158)";
}

function drawOverlay(canvas, video, landmarks, statusColor, perJoint, enablePhysGNN = true) {
  const ctx = canvas.getContext("2d");
  const w   = (canvas.width  = video.clientWidth);
  const h   = (canvas.height = video.clientHeight);
  ctx.clearRect(0, 0, w, h);
  if (!landmarks) return;

  const color = statusColor || "var(--accent-soft, #E7B978)";

  ctx.save();
  ctx.translate(w, 0);
  ctx.scale(-1, 1); // mirror to match the mirrored video

  // ── Connections ──────────────────────────────────────────────────────────
  CONNECTIONS.forEach(([a, b]) => {
    const p1 = landmarks[a], p2 = landmarks[b];
    if (!p1 || !p2) return;
    ctx.beginPath();
    ctx.moveTo(p1.x * w, p1.y * h);
    ctx.lineTo(p2.x * w, p2.y * h);
    ctx.strokeStyle = enablePhysGNN ? color : "rgba(231, 185, 120, 0.7)";
    ctx.lineWidth   = enablePhysGNN ? 3.5 : 2;
    ctx.stroke();
  });

  // ── Joints ───────────────────────────────────────────────────────────────
  const keyJoints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28];
  // Build a landmark-index → joint-name mapping for per-joint colouring
  const LM_JOINT_NAMES = {
    25: "left_knee", 26: "right_knee", 27: "left_knee", 28: "right_knee",
    23: "spine_lean", 11: "shoulder_level", 12: "shoulder_level",
  };

  keyJoints.forEach((i) => {
    const p = landmarks[i];
    if (!p) return;
    const jointName = LM_JOINT_NAMES[i];
    const score = perJoint && jointName ? perJoint[jointName] : undefined;
    const isInpainted = Boolean(p.is_inpainted);
    
    // Inpainted joint gets a highlighted cyan/teal aura
    const dotColor = isInpainted 
      ? "#4EF2BB"
      : perJoint ? jointColor(score, color) : color;

    ctx.beginPath();
    ctx.arc(p.x * w, p.y * h, isInpainted ? 6.5 : 5, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.fill();

    // Inpainted neural graph recovery ring
    if (isInpainted) {
      ctx.beginPath();
      ctx.arc(p.x * w, p.y * h, 10, 0, Math.PI * 2);
      ctx.strokeStyle = "#4EF2BB";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    } else if (score === null && perJoint) {
      // Unmeasurable (occluded) joint ring
      ctx.beginPath();
      ctx.arc(p.x * w, p.y * h, 8, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(160,160,160,0.4)";
      ctx.setLineDash([3, 3]);
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.setLineDash([]);
    }
  });

  ctx.restore();
}
