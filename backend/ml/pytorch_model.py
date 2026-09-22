import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class STGCN_Block(nn.Module):
    def __init__(self, in_channels, out_channels, A, dropout=0.3):
        super(STGCN_Block, self).__init__()
        # A: (V, V) adjacency matrix
        self.register_buffer('A', torch.tensor(A, dtype=torch.float32))
        self.gcn = nn.Conv1d(in_channels, out_channels, kernel_size=1)
        self.tcn = nn.Conv2d(out_channels, out_channels, kernel_size=(3, 1), padding=(1, 0))
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # x: (N, C, T, V)
        N, C, T, V = x.size()
        # Spatial Graph Convolution
        x = x.permute(0, 2, 1, 3).contiguous().view(N * T, C, V) # (N*T, C, V)
        x = self.gcn(x) # (N*T, out_C, V)
        x = torch.matmul(x, self.A) # (N*T, out_C, V)
        x = x.view(N, T, -1, V).permute(0, 2, 1, 3).contiguous() # (N, out_C, T, V)
        
        # Temporal Convolution
        x = self.tcn(x)
        x = self.relu(x)
        x = self.dropout(x)
        return x

class DynamicAttentionBlock(nn.Module):
    def __init__(self, in_channels, V=33):
        super(DynamicAttentionBlock, self).__init__()
        self.W_q = nn.Linear(in_channels, in_channels // 2)
        self.W_k = nn.Linear(in_channels, in_channels // 2)
        self.scale = (in_channels // 2) ** 0.5
        
    def forward(self, x):
        # x: (N, C, T, V)
        N, C, T, V = x.size()
        # Average over time for attention weights
        x_mean = x.mean(dim=2) # (N, C, V)
        x_mean = x_mean.permute(0, 2, 1) # (N, V, C)
        
        Q = self.W_q(x_mean) # (N, V, C/2)
        K = self.W_k(x_mean) # (N, V, C/2)
        
        # Compute dynamic adjacency: A_dyn = Softmax(Q * K^T / sqrt(d))
        scores = torch.bmm(Q, K.transpose(1, 2)) / self.scale # (N, V, V)
        A_dyn = F.softmax(scores, dim=-1) # (N, V, V)
        
        # Apply A_dyn
        x_flat = x.permute(0, 1, 3, 2).contiguous().view(N, C, V * T) # (N, C, V*T)
        A_dyn_expanded = A_dyn.unsqueeze(1).expand(-1, C, -1, -1) # (N, C, V, V)
        
        out = torch.zeros_like(x)
        for b in range(N):
            out[b] = torch.matmul(A_dyn[b], x[b].permute(1, 2, 0)).permute(2, 0, 1)
        
        return out, A_dyn

class SthiraPhysGNN(nn.Module):
    def __init__(self, num_nodes=33, in_channels=4, hidden_channels=32, A_bone=None):
        super(SthiraPhysGNN, self).__init__()
        
        if A_bone is None:
            # Create a dummy identity matrix if none provided, but we expect A_bone
            A_bone = np.eye(num_nodes)
            
        # Normalize A_bone
        d = np.sum(A_bone, axis=1)
        d_inv = np.zeros_like(d, dtype=np.float32)
        d_inv[d > 0] = 1.0 / np.sqrt(d[d > 0])
        D_mat = np.diag(d_inv)
        A_norm = D_mat @ A_bone @ D_mat
        self.register_buffer('A_bone', torch.tensor(A_norm, dtype=torch.float32))
        
        self.data_bn = nn.BatchNorm1d(in_channels * num_nodes)
        
        # Learnable alpha to balance static bone graph and dynamic attention
        self.alpha = nn.Parameter(torch.tensor(0.7))
        
        self.stgcn_1 = STGCN_Block(in_channels, hidden_channels, A_norm)
        self.attention = DynamicAttentionBlock(hidden_channels, num_nodes)
        self.stgcn_2 = STGCN_Block(hidden_channels, hidden_channels, A_norm)
        
        # Output layer maps back to (X, Y, Z) coordinates (3 channels)
        self.out_conv = nn.Conv2d(hidden_channels, 3, kernel_size=1)
        
    def forward(self, x):
        # x shape: (N, T, V, C) -> input from MediaPipe (N=batch, T=time, V=33 joints, C=4 coords+vis)
        N, T, V, C = x.size()
        
        # Center coordinates relative to root (mid-hip: avg of 23 and 24)
        root = (x[:, :, 23, :3] + x[:, :, 24, :3]) / 2.0 # (N, T, 3)
        root = root.unsqueeze(2).expand(-1, -1, V, -1) # (N, T, V, 3)
        x_centered = x.clone()
        x_centered[:, :, :, :3] = x[:, :, :, :3] - root
        
        # Prepare for PyTorch channels-first: (N, C, T, V)
        x_in = x_centered.permute(0, 3, 1, 2).contiguous()
        
        # Batch norm
        x_in_bn = x_in.view(N, C * V, T)
        x_in_bn = self.data_bn(x_in_bn)
        x_in_bn = x_in_bn.view(N, C, T, V)
        
        # Block 1
        h1 = self.stgcn_1(x_in_bn)
        
        # Dynamic Attention
        h_dyn, A_dyn = self.attention(h1)
        
        # Blend graphs (using alpha)
        # We manually apply the blended graph convolution here
        h_blend = self.alpha * h1 + (1 - self.alpha) * h_dyn
        
        # Block 2
        h2 = self.stgcn_2(h_blend)
        
        # Map to 3D space
        out_residuals = self.out_conv(h2) # (N, 3, T, V)
        
        # Back to (N, T, V, 3)
        out_residuals = out_residuals.permute(0, 2, 3, 1).contiguous()
        
        # Add root back (residual connection on original coordinates)
        # We use a residual connection from the original noisy coordinates + the GNN learned refinement
        out_coords = x[:, :, :, :3] + 0.15 * out_residuals
        
        return out_coords
