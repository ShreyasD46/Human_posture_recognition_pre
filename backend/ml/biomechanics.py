"""
Biomechanical definitions and anatomical constraints for Sthira-PhysGNN.
Standardized per American Academy of Orthopaedic Surgeons (AAOS)
and clinical biomechanics references.
"""

# ── 33 MediaPipe BlazePose Landmark Indices ────────────────────────────────
NOSE = 0
LEFT_EYE_INNER = 1
LEFT_EYE = 2
LEFT_EYE_OUTER = 3
RIGHT_EYE_INNER = 4
RIGHT_EYE = 5
RIGHT_EYE_OUTER = 6
LEFT_EAR = 7
RIGHT_EAR = 8
MOUTH_LEFT = 9
MOUTH_RIGHT = 10
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_PINKY = 17
RIGHT_PINKY = 18
LEFT_INDEX = 19
RIGHT_INDEX = 20
LEFT_THUMB = 21
RIGHT_THUMB = 22
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32

NUM_LANDMARKS = 33

# ── Physiological Skeletal Bone Segments (Pairs of Joint Indices) ───────────
# Real human bones maintain invariant lengths across frames during movement.
ANATOMICAL_BONES = [
    # Torso / Core Frame
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_HIP, RIGHT_HIP),
    (LEFT_SHOULDER, LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),

    # Upper Limbs (Left)
    (LEFT_SHOULDER, LEFT_ELBOW),
    (LEFT_ELBOW, LEFT_WRIST),
    (LEFT_WRIST, LEFT_INDEX),
    (LEFT_WRIST, LEFT_PINKY),

    # Upper Limbs (Right)
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW, RIGHT_WRIST),
    (RIGHT_WRIST, RIGHT_INDEX),
    (RIGHT_WRIST, RIGHT_PINKY),

    # Lower Limbs (Left)
    (LEFT_HIP, LEFT_KNEE),
    (LEFT_KNEE, LEFT_ANKLE),
    (LEFT_ANKLE, LEFT_HEEL),
    (LEFT_ANKLE, LEFT_FOOT_INDEX),
    (LEFT_HEEL, LEFT_FOOT_INDEX),

    # Lower Limbs (Right)
    (RIGHT_HIP, RIGHT_KNEE),
    (RIGHT_KNEE, RIGHT_ANKLE),
    (RIGHT_ANKLE, RIGHT_HEEL),
    (RIGHT_ANKLE, RIGHT_FOOT_INDEX),
    (RIGHT_HEEL, RIGHT_FOOT_INDEX),

    # Cranial / Cervical Spine
    (NOSE, LEFT_SHOULDER),
    (NOSE, RIGHT_SHOULDER),
]

# ── AAOS Orthopedic Range of Motion (ROM) Physiological Limits (Degrees) ───
# Triplet format: (proximal_idx, vertex_idx, distal_idx)
# min_deg: minimum anatomically possible angle
# max_deg: maximum anatomically possible angle (hyperextension barrier)
ORTHOPEDIC_ROM_LIMITS = {
    "left_knee": {
        "triplet": (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
        "min_deg": 35.0,     # Extreme acute flexion (deep squat)
        "max_deg": 182.0,    # Max physiological extension (rare mild recurvatum <= 2 deg)
        "name": "Left Knee Flexion/Extension",
    },
    "right_knee": {
        "triplet": (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
        "min_deg": 35.0,
        "max_deg": 182.0,
        "name": "Right Knee Flexion/Extension",
    },
    "left_elbow": {
        "triplet": (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
        "min_deg": 30.0,     # Full elbow flexion
        "max_deg": 182.0,    # Full elbow extension
        "name": "Left Elbow Flexion/Extension",
    },
    "right_elbow": {
        "triplet": (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
        "min_deg": 30.0,
        "max_deg": 182.0,
        "name": "Right Elbow Flexion/Extension",
    },
    "left_shoulder": {
        "triplet": (LEFT_ELBOW, LEFT_SHOULDER, LEFT_HIP),
        "min_deg": 10.0,     # Adduction against torso
        "max_deg": 185.0,    # Full overhead abduction
        "name": "Left Shoulder Abduction",
    },
    "right_shoulder": {
        "triplet": (RIGHT_ELBOW, RIGHT_SHOULDER, RIGHT_HIP),
        "min_deg": 10.0,
        "max_deg": 185.0,
        "name": "Right Shoulder Abduction",
    },
    "left_hip": {
        "triplet": (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE),
        "min_deg": 40.0,     # Acute hip flexion
        "max_deg": 190.0,    # Mild hip hyperextension (warrior 1/crescent lunge)
        "name": "Left Hip Flexion/Extension",
    },
    "right_hip": {
        "triplet": (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE),
        "min_deg": 40.0,
        "max_deg": 190.0,
        "name": "Right Hip Flexion/Extension",
    },
}

def get_anatomical_adjacency_matrix():
    """
    Constructs the binary symmetric adjacency matrix A_bone in R^(33 x 33)
    representing the physical musculoskeletal connectivity of human anatomy.
    Includes self-loops.
    """
    import numpy as np
    A = np.eye(NUM_LANDMARKS, dtype=np.float32)
    for u, v in ANATOMICAL_BONES:
        A[u, v] = 1.0
        A[v, u] = 1.0
    return A
