"""
High-performance biomechanical angle and Euclidean vector mathematics.
Zero external allocations in hot path.
"""
import math
from typing import Dict, Tuple, Optional, Union
from core.models.landmark import Landmark, LandmarkIndex


def calculate_angle_3d(a: Landmark, b: Landmark, c: Landmark) -> Optional[float]:
    """
    Computes true 3D Euclidean joint angle at vertex b formed by rays b->a and b->c.
    Eliminates monocular planar foreshortening artifacts.
    Returns angle in degrees [0, 180].
    """
    ax, ay, az = a.x - b.x, a.y - b.y, a.z - b.z
    cx, cy, cz = c.x - b.x, c.y - b.y, c.z - b.z

    dot = ax * cx + ay * cy + az * cz
    mag_a = math.sqrt(ax * ax + ay * ay + az * az)
    mag_c = math.sqrt(cx * cx + cy * cy + cz * cz)

    if mag_a * mag_c <= 1e-7:
        return None

    cos_val = dot / (mag_a * mag_c)
    cos_val = max(-1.0, min(1.0, cos_val))
    return math.degrees(math.acos(cos_val))


def calculate_angle_2d(a: Landmark, b: Landmark, c: Landmark) -> Optional[float]:
    """
    Computes planar 2D image-plane angle at vertex b formed by rays b->a and b->c.
    Returns angle in degrees [0, 180].
    """
    ax, ay = a.x - b.x, a.y - b.y
    cx, cy = c.x - b.x, c.y - b.y

    dot = ax * cx + ay * cy
    mag_a = math.hypot(ax, ay)
    mag_c = math.hypot(cx, cy)

    if mag_a * mag_c <= 1e-7:
        return None

    cos_val = dot / (mag_a * mag_c)
    cos_val = max(-1.0, min(1.0, cos_val))
    return math.degrees(math.acos(cos_val))


def calculate_inclination_vertical(p_origin: Landmark, p_target: Landmark) -> float:
    """
    Computes inclination angle (in degrees) of the segment from p_origin to p_target
    relative to a true vertical line directed upward.
    Used for neck inclination and torso posture inclination checks.
    """
    dx = p_target.x - p_origin.x
    dy = p_target.y - p_origin.y  # Note: y points downwards in image coordinates!

    # Vector 1: p_origin to p_target -> (dx, dy)
    # Vector 2: Vertical upward -> (0, -1)
    # dot = -dy
    # mag1 = hypot(dx, dy)
    mag1 = math.hypot(dx, dy)
    if mag1 <= 1e-7:
        return 0.0

    cos_theta = (-dy) / mag1
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))


def calculate_distance(p1: Landmark, p2: Landmark, use_3d: bool = False) -> float:
    """Computes Euclidean distance between two landmarks (normalized coordinates)."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    if use_3d:
        dz = p2.z - p1.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    return math.hypot(dx, dy)


def compute_joint_angle_by_triplet(
    landmarks: list,
    triplet: Tuple[int, int, int],
    use_3d: bool = True
) -> Optional[float]:
    """
    Helper to calculate angle from standard triplet indices.
    If triplet[2] is -1, computes inclination to vertical from triplet[0] to triplet[1].
    """
    p1_idx, vertex_idx, p2_idx = triplet
    if max(p1_idx, vertex_idx) >= len(landmarks):
        return None

    p_a = landmarks[p1_idx]
    p_b = landmarks[vertex_idx]

    if p2_idx == -1:
        # Inclination to vertical
        return calculate_inclination_vertical(p_a, p_b)

    if p2_idx >= len(landmarks):
        return None

    p_c = landmarks[p2_idx]
    if use_3d:
        ang_3d = calculate_angle_3d(p_a, p_b, p_c)
        if ang_3d is not None and not math.isnan(ang_3d):
            return ang_3d
    return calculate_angle_2d(p_a, p_b, p_c)
