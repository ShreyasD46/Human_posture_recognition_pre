"""
Dynamic Ghost Reference Skeleton Retargeting Engine.
Calibrates to user's body proportions and projects ideal phase angles
via forward kinematics anchored at stable joint.
"""
import math
from typing import Dict, List, Tuple, Optional
from core.models.landmark import Landmark, LandmarkIndex, SKELETON_CONNECTIONS
from core.math.angles import calculate_distance


class GhostSkeletonGenerator:
    """
    Generates a reference 'Ghost' skeleton matched to the user's exact limb proportions.
    Anchors at the user's current root position and projects ideal joint angles.
    """

    def __init__(self):
        self.calibrated_lengths: Dict[Tuple[int, int], float] = {}
        self.is_calibrated: bool = False

    def calibrate(self, user_landmarks: List[Landmark]):
        """
        Calculates user's personal bone segment lengths from clear frames.
        """
        if len(user_landmarks) < 29:
            return

        key_bones = [
            (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.RIGHT_SHOULDER),
            (LandmarkIndex.LEFT_HIP, LandmarkIndex.RIGHT_HIP),
            (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_HIP),
            (LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_HIP),
            (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_ELBOW),
            (LandmarkIndex.LEFT_ELBOW, LandmarkIndex.LEFT_WRIST),
            (LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_ELBOW),
            (LandmarkIndex.RIGHT_ELBOW, LandmarkIndex.RIGHT_WRIST),
            (LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_KNEE),
            (LandmarkIndex.LEFT_KNEE, LandmarkIndex.LEFT_ANKLE),
            (LandmarkIndex.RIGHT_HIP, LandmarkIndex.RIGHT_KNEE),
            (LandmarkIndex.RIGHT_KNEE, LandmarkIndex.RIGHT_ANKLE),
        ]

        for u, v in key_bones:
            dist = calculate_distance(user_landmarks[u], user_landmarks[v])
            if dist > 0.01:
                self.calibrated_lengths[(min(u, v), max(u, v))] = dist

        if len(self.calibrated_lengths) >= 8:
            self.is_calibrated = True

    def get_bone_length(self, u: int, v: int, default: float = 0.15) -> float:
        key = (min(u, v), max(u, v))
        return self.calibrated_lengths.get(key, default)

    def generate_ghost(
        self,
        user_landmarks: List[Landmark],
        target_angles: Dict[str, float],
        anchor_joint: str = "mid_hip"
    ) -> List[Landmark]:
        """
        Generates the 33-landmark ghost skeleton for the current frame.
        target_angles: dict of joint_name -> ideal_angle (degrees)
        anchor_joint: 'mid_hip' | 'left_shoulder' | 'left_foot' | 'mid_shoulder'
        """
        if not user_landmarks or len(user_landmarks) < 33:
            return []

        # If not calibrated yet, calibrate on current frame
        if not self.is_calibrated:
            self.calibrate(user_landmarks)

        # Clone user landmarks as initial baseline
        ghost = [Landmark(x=lm.x, y=lm.y, z=lm.z, visibility=0.85) for lm in user_landmarks]

        # Determine anchor position from user
        if anchor_joint == "mid_hip":
            root_x = 0.5 * (user_landmarks[LandmarkIndex.LEFT_HIP].x + user_landmarks[LandmarkIndex.RIGHT_HIP].x)
            root_y = 0.5 * (user_landmarks[LandmarkIndex.LEFT_HIP].y + user_landmarks[LandmarkIndex.RIGHT_HIP].y)
        elif anchor_joint == "left_shoulder":
            root_x = user_landmarks[LandmarkIndex.LEFT_SHOULDER].x
            root_y = user_landmarks[LandmarkIndex.LEFT_SHOULDER].y
        else:
            root_x = 0.5 * (user_landmarks[LandmarkIndex.LEFT_SHOULDER].x + user_landmarks[LandmarkIndex.RIGHT_SHOULDER].x)
            root_y = 0.5 * (user_landmarks[LandmarkIndex.LEFT_SHOULDER].y + user_landmarks[LandmarkIndex.RIGHT_SHOULDER].y)

        # Forward Kinematics: Adjust Arms according to target elbow / shoulder angles
        # Left Arm:
        if "left_elbow" in target_angles:
            target_elbow_angle = target_angles["left_elbow"]
            # Bone lengths
            l_upper = self.get_bone_length(LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_ELBOW, 0.16)
            l_forearm = self.get_bone_length(LandmarkIndex.LEFT_ELBOW, LandmarkIndex.LEFT_WRIST, 0.14)

            # Keep shoulder at user's current shoulder
            shldr = ghost[LandmarkIndex.LEFT_SHOULDER]
            # Angle of upper arm relative to downward vertical (default ~15 deg down)
            shoulder_deg = target_angles.get("left_shoulder", 20.0)
            rad_shldr = math.radians(90.0 + shoulder_deg)

            elbow_x = shldr.x + l_upper * math.cos(rad_shldr)
            elbow_y = shldr.y + l_upper * math.sin(rad_shldr)
            ghost[LandmarkIndex.LEFT_ELBOW].x = elbow_x
            ghost[LandmarkIndex.LEFT_ELBOW].y = elbow_y

            # Forearm rotated by target elbow flexion
            rad_elbow = rad_shldr - math.radians(180.0 - target_elbow_angle)
            wrist_x = elbow_x + l_forearm * math.cos(rad_elbow)
            wrist_y = elbow_y + l_forearm * math.sin(rad_elbow)
            ghost[LandmarkIndex.LEFT_WRIST].x = wrist_x
            ghost[LandmarkIndex.LEFT_WRIST].y = wrist_y

        # Right Arm (Symmetric if target provided)
        if "right_elbow" in target_angles:
            target_r_elbow = target_angles["right_elbow"]
            l_upper_r = self.get_bone_length(LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_ELBOW, 0.16)
            l_forearm_r = self.get_bone_length(LandmarkIndex.RIGHT_ELBOW, LandmarkIndex.RIGHT_WRIST, 0.14)

            shldr_r = ghost[LandmarkIndex.RIGHT_SHOULDER]
            shoulder_r_deg = target_angles.get("right_shoulder", 20.0)
            rad_shldr_r = math.radians(90.0 - shoulder_r_deg)

            elbow_rx = shldr_r.x - l_upper_r * math.cos(rad_shldr_r)
            elbow_ry = shldr_r.y + l_upper_r * math.sin(rad_shldr_r)
            ghost[LandmarkIndex.RIGHT_ELBOW].x = elbow_rx
            ghost[LandmarkIndex.RIGHT_ELBOW].y = elbow_ry

            rad_elbow_r = rad_shldr_r - math.radians(180.0 - target_r_elbow)
            wrist_rx = elbow_rx - l_forearm_r * math.cos(rad_elbow_r)
            wrist_ry = elbow_ry + l_forearm_r * math.sin(rad_elbow_r)
            ghost[LandmarkIndex.RIGHT_WRIST].x = wrist_rx
            ghost[LandmarkIndex.RIGHT_WRIST].y = wrist_ry

        # Left Knee (Squats, Pushups, Warrior II):
        if "left_knee" in target_angles:
            target_knee_angle = target_angles["left_knee"]
            l_thigh = self.get_bone_length(LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_KNEE, 0.22)
            l_shin = self.get_bone_length(LandmarkIndex.LEFT_KNEE, LandmarkIndex.LEFT_ANKLE, 0.22)

            hip = ghost[LandmarkIndex.LEFT_HIP]
            knee_rad = math.radians(90.0 + (180.0 - target_knee_angle) * 0.5)

            knee_x = hip.x + l_thigh * math.cos(knee_rad) * 0.5
            knee_y = hip.y + l_thigh * math.sin(knee_rad)
            ghost[LandmarkIndex.LEFT_KNEE].x = knee_x
            ghost[LandmarkIndex.LEFT_KNEE].y = knee_y

            ankle_y = knee_y + l_shin
            ghost[LandmarkIndex.LEFT_ANKLE].y = min(0.98, ankle_y)

        return ghost
