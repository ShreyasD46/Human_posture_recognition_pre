"""
Physics-Informed Loss Engine for Sthira-PhysGNN.
Formulates:
1. Coordinate L1/MSE Loss (reconstruction fidelity)
2. Geodesic Bone-Length Invariance Loss (penalizes bone stretching/shrinking)
3. Orthopedic Range of Motion (ROM) Barrier Loss (penalizes hyperextension/anatomical violations)
4. Dynamic Temporal Smoothness Loss (penalizes jitter acceleration)
"""
import numpy as np
from ml.biomechanics import (
    ANATOMICAL_BONES,
    ORTHOPEDIC_ROM_LIMITS,
    NUM_LANDMARKS,
)

class PhysGNNLosses:
    """
    Computes biomechanical and kinematic loss terms for both training backprop
    and offline evaluation / ablation analysis.
    """

    def __init__(
        self,
        lambda_bone: float = 2.5,
        lambda_rom: float = 3.0,
        lambda_smooth: float = 1.5,
    ):
        self.lambda_bone = lambda_bone
        self.lambda_rom = lambda_rom
        self.lambda_smooth = lambda_smooth

    @staticmethod
    def compute_angle_3d(a, b, c, eps=1e-7):
        """
        Calculates the 3D joint angle at vertex b between vectors (a - b) and (c - b).
        Supports NumPy arrays of shape (..., 3).
        """
        ba = a - b
        bc = c - b
        dot = np.sum(ba * bc, axis=-1)
        norm_ba = np.linalg.norm(ba, axis=-1)
        norm_bc = np.linalg.norm(bc, axis=-1)
        denom = norm_ba * norm_bc + eps
        cos_theta = np.clip(dot / denom, -1.0, 1.0)
        return np.degrees(np.arccos(cos_theta))

    def bone_length_invariance_loss(self, pred_seq, ref_bone_lengths):
        """
        pred_seq: (T, 33, 3) - predicted 3D metric landmark coordinates over T frames.
        ref_bone_lengths: dict (u, v) -> float (calibrated baseline length).
        Penalizes any variance in bone length across time.
        """
        T = pred_seq.shape[0]
        loss = 0.0
        count = 0
        for u, v in ANATOMICAL_BONES:
            diff = pred_seq[:, u, :] - pred_seq[:, v, :]  # (T, 3)
            lengths = np.linalg.norm(diff, axis=-1)       # (T,)
            if (u, v) in ref_bone_lengths:
                target = ref_bone_lengths[(u, v)]
                # Relative fractional stretching penalty
                loss += np.mean(((lengths - target) / (target + 1e-6)) ** 2)
            else:
                # Variance penalty across the window
                loss += np.var(lengths)
            count += 1
        return (loss / max(1, count)) * self.lambda_bone

    def orthopedic_rom_barrier_loss(self, pred_coords):
        """
        pred_coords: (..., 33, 3)
        Checks if joint angles exceed AAOS anatomical limits.
        Uses quadratic barrier penalty: max(0, theta - max)^2 + max(0, min - theta)^2
        """
        loss = 0.0
        count = 0
        for joint_key, rom in ORTHOPEDIC_ROM_LIMITS.items():
            u, v, w = rom["triplet"]
            p_u = pred_coords[..., u, :]
            p_v = pred_coords[..., v, :]
            p_w = pred_coords[..., w, :]
            angle = self.compute_angle_3d(p_u, p_v, p_w)

            min_limit = rom["min_deg"]
            max_limit = rom["max_deg"]

            under_penalty = np.maximum(0.0, min_limit - angle) ** 2
            over_penalty = np.maximum(0.0, angle - max_limit) ** 2

            loss += np.mean(under_penalty + over_penalty)
            count += 1

        return (loss / max(1, count)) * self.lambda_rom

    def temporal_smoothness_loss(self, pred_seq):
        """
        pred_seq: (T, 33, 3) where T >= 3.
        Penalizes second-order discrete derivative (acceleration noise / high-frequency jitter).
        d^2 P / dt^2 = P_t - 2*P_{t-1} + P_{t-2}
        """
        if pred_seq.shape[0] < 3:
            return 0.0
        # Acceleration: pred[2:] - 2*pred[1:-1] + pred[:-2]
        accel = pred_seq[2:] - 2.0 * pred_seq[1:-1] + pred_seq[:-2]
        loss = np.mean(accel ** 2)
        return loss * self.lambda_smooth

    def evaluate_total_loss(self, pred_seq, gt_seq, ref_bone_lengths):
        """
        Computes the complete loss breakdown for research telemetry.
        """
        # Reconstruction error (MSE / Smooth L1)
        l_coord = np.mean((pred_seq - gt_seq) ** 2)
        l_bone = self.bone_length_invariance_loss(pred_seq, ref_bone_lengths)
        l_rom = self.orthopedic_rom_barrier_loss(pred_seq)
        l_smooth = self.temporal_smoothness_loss(pred_seq)
        total = l_coord + l_bone + l_rom + l_smooth

        return {
            "total_loss": float(total),
            "coord_loss": float(l_coord),
            "bone_invariance_loss": float(l_bone),
            "rom_barrier_loss": float(l_rom),
            "temporal_smoothness_loss": float(l_smooth),
        }
