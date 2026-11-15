"""
Visibility gating and confidence thresholding.
"""
from typing import List, Dict, Tuple, Optional
from core.models.landmark import Landmark, STANDARD_JOINT_TRIPLETS


def is_joint_measurable(
    landmarks: List[Landmark],
    triplet: Tuple[int, int, int],
    confidence_threshold: float = 0.55
) -> bool:
    """
    Checks if all required keypoints for a joint angle have visibility above threshold.
    """
    p1, p2, p3 = triplet
    for idx in (p1, p2, p3):
        if idx == -1:
            continue
        if idx >= len(landmarks) or landmarks[idx].visibility < confidence_threshold:
            return False
    return True


def check_required_joints_visible(
    landmarks: List[Landmark],
    required_joint_names: List[str],
    confidence_threshold: float = 0.55
) -> Tuple[bool, List[str]]:
    """
    Validates whether all required exercise joints are visible in frame.
    Returns (all_visible, missing_joints_list).
    """
    missing = []
    for joint_name in required_joint_names:
        triplet = STANDARD_JOINT_TRIPLETS.get(joint_name)
        if triplet and not is_joint_measurable(landmarks, triplet, confidence_threshold):
            missing.append(joint_name)
    return len(missing) == 0, missing
