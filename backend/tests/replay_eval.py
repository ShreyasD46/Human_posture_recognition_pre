"""
Offline evaluation harness (Phase 5).

Runs pre-extracted MediaPipe keypoint sequences through the rule engine
and measures precision / recall per pose.

Usage
-----
1. Film yourself doing each pose (correct + common mistakes).
2. Extract keypoints offline:
       python extract_keypoints.py --input test_data/clips/ --output test_data/json/
3. Run evaluation:
       python backend/tests/replay_eval.py --clips test_data/json/ --threshold 75

Clip JSON format
----------------
{
  "pose":  "trikonasana",
  "label": "correct" | "bent_knee" | ...,
  "path":  "test_data/clips/trikonasana_correct_01.mp4",
  "frames": [
    [{"x": 0.5, "y": 0.3, "visibility": 0.9}, ...],   // 33 landmarks per frame
    ...
  ]
}
"""

import sys
import os
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Ensure backend/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scoring import compute_pose_score

CORRECT_THRESHOLD = 75.0   # avg score above this → "predicted correct"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_clip(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def load_all_clips(clips_dir: Path) -> list[dict]:
    clips = []
    for p in sorted(clips_dir.glob("*.json")):
        try:
            clips.append(load_clip(p))
        except Exception as e:
            print(f"  ⚠  Skipping {p.name}: {e}")
    return clips


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_clip(clip: dict, threshold: float = CORRECT_THRESHOLD) -> dict:
    """Run all frames through compute_pose_score and return a result record."""
    pose   = clip["pose"]
    frames = clip.get("frames", [])
    if not frames:
        return {"clip": clip.get("path", "?"), "error": "no frames", "skipped": True}

    scores = [compute_pose_score(pose, frame)["score"] for frame in frames]
    avg    = sum(scores) / len(scores)

    predicted_correct = avg >= threshold
    actual_correct    = clip.get("label", "") == "correct"

    return {
        "clip":               clip.get("path", "?"),
        "pose":               pose,
        "label":              clip.get("label", "?"),
        "avg_score":          round(avg, 1),
        "predicted_correct":  predicted_correct,
        "actual_correct":     actual_correct,
        "n_frames":           len(frames),
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_confusion(results: list[dict]) -> dict:
    tp = sum(1 for r in results if r["predicted_correct"] and r["actual_correct"])
    fp = sum(1 for r in results if r["predicted_correct"] and not r["actual_correct"])
    fn = sum(1 for r in results if not r["predicted_correct"] and r["actual_correct"])
    tn = sum(1 for r in results if not r["predicted_correct"] and not r["actual_correct"])
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0.0)
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 3),
        "recall":    round(recall, 3),
        "f1":        round(f1, 3),
        "n":         len(results),
    }


def compute_per_pose(results: list[dict]) -> dict:
    by_pose: dict[str, list] = defaultdict(list)
    for r in results:
        by_pose[r["pose"]].append(r)
    return {pose: compute_confusion(clips) for pose, clips in by_pose.items()}


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(overall: dict, per_pose: dict, threshold: float) -> None:
    sep = "─" * 58
    print(f"\n{sep}")
    print(f"  Sthira Rule-Engine Evaluation  (threshold={threshold})")
    print(sep)
    print(f"  {'Pose':<22} {'N':>4}  {'Prec':>6}  {'Rec':>6}  {'F1':>6}")
    print(sep)
    for pose, m in sorted(per_pose.items()):
        print(f"  {pose:<22} {m['n']:>4}  {m['precision']:>6.3f}  {m['recall']:>6.3f}  {m['f1']:>6.3f}")
    print(sep)
    m = overall
    print(f"  {'OVERALL':<22} {m['n']:>4}  {m['precision']:>6.3f}  {m['recall']:>6.3f}  {m['f1']:>6.3f}")
    print(f"  TP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}")
    print(sep)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_eval(clips_dir: Path, threshold: float = CORRECT_THRESHOLD,
             verbose: bool = False) -> dict:
    clips = load_all_clips(clips_dir)
    if not clips:
        print(f"No JSON clip files found in {clips_dir}")
        return {}

    print(f"Evaluating {len(clips)} clips …")
    results = []
    for clip in clips:
        r = score_clip(clip, threshold=threshold)
        if r.get("skipped"):
            print(f"  ↷  Skipped: {r['clip']}")
            continue
        results.append(r)
        if verbose:
            flag = "✓" if r["predicted_correct"] == r["actual_correct"] else "✗"
            print(f"  {flag} {Path(r['clip']).name:<40} "
                  f"score={r['avg_score']:>5.1f}  "
                  f"label={r['label']:<14} "
                  f"pred={'correct' if r['predicted_correct'] else 'incorrect'}")

    if not results:
        print("All clips skipped.")
        return {}

    overall  = compute_confusion(results)
    per_pose = compute_per_pose(results)
    print_report(overall, per_pose, threshold)
    return {"overall": overall, "per_pose": per_pose, "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sthira rule-engine evaluation harness")
    parser.add_argument("--clips",     required=True, help="Directory of JSON clip files")
    parser.add_argument("--threshold", type=float, default=CORRECT_THRESHOLD,
                        help=f"Avg-score threshold for 'predicted correct' (default {CORRECT_THRESHOLD})")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    run_eval(Path(args.clips), threshold=args.threshold, verbose=args.verbose)
