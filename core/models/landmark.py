"""
Landmark models, MediaPipe 33-keypoint topology, and PoseResult schemas.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import numpy as np


class LandmarkIndex:
    # Face
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

    # Upper Body
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

    # Lower Body
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


# Human Skeleton Topological Connections for Rendering
SKELETON_CONNECTIONS: List[Tuple[int, int]] = [
    # Torso
    (11, 12), (11, 23), (12, 24), (23, 24),
    # Left Arm
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    # Right Arm
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
    # Left Leg
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    # Right Leg
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
    # Head / Neck
    (9, 10), (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8)
]


# Standard named joint triplets [p1, vertex, p2]
STANDARD_JOINT_TRIPLETS: Dict[str, Tuple[int, int, int]] = {
    # Left arm
    "left_elbow": (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_ELBOW, LandmarkIndex.LEFT_WRIST),
    "left_shoulder": (LandmarkIndex.LEFT_ELBOW, LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_HIP),
    "left_shoulder_lateral": (LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_ELBOW),
    
    # Right arm
    "right_elbow": (LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_ELBOW, LandmarkIndex.RIGHT_WRIST),
    "right_shoulder": (LandmarkIndex.RIGHT_ELBOW, LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_HIP),
    "right_shoulder_lateral": (LandmarkIndex.RIGHT_HIP, LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_ELBOW),
    
    # Left leg
    "left_knee": (LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_KNEE, LandmarkIndex.LEFT_ANKLE),
    "left_hip": (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_KNEE),
    
    # Right leg
    "right_knee": (LandmarkIndex.RIGHT_HIP, LandmarkIndex.RIGHT_KNEE, LandmarkIndex.RIGHT_ANKLE),
    "right_hip": (LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_HIP, LandmarkIndex.RIGHT_KNEE),
    
    # Spine & Torso
    "left_spine": (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_KNEE),
    "right_spine": (LandmarkIndex.RIGHT_SHOULDER, LandmarkIndex.RIGHT_HIP, LandmarkIndex.RIGHT_KNEE),
    "neck_inclination": (LandmarkIndex.LEFT_SHOULDER, LandmarkIndex.LEFT_EAR, -1),   # special vertical vector
    "torso_inclination": (LandmarkIndex.LEFT_HIP, LandmarkIndex.LEFT_SHOULDER, -1), # special vertical vector
}


@dataclass
class Landmark:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0

    def to_dict(self) -> dict:
        return {"x": round(self.x, 5), "y": round(self.y, 5), "z": round(self.z, 5), "visibility": round(self.visibility, 3)}

    @classmethod
    def from_dict(cls, data: dict) -> "Landmark":
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z=float(data.get("z", 0.0)),
            visibility=float(data.get("visibility", 1.0))
        )


@dataclass
class PoseResult:
    landmarks: List[Landmark] = field(default_factory=list)
    world_landmarks: Optional[List[Landmark]] = None
    inference_time_ms: float = 0.0
    is_detected: bool = False

    def to_dict(self) -> dict:
        return {
            "landmarks": [lm.to_dict() for lm in self.landmarks],
            "inference_time_ms": round(self.inference_time_ms, 2),
            "is_detected": self.is_detected
        }
