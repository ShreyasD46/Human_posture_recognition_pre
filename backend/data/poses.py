"""
Reference angle data for the 5 MVP poses (standing / front-facing only).
Angles are approximate biomechanical targets drawn from standard yoga
alignment cues (front-camera visible joints only). tolerance is in degrees.

joint_triplet keys use MediaPipe BlazePose 33-landmark indices:
11 L shoulder, 12 R shoulder, 13 L elbow, 14 R elbow, 15 L wrist, 16 R wrist,
23 L hip, 24 R hip, 25 L knee, 26 R knee, 27 L ankle, 28 R ankle.

weight: per-joint importance factor; weights sum to 1.0 per pose.
        Highest weight = most critical for injury avoidance / pose intent.
"""

POSES = {
    "tadasana": {
        "label": "Tadasana (Mountain Pose)",
        "instructions": "Stand tall, feet hip-width apart, arms relaxed at your sides, "
                         "spine long, shoulders stacked over hips.",
        "hold_time_target": 15,
        "keypoint_angles": [
            {"name": "left_knee",       "triplet": [23, 25, 27], "ideal": 178, "tolerance": 8,
             "weight": 0.20, "feedback": "Soften your knees, don't lock them"},
            {"name": "right_knee",      "triplet": [24, 26, 28], "ideal": 178, "tolerance": 8,
             "weight": 0.20, "feedback": "Soften your knees, don't lock them"},
            {"name": "spine_lean",      "triplet": [11, 23, 25], "ideal": 178, "tolerance": 10,
             "weight": 0.40, "feedback": "Stand tall, stack your shoulders over your hips"},
            {"name": "shoulder_level",  "triplet": [13, 11, 12], "ideal": 95,  "tolerance": 15,
             "weight": 0.20, "feedback": "Relax your shoulders down and back"},
        ],
    },
    "vrikshasana": {
        "label": "Vrikshasana (Tree Pose)",
        "instructions": "Balance on one leg, place the sole of the other foot on your inner "
                         "thigh or calf, palms together at your chest.",
        "hold_time_target": 20,
        "keypoint_angles": [
            {"name": "standing_knee",   "triplet": [23, 25, 27], "ideal": 178, "tolerance": 8,
             "weight": 0.45, "feedback": "Keep your standing leg strong and straight"},
            {"name": "lifted_hip_knee", "triplet": [24, 26, 28], "ideal": 45,  "tolerance": 20,
             "weight": 0.30, "feedback": "Press your lifted foot into your thigh, open the hip"},
            {"name": "torso_upright",   "triplet": [11, 23, 25], "ideal": 178, "tolerance": 12,
             "weight": 0.25, "feedback": "Lengthen your spine, avoid leaning to one side"},
        ],
    },
    "trikonasana": {
        "label": "Trikonasana (Triangle Pose)",
        "instructions": "Feet wide apart, front foot forward, hinge at the hip over the "
                         "front leg, one hand down, the other reaching up.",
        "hold_time_target": 15,
        "keypoint_angles": [
            {"name": "front_knee",      "triplet": [23, 25, 27], "ideal": 175, "tolerance": 10,
             "weight": 0.35, "feedback": "Keep your front leg straight, don't bend the knee"},
            {"name": "hip_hinge",       "triplet": [11, 23, 25], "ideal": 100, "tolerance": 15,
             "weight": 0.35, "feedback": "Hinge deeper from your hip, lengthen your spine"},
            {"name": "top_arm_line",    "triplet": [15, 11, 23], "ideal": 175, "tolerance": 15,
             "weight": 0.30, "feedback": "Stack your top arm straight up, open your chest"},
        ],
    },
    "virabhadrasana_ii": {
        "label": "Virabhadrasana II (Warrior II)",
        "instructions": "Front knee bent over the ankle, back leg straight, arms extended "
                         "parallel to the floor, gaze over the front hand.",
        "hold_time_target": 20,
        "keypoint_angles": [
            {"name": "front_knee_bend",   "triplet": [23, 25, 27], "ideal": 90,  "tolerance": 15,
             "weight": 0.40, "feedback": "Bend your front knee to a right angle, over the ankle"},
            {"name": "back_leg_straight", "triplet": [24, 26, 28], "ideal": 175, "tolerance": 10,
             "weight": 0.30, "feedback": "Straighten your back leg fully"},
            {"name": "arm_line",          "triplet": [13, 11, 12], "ideal": 178, "tolerance": 12,
             "weight": 0.30, "feedback": "Extend both arms level, reach through your fingertips"},
        ],
    },
    "utkatasana": {
        "label": "Utkatasana (Chair Pose)",
        "instructions": "Bend your knees as if sitting in a chair, weight in your heels, "
                         "arms reaching overhead, spine long.",
        "hold_time_target": 15,
        "keypoint_angles": [
            {"name": "knee_bend",      "triplet": [23, 25, 27], "ideal": 115, "tolerance": 15,
             "weight": 0.35, "feedback": "Sit deeper, bend your knees more"},
            {"name": "torso_lean",     "triplet": [11, 23, 25], "ideal": 150, "tolerance": 15,
             "weight": 0.35, "feedback": "Lean your chest forward slightly, keep your spine long"},
            {"name": "arms_overhead",  "triplet": [23, 11, 15], "ideal": 170, "tolerance": 15,
             "weight": 0.30, "feedback": "Reach your arms further overhead, by your ears"},
        ],
    },
}
