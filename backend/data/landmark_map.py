"""
Maps each joint name (as defined in data/poses.py) to the three MediaPipe
BlazePose landmark indices whose visibility must be adequate for the angle
to be reliably calculated.

These are derived directly from the "triplet" field in poses.py, but kept
as an explicit lookup so the scoring module doesn't have to iterate POSES
every call.

MediaPipe BlazePose 33-landmark indices (key ones):
  11 L shoulder  12 R shoulder
  13 L elbow     14 R elbow
  15 L wrist     16 R wrist
  23 L hip       24 R hip
  25 L knee      26 R knee
  27 L ankle     28 R ankle
"""

JOINT_LANDMARK_MAP: dict[str, list[int]] = {
    # ── Tadasana ──────────────────────────────────────────────────────────
    "left_knee":       [23, 25, 27],
    "right_knee":      [24, 26, 28],
    "spine_lean":      [11, 23, 25],
    "shoulder_level":  [13, 11, 12],

    # ── Vrikshasana ───────────────────────────────────────────────────────
    "standing_knee":   [23, 25, 27],
    "lifted_hip_knee": [24, 26, 28],
    "torso_upright":   [11, 23, 25],

    # ── Trikonasana ───────────────────────────────────────────────────────
    "front_knee":      [23, 25, 27],
    "hip_hinge":       [11, 23, 25],
    "top_arm_line":    [15, 11, 23],

    # ── Virabhadrasana II ─────────────────────────────────────────────────
    "front_knee_bend":   [23, 25, 27],
    "back_leg_straight": [24, 26, 28],
    "arm_line":          [13, 11, 12],

    # ── Utkatasana ────────────────────────────────────────────────────────
    "knee_bend":      [23, 25, 27],
    "torso_lean":     [11, 23, 25],
    "arms_overhead":  [23, 11, 15],
}
