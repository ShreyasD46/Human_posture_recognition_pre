import { useCallback, useEffect, useRef, useState } from "react";
import { PoseLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";

const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.17/wasm";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

// Landmarks needed for calibration/full-body-visible check (front-facing standing poses).
const KEY_JOINTS = [11, 12, 23, 24, 25, 26, 27, 28];
const VISIBILITY_THRESHOLD = 0.6;

/**
 * Loads MediaPipe PoseLandmarker (BlazePose, 33 keypoints) and exposes a
 * detect(videoEl) function throttled by the caller. Fully client-side —
 * no video frames ever leave the browser.
 */
export function usePoseDetection() {
  const landmarkerRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const vision = await FilesetResolver.forVisionTasks(WASM_URL);
        const landmarker = await PoseLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
          runningMode: "VIDEO",
          numPoses: 1,
        });
        if (!cancelled) {
          landmarkerRef.current = landmarker;
          setReady(true);
        }
      } catch (e) {
        if (!cancelled) setError("Couldn't load the pose model. Check your connection and reload.");
      }
    })();
    return () => {
      cancelled = true;
      landmarkerRef.current?.close();
    };
  }, []);

  const detect = useCallback((videoEl) => {
    const landmarker = landmarkerRef.current;
    if (!landmarker || !videoEl || videoEl.readyState < 2) return null;
    const result = landmarker.detectForVideo(videoEl, performance.now());
    if (!result?.landmarks?.length) return null;
    return result.landmarks[0]; // [{x, y, z, visibility}] normalized 0-1
  }, []);

  const isFullyVisible = useCallback((landmarks) => {
    if (!landmarks) return false;
    return KEY_JOINTS.every((i) => (landmarks[i]?.visibility ?? 0) >= VISIBILITY_THRESHOLD);
  }, []);

  return { ready, error, detect, isFullyVisible };
}
