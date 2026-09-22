import torch
import torch.nn as nn
from ml.biomechanics import ANATOMICAL_BONES, ORTHOPEDIC_ROM_LIMITS

class PhysGNNLosses(nn.Module):
    def __init__(self, lambda_bone=2.5, lambda_rom=3.0, lambda_smooth=1.5):
        super(PhysGNNLosses, self).__init__()
        self.lambda_bone = lambda_bone
        self.lambda_rom = lambda_rom
        self.lambda_smooth = lambda_smooth
        self.smooth_l1 = nn.SmoothL1Loss(beta=0.01) # 1cm beta for Huber loss

    def compute_angle_3d_torch(self, a, b, c, eps=1e-7):
        """
        Calculates the 3D joint angle at vertex b between vectors (a - b) and (c - b) in PyTorch.
        Inputs: (N, T, 3)
        Returns: (N, T) in degrees
        """
        ba = a - b
        bc = c - b
        
        dot = torch.sum(ba * bc, dim=-1)
        norm_ba = torch.norm(ba, dim=-1)
        norm_bc = torch.norm(bc, dim=-1)
        
        denom = norm_ba * norm_bc + eps
        cos_theta = torch.clamp(dot / denom, -1.0, 1.0)
        
        # arccos in radians -> multiply by 180/pi to get degrees
        return torch.acos(cos_theta) * (180.0 / 3.141592653589793)

    def bone_length_invariance_loss(self, pred_seq, ref_bone_lengths=None):
        """
        pred_seq: (N, T, V, 3)
        ref_bone_lengths: None (for relative variance over time)
        """
        N, T, V, C = pred_seq.size()
        loss = torch.tensor(0.0, device=pred_seq.device)
        count = 0
        
        for u, v in ANATOMICAL_BONES:
            diff = pred_seq[:, :, u, :] - pred_seq[:, :, v, :] # (N, T, 3)
            lengths = torch.norm(diff, dim=-1) # (N, T)
            
            # Variance penalty across the temporal window
            # We want the variance of each bone length over time to be 0
            var = torch.var(lengths, dim=1) # (N,)
            loss += torch.mean(var)
            count += 1
            
        return (loss / max(1, count)) * self.lambda_bone

    def orthopedic_rom_barrier_loss(self, pred_coords):
        """
        pred_coords: (N, T, V, 3)
        """
        loss = torch.tensor(0.0, device=pred_coords.device)
        count = 0
        
        for joint_key, rom in ORTHOPEDIC_ROM_LIMITS.items():
            u, v, w = rom["triplet"]
            p_u = pred_coords[:, :, u, :]
            p_v = pred_coords[:, :, v, :]
            p_w = pred_coords[:, :, w, :]
            
            angle = self.compute_angle_3d_torch(p_u, p_v, p_w) # (N, T)
            
            min_limit = rom["min_deg"]
            max_limit = rom["max_deg"]
            
            under_penalty = torch.relu(min_limit - angle) ** 2
            over_penalty = torch.relu(angle - max_limit) ** 2
            
            loss += torch.mean(under_penalty + over_penalty)
            count += 1
            
        return (loss / max(1, count)) * self.lambda_rom

    def temporal_smoothness_loss(self, pred_seq):
        """
        pred_seq: (N, T, V, 3) where T >= 3
        d^2 P / dt^2 = P_t - 2*P_{t-1} + P_{t-2}
        """
        if pred_seq.size(1) < 3:
            return torch.tensor(0.0, device=pred_seq.device)
            
        accel = pred_seq[:, 2:, :, :] - 2.0 * pred_seq[:, 1:-1, :, :] + pred_seq[:, :-2, :, :]
        loss = torch.mean(accel ** 2)
        return loss * self.lambda_smooth

    def forward(self, pred_seq, gt_seq):
        """
        Evaluates the combined physics-informed loss.
        """
        l_coord = self.smooth_l1(pred_seq, gt_seq)
        l_bone = self.bone_length_invariance_loss(pred_seq)
        l_rom = self.orthopedic_rom_barrier_loss(pred_seq)
        l_smooth = self.temporal_smoothness_loss(pred_seq)
        
        total = l_coord + l_bone + l_rom + l_smooth
        return total, l_coord, l_bone, l_rom, l_smooth
