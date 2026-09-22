import { useEffect, useState } from "react";
import "./PoseDemo.css";

/**
 * Static illustration demonstration of a yoga pose.
 *
 * User clicks "I'm Ready" → 3-2-1-Go countdown → onReady().
 */
export default function PoseDemo({ poseId, poseInfo, onReady }) {
  const [countdown, setCountdown] = useState(null);   // null | 3 | 2 | 1 | "go"
  const [countdownLeaving, setCountdownLeaving] = useState(false);

  // Map poseId to the generated illustration files
  const illustrationSrc = `/${poseId}_illustration.jpg`;

  // Countdown logic
  useEffect(() => {
    if (countdown === null) return;

    if (countdown === "go") {
      // Start fade-out, then call onReady
      setCountdownLeaving(true);
      const t = setTimeout(() => onReady(), 700);
      return () => clearTimeout(t);
    }

    if (countdown > 0) {
      const t = setTimeout(
        () => setCountdown((c) => (c === 1 ? "go" : c - 1)),
        1000
      );
      return () => clearTimeout(t);
    }
  }, [countdown, onReady]);

  const handleReady = () => {
    setCountdownLeaving(false);
    setCountdown(3);
  };

  return (
    <>
      <div className="demo-overlay">
        <span className="demo-label-pulse">Watch the demo</span>

        <div className="demo-figure-container">
          <img 
            src={illustrationSrc} 
            alt={poseInfo?.label || "Yoga Pose"} 
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '24px' }}
          />
        </div>

        <div className="demo-info">
          <h2>{poseInfo?.label || "Yoga Pose"}</h2>
          <p>{poseInfo?.instructions || ""}</p>
          <div className="target-hold">
            Target hold: {poseInfo?.hold_time_target || 15}s
          </div>
        </div>

        {countdown === null && (
          <button className="demo-ready-btn" onClick={handleReady}>
            I'm Ready
          </button>
        )}
      </div>

      {/* Countdown overlay */}
      {countdown !== null && (
        <div className={`countdown-overlay${countdownLeaving ? " leaving" : ""}`}>
          {countdown === "go" ? (
            <div className="demo-go-text">Go!</div>
          ) : (
            <div className="countdown-number" key={countdown}>
              {countdown}
            </div>
          )}
        </div>
      )}
    </>
  );
}
