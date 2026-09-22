"""
Weighted composite scoring module.

Replaces binary pass/fail-per-joint with a continuous 0–100 pose score.
Each joint contributes proportionally to its weight; joints with low-visibility
landmarks are skipped (confidence gating).

Severity scale (replaces old "low"/"high"):
  minor    — deviation < 1.5× tolerance
  moderate — deviation < 2.5× tolerance
  major    — deviation ≥ 2.5× tolerance
"""

import math
from data.poses import POSES
from data.landmark_map import JOINT_LANDMARK_MAP

CONFIDENCE_THRESHOLD = 0.6   # min per-landmark visibility to include in scoring


def _severity(deviation: float, tolerance: float) -> str:
    ratio = deviation / tolerance
    if ratio < 1.5:
        return "minor"
    if ratio < 2.5:
        return "moderate"
    return "major"


def compute_pose_score(
    pose_name: str,
    landmarks: list,
    *,
    use_visibility_gating: bool = True,
    use_3d: bool = True,
) -> dict:
    """
    Compute a weighted composite score for the given pose and landmark list.

    Parameters
    ----------
    pose_name : str
        Key into POSES dict (e.g. "tadasana").
    landmarks : list
        List of 33 dicts with keys {x, y, visibility} from MediaPipe BlazePose.
    use_visibility_gating : bool
        When True (default), joints whose required landmarks have visibility
        below CONFIDENCE_THRESHOLD are skipped rather than scored.

    Returns
    -------
    dict with keys:
      score       : float 0–100  (weighted composite)
      per_joint   : dict joint_name → float 0–100 or None (unmeasurable)
      errors      : list of {joint, deviation, severity, feedback}
    """
    pose_def = POSES.get(pose_name)
    if not pose_def:
        return {"score": 0.0, "per_joint": {}, "errors": []}

    total_score = 0.0
    weight_measured = 0.0   # sum of weights for joints we could actually measure
    per_joint: dict = {}
    errors: list = []

    for joint in pose_def["keypoint_angles"]:
        name    = joint["name"]
        triplet = joint["triplet"]
        ideal   = joint["ideal"]
        tol     = joint["tolerance"]
        weight  = joint.get("weight", 1.0)

        # ── Visibility gating ────────────────────────────────────────────
        if use_visibility_gating:
            required_lm_indices = JOINT_LANDMARK_MAP.get(name, triplet)
            low_vis = any(
                (landmarks[i].get("visibility", 1.0) if i < len(landmarks) else 0.0)
                < CONFIDENCE_THRESHOLD
                for i in required_lm_indices
            )
            if low_vis:
                per_joint[name] = None   # unmeasurable this frame
                continue

        # ── Angle calculation ────────────────────────────────────────────
        try:
            a, b, c = landmarks[triplet[0]], landmarks[triplet[1]], landmarks[triplet[2]]
        except (IndexError, TypeError):
            per_joint[name] = None
            continue

        # ── Angle calculation (3D True Euclidean Space) ──────────────────
        angle_3d = _angle_3d(a, b, c) if use_3d else None
        angle_2d = _angle_2d(a, b, c)
        
        # Use 3D angle if available and valid; fallback to 2D
        angle = angle_3d if (angle_3d is not None and not math.isnan(angle_3d)) else angle_2d

        if angle is None:
            per_joint[name] = None
            continue

        foreshortening_error = round(abs(angle_3d - angle_2d), 1) if (angle_3d is not None and angle_2d is not None) else 0.0

        # ── Scoring ──────────────────────────────────────────────────────
        deviation = abs(angle - ideal)
        # Linear falloff: 0 deviation → 1.0, deviation ≥ 2×tolerance → 0.0
        joint_score_01 = max(0.0, 1.0 - deviation / (2 * tol))
        joint_score_100 = round(joint_score_01 * 100, 1)

        per_joint[name] = joint_score_100
        total_score    += joint_score_01 * weight
        weight_measured += weight

        if deviation > tol:
            errors.append({
                "joint":     name,
                "deviation": round(deviation, 1),
                "severity":  _severity(deviation, tol),
                "feedback":  joint["feedback"],
                "measured_angle": round(angle, 1),
                "ideal_angle":    ideal,
                "foreshortening_error": foreshortening_error,
            })

    # Normalise: if some joints were skipped we still get a 0-100 score
    # based on the joints that were actually measured.
    if weight_measured > 0:
        normalised_score = round((total_score / weight_measured) * 100, 1)
    else:
        normalised_score = 0.0

    return {
        "score":     normalised_score,
        "per_joint": per_joint,
        "errors":    errors,
    }


# ---------------------------------------------------------------------------
# Biomechanical 3D Geometry vs Planar 2D Projection
# ---------------------------------------------------------------------------

def _angle_3d(a: dict, b: dict, c: dict) -> float | None:
    """
    True 3D Euclidean joint angle at vertex b formed by points a-b-c.
    Eliminates monocular planar foreshortening perspective errors.
    """
    ax = a.get("x", 0.0) - b.get("x", 0.0)
    ay = a.get("y", 0.0) - b.get("y", 0.0)
    az = a.get("z", 0.0) - b.get("z", 0.0)

    cx = c.get("x", 0.0) - b.get("x", 0.0)
    cy = c.get("y", 0.0) - b.get("y", 0.0)
    cz = c.get("z", 0.0) - b.get("z", 0.0)

    dot = ax * cx + ay * cy + az * cz
    mag_a = math.sqrt(ax * ax + ay * ay + az * az)
    mag_c = math.sqrt(cx * cx + cy * cy + cz * cz)
    if mag_a * mag_c == 0:
        return None
    cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))
    return math.degrees(math.acos(cos_angle))


def _angle_2d(a: dict, b: dict, c: dict) -> float | None:
    """Flat 2D image plane angle at vertex b."""
    ax, ay = a["x"] - b["x"], a["y"] - b["y"]
    cx, cy = c["x"] - b["x"], c["y"] - b["y"]
    dot    = ax * cx + ay * cy
    mag_a  = math.hypot(ax, ay)
    mag_c  = math.hypot(cx, cy)
    if mag_a * mag_c == 0:
        return None
    cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))
    return math.degrees(math.acos(cos_angle))


def _angle(a: dict, b: dict, c: dict) -> float | None:
    """Alias for backward compatibility."""
    return _angle_3d(a, b, c) or _angle_2d(a, b, c)
