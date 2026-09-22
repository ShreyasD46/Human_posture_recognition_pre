"""
Hand-crafted keypoint fixtures for the pose rule-engine regression test suite.

Each fixture is a list of 33 landmark dicts with keys {x, y, visibility},
using MediaPipe BlazePose 33-landmark indices (0-indexed, normalised 0-1 coords).

Key indices:
  11 L shoulder, 12 R shoulder, 13 L elbow,
  23 L hip, 24 R hip, 25 L knee, 26 R knee, 27 L ankle, 28 R ankle,
  15 L wrist, 16 R wrist.

Angles are computed by pose_engine._angle / scoring._angle:
  angle at vertex b from triplet (a, b, c) = dot-product arc-cosine.

All x, y values are normalised 0-1 (proportion of frame).
visibility=0.92 → clearly visible; 0.15 → low confidence / occluded.

Coordinate strategy: place joints on a near-collinear arrangement to hit ~178°,
or place them at known geometric angles for bent-limb fixtures.
"""

import math


def _landmark(x, y, v=0.92):
    return {"x": x, "y": y, "visibility": v}


def _make_33(overrides: dict) -> list:
    """Return a full 33-landmark list; unspecified landmarks use a neutral position."""
    base = [_landmark(0.5, 0.5, 0.9) for _ in range(33)]
    for idx, lm in overrides.items():
        base[idx] = lm
    return base


def _angle_deg(a, b, c):
    """Mirror of pose_engine._angle for fixture verification."""
    ax, ay = a["x"] - b["x"], a["y"] - b["y"]
    cx, cy = c["x"] - b["x"], c["y"] - b["y"]
    dot = ax * cx + ay * cy
    mag_a = math.hypot(ax, ay)
    mag_c = math.hypot(cx, cy)
    if mag_a * mag_c == 0:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (mag_a * mag_c)))))


# ---------------------------------------------------------------------------
# ── TADASANA ─────────────────────────────────────────────────────────────────
# Joints: left_knee [23,25,27]  ideal 178 ±8
#         right_knee [24,26,28] ideal 178 ±8
#         spine_lean [11,23,25] ideal 178 ±10
#         shoulder_level [13,11,12] ideal 95 ±15
# ---------------------------------------------------------------------------

# Near-straight lines → angles close to 180°.
# Place hip, knee, ankle vertically (same x, increasing y) for 178-180°.
# For shoulder_level: place lElbow(13) and rShoulder(12) around lShoulder(11)
# so the angle at (11) between (13)-(11)-(12) ≈ 95°.

# spine_lean triplet is [11, 23, 25] — angle at HIP(23) between SHOULDER(11) and KNEE(25).
# For ~178°: shoulder must be directly above hip (same x) so hip→shoulder is antiparallel to hip→knee.
_T_LSHOULDER = _landmark(0.440, 0.30)   # same x as hip below → near-collinear
_T_RSHOULDER = _landmark(0.620, 0.30)
# shoulder_level triplet is [13, 11, 12] — angle at lShoulder(11) between lElbow(13) and rShoulder(12).
# lElbow below-left, rShoulder to the right → ≈95°
_T_LELBOW    = _landmark(0.427, 0.449)  # exactly 95° from lShoulder→rShoulder direction

_T_LHIP   = _landmark(0.440, 0.54)    # same x as _T_LSHOULDER → spine_lean ≈178°
_T_RHIP   = _landmark(0.560, 0.54)
# knee almost directly below hip, ankle below knee → left_knee ≈178°
_T_LKNEE  = _landmark(0.441, 0.70)
_T_RKNEE  = _landmark(0.561, 0.70)
_T_LANKLE = _landmark(0.442, 0.87)
_T_RANKLE = _landmark(0.562, 0.87)

TADASANA_CORRECT = _make_33({
    11: _T_LSHOULDER,
    12: _T_RSHOULDER,
    13: _T_LELBOW,
    23: _T_LHIP,
    24: _T_RHIP,
    25: _T_LKNEE,
    26: _T_RKNEE,
    27: _T_LANKLE,
    28: _T_RANKLE,
})

# --- Slouched: raise lElbow(13) so angle at lShoulder(11) between (13)-(11)-(12) > 110° ---
# Move lElbow directly above lShoulder → large angle (approaching 180° through wrong direction)
# Instead: move it far left+up so the angle blows past 95+15=110°.
TADASANA_SLOUCHED = _make_33({
    11: _T_LSHOULDER,
    12: _T_RSHOULDER,
    13: _landmark(0.22, 0.28),  # elbow far left → shoulder_level angle >> 110° → flags
    23: _T_LHIP,
    24: _T_RHIP,
    25: _T_LKNEE,
    26: _T_RKNEE,
    27: _T_LANKLE,
    28: _T_RANKLE,
})

# --- Bent knees: move ankle so knee is bent ~150° ---
# Angle at knee(25) between hip(23) and ankle(27).
# Place ankle displaced sideways so the angle drops to ~150°.
TADASANA_BENT_KNEES = _make_33({
    11: _T_LSHOULDER,
    12: _T_RSHOULDER,
    13: _T_LELBOW,
    23: _T_LHIP,
    24: _T_RHIP,
    25: _T_LKNEE,
    26: _T_RKNEE,
    27: _landmark(0.47, 0.87),  # ankle displaced → left_knee angle ~148° → flags
    28: _landmark(0.52, 0.87),
})


# ---------------------------------------------------------------------------
# ── TRIKONASANA ──────────────────────────────────────────────────────────────
# Joints: front_knee [23,25,27] ideal 175 ±10
#         hip_hinge  [11,23,25] ideal 100 ±15
#         top_arm_line [15,11,23] ideal 175 ±15
# ---------------------------------------------------------------------------

# For hip_hinge at vertex 23: angle between (11) and (25).
# For front_knee at vertex 25: near-straight (175°).
# For top_arm_line at vertex 11: angle between wrist(15) and hip(23).
#
# Strategy: set coords so each angle hits within tolerance.
# hip_hinge: shoulder(11) is above-left of hip(23), knee(25) is below-left.
#   Need angle at hip ≈ 100°.
#   Place shoulder at (0.50, 0.30), hip at (0.44, 0.52), knee at (0.28, 0.70).
#   Vector hip→shoulder: (0.06, -0.22); hip→knee: (-0.16, 0.18).
#   dot = 0.06*(-0.16) + (-0.22)*0.18 = -0.0096 - 0.0396 = -0.0492
#   mag_s=√(0.0036+0.0484)=√0.052≈0.228; mag_k=√(0.0256+0.0324)=√0.058≈0.241
#   cos = -0.0492/(0.228*0.241) ≈ -0.0492/0.0550 ≈ -0.895 → angle ≈ 153°  too high
#
# Easier approach: use exact geometry.
# Place hip at origin, put shoulder at angle θ_s from vertical, knee at θ_k.
# We want the angle between the two vectors = 100°.
# Let shoulder direction = 90° from vertical (i.e., straight up from hip), knee = 10° below vertical.
# angle between them = 90+10 = 100°. ✓

def _tri_joints():
    hip = (0.50, 0.55)
    # shoulder 0.15 units directly above hip → hip→shoulder direction = up (270° in screen coords)
    shoulder = (hip[0], hip[1] - 0.15)     # straight up
    # knee: 100° from shoulder direction at vertex hip.
    # shoulder direction from hip: angle = -90° (up). Rotate by 100°: -90+100=10° from pos-x axis.
    import math as m
    knee_angle_rad = m.radians(10)           # 10° from positive-x = mostly rightward+down
    knee_dist = 0.22
    knee = (hip[0] + knee_dist * m.cos(knee_angle_rad),
            hip[1] + knee_dist * m.sin(knee_angle_rad))
    # ankle: nearly collinear with hip→knee (175°) — place past knee in the same direction
    ankle_dist = 0.22
    ankle = (knee[0] + ankle_dist * m.cos(knee_angle_rad),
             knee[1] + ankle_dist * m.sin(knee_angle_rad))
    # wrist(15): placed so angle at shoulder(11) between wrist(15) and hip(23) ≈ 175°
    # direction hip→shoulder = up. Wrist should be nearly opposite direction from hip relative to shoulder.
    # hip relative to shoulder = down. So wrist should be up (175° from down = nearly up).
    wrist = (shoulder[0], shoulder[1] - 0.15)   # directly above shoulder → ~175°
    return shoulder, hip, knee, ankle, wrist

_tri_s, _tri_h, _tri_k, _tri_a, _tri_w = _tri_joints()

TRIKONASANA_CORRECT = _make_33({
    11: _landmark(*_tri_s),
    15: _landmark(*_tri_w),
    23: _landmark(*_tri_h),
    25: _landmark(*_tri_k),
    27: _landmark(*_tri_a),
    # mirror for right side (not used by angle triplets but nice to have)
    12: _landmark(0.62, 0.28),
    24: _landmark(0.64, 0.55),
    26: _landmark(0.72, 0.70),
    28: _landmark(0.80, 0.86),
})

# --- Bent front knee: move ankle to make knee angle ~148° (175-10=165 in tolerance; use 148 outside) ---
# Displace ankle perpendicular to the knee→hip direction to create a bend.
import math as _m
_knee_angle_rad = _m.radians(10)
_perp_angle = _knee_angle_rad + _m.radians(90)
_bent_ankle = (
    _tri_k[0] + 0.20 * _m.cos(_perp_angle),
    _tri_k[1] + 0.20 * _m.sin(_perp_angle),
)

TRIKONASANA_BENT_KNEE = _make_33({
    11: _landmark(*_tri_s),
    15: _landmark(*_tri_w),
    23: _landmark(*_tri_h),
    25: _landmark(*_tri_k),
    27: _landmark(*_bent_ankle),   # displaced → knee angle ~127° → flags
    12: _landmark(0.62, 0.28),
    24: _landmark(0.64, 0.55),
    26: _landmark(0.72, 0.70),
    28: _landmark(0.80, 0.86),
})


# ---------------------------------------------------------------------------
# ── VRIKSHASANA ──────────────────────────────────────────────────────────────
# Joints: standing_knee [23,25,27] ideal 178 ±8
#         lifted_hip_knee [24,26,28] ideal 45 ±20
#         torso_upright [11,23,25] ideal 178 ±12
# ---------------------------------------------------------------------------

# Standing leg: near-straight (like Tadasana left leg)
# Lifted leg: angle at right knee(26) between R hip(24) and R ankle(28) ≈ 45°
# Place R hip above R knee, R ankle diagonally away to get 45° bend.

def _vrk_joints():
    lhip = (0.44, 0.54)
    lknee = (0.441, 0.70)
    lankle = (0.442, 0.87)
    # shoulder above hip for torso_upright ≈ 178°
    lshoulder = (0.440, 0.30)

    rhip = (0.56, 0.54)
    # R knee bent, elevated
    rknee = (0.62, 0.66)
    # angle at rknee(26) between rhip(24) and rankle(28) = 45°
    # Vector knee→hip: rhip - rknee = (-0.06, -0.12); direction ≈ -90+atan2(-0.12,-0.06)
    import math as m
    hip_dir = m.atan2(rhip[1] - rknee[1], rhip[0] - rknee[0])
    ankle_dir = hip_dir + m.radians(45)   # 45° from hip direction
    rankle = (rknee[0] + 0.14 * m.cos(ankle_dir),
              rknee[1] + 0.14 * m.sin(ankle_dir))
    return lshoulder, lhip, lknee, lankle, rhip, rknee, rankle

_v_ls, _v_lh, _v_lk, _v_la, _v_rh, _v_rk, _v_ra = _vrk_joints()

VRIKSHASANA_CORRECT = _make_33({
    11: _landmark(*_v_ls),
    12: _landmark(0.60, 0.30),
    23: _landmark(*_v_lh),
    24: _landmark(*_v_rh),
    25: _landmark(*_v_lk),
    26: _landmark(*_v_rk),
    27: _landmark(*_v_la),
    28: _landmark(*_v_ra),
})


# ---------------------------------------------------------------------------
# ── VIRABHADRASANA II ─────────────────────────────────────────────────────────
# Joints: front_knee_bend [23,25,27] ideal 90 ±15
#         back_leg_straight [24,26,28] ideal 175 ±10
#         arm_line [13,11,12] ideal 178 ±12
# ---------------------------------------------------------------------------

def _war2_joints():
    import math as m
    lhip = (0.42, 0.54)
    lknee = (0.34, 0.70)
    # front_knee_bend: angle at lknee between lhip and lankle = 90°
    hip_dir = m.atan2(lhip[1] - lknee[1], lhip[0] - lknee[0])
    ankle_dir = hip_dir + m.radians(90)
    lankle = (lknee[0] + 0.18 * m.cos(ankle_dir),
              lknee[1] + 0.18 * m.sin(ankle_dir))

    # back leg straight (175°): near-collinear vertically (same x)
    rhip   = (0.620, 0.54)
    rknee  = (0.621, 0.70)
    rankle = (0.622, 0.87)

    # arm_line: angle at lshoulder(11) between lelbow(13) and rshoulder(12) ≈ 178°
    # Arms extended horizontally: lshoulder, lelbow, lwrist all on same y.
    lshoulder = (0.40, 0.36)
    rshoulder = (0.62, 0.36)
    lelbow = (0.22, 0.36)   # left of lshoulder, same y → near-180° angle

    return lshoulder, rshoulder, lelbow, lhip, rhip, lknee, lankle, rknee, rankle

_w_ls, _w_rs, _w_le, _w_lh, _w_rh, _w_lk, _w_la, _w_rk, _w_ra = _war2_joints()

VIRABHADRASANA_II_CORRECT = _make_33({
    11: _landmark(*_w_ls),
    12: _landmark(*_w_rs),
    13: _landmark(*_w_le),
    23: _landmark(*_w_lh),
    24: _landmark(*_w_rh),
    25: _landmark(*_w_lk),
    26: _landmark(*_w_rk),
    27: _landmark(*_w_la),
    28: _landmark(*_w_ra),
})


# ---------------------------------------------------------------------------
# ── UTKATASANA ───────────────────────────────────────────────────────────────
# Joints: knee_bend [23,25,27] ideal 115 ±15
#         torso_lean [11,23,25] ideal 150 ±15
#         arms_overhead [23,11,15] ideal 170 ±15
# ---------------------------------------------------------------------------

def _utk_joints():
    import math as m
    lhip = (0.44, 0.58)
    lknee = (0.40, 0.73)
    # knee_bend: angle at lknee between lhip and lankle = 115°
    hip_dir = m.atan2(lhip[1] - lknee[1], lhip[0] - lknee[0])
    ankle_dir = hip_dir + m.radians(115)
    lankle = (lknee[0] + 0.18 * m.cos(ankle_dir),
              lknee[1] + 0.18 * m.sin(ankle_dir))

    # torso_lean: angle at lhip(23) between lshoulder(11) and lknee(25) = 150°
    knee_dir = m.atan2(lknee[1] - lhip[1], lknee[0] - lhip[0])
    shoulder_dir = knee_dir + m.radians(150)
    lshoulder = (lhip[0] + 0.24 * m.cos(shoulder_dir),
                 lhip[1] + 0.24 * m.sin(shoulder_dir))

    # arms_overhead: angle at lshoulder(11) between lhip(23) and lwrist(15) = 170°
    hip_from_shoulder_dir = m.atan2(lhip[1] - lshoulder[1], lhip[0] - lshoulder[0])
    wrist_dir = hip_from_shoulder_dir + m.radians(170)
    lwrist = (lshoulder[0] + 0.24 * m.cos(wrist_dir),
              lshoulder[1] + 0.24 * m.sin(wrist_dir))

    return lshoulder, lhip, lknee, lankle, lwrist

_u_ls, _u_lh, _u_lk, _u_la, _u_lw = _utk_joints()

UTKATASANA_CORRECT = _make_33({
    11: _landmark(*_u_ls),
    12: _landmark(0.60, _u_ls[1]),
    15: _landmark(*_u_lw),
    23: _landmark(*_u_lh),
    24: _landmark(0.56, _u_lh[1]),
    25: _landmark(*_u_lk),
    26: _landmark(0.60, _u_lk[1]),
    27: _landmark(*_u_la),
    28: _landmark(0.58, _u_la[1]),
})


# ---------------------------------------------------------------------------
# Low-visibility fixture — one landmark deliberately occluded
# ---------------------------------------------------------------------------

TRIKONASANA_OCCLUDED_KNEE = _make_33({
    11: _landmark(*_tri_s),
    15: _landmark(*_tri_w),
    23: _landmark(*_tri_h),
    25: _landmark(*_tri_k, 0.15),  # ← low visibility on the knee landmark
    27: _landmark(*_tri_a),
    12: _landmark(0.62, 0.28),
    24: _landmark(0.64, 0.55),
    26: _landmark(0.72, 0.70),
    28: _landmark(0.80, 0.86),
})
