import os
import sys
import torch
import torch.optim as optim
import numpy as np
from tqdm import tqdm

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.pytorch_model import SthiraPhysGNN
from ml.pytorch_losses import PhysGNNLosses
from ml.biomechanics import get_anatomical_adjacency_matrix
from ml.train import generate_synthetic_yoga_dataset

def prepare_data(num_sequences_per_pose=20, seq_len=45):
    print("Generating synthetic yoga dataset...")
    raw_data = generate_synthetic_yoga_dataset(num_sequences_per_pose=num_sequences_per_pose, seq_len=seq_len)
    
    # We want sliding windows of size T=5 for the ST-GNN
    window_size = 5
    
    X = []
    Y = []
    
    for item in raw_data:
        raw_seq = item["raw_sequence"] # (seq_len, 33, 4)
        gt_seq = item["gt_sequence"]   # (seq_len, 33, 3)
        
        # Create sliding windows
        for t in range(seq_len - window_size + 1):
            X.append(raw_seq[t : t + window_size])
            Y.append(gt_seq[t : t + window_size])
            
    X = np.stack(X)
    Y = np.stack(Y)
    
    # Shuffle
    idx = np.random.permutation(len(X))
    X = X[idx]
    Y = Y[idx]
    
    # Split train/val (80/20)
    split = int(0.8 * len(X))
    
    X_train, Y_train = torch.tensor(X[:split], dtype=torch.float32), torch.tensor(Y[:split], dtype=torch.float32)
    X_val, Y_val = torch.tensor(X[split:], dtype=torch.float32), torch.tensor(Y[split:], dtype=torch.float32)
    
    return X_train, Y_train, X_val, Y_val

def train_model():
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    X_train, Y_train, X_val, Y_val = prepare_data()
    
    train_dataset = torch.utils.data.TensorDataset(X_train, Y_train)
    val_dataset = torch.utils.data.TensorDataset(X_val, Y_val)
    
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32)
    
    A_bone = get_anatomical_adjacency_matrix()
    model = SthiraPhysGNN(A_bone=A_bone).to(device)
    
    criterion = PhysGNNLosses().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    epochs = 20
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_coord = 0.0
        train_bone = 0.0
        train_rom = 0.0
        train_smooth = 0.0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
        for batch_X, batch_Y in pbar:
            batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            
            loss, l_coord, l_bone, l_rom, l_smooth = criterion(outputs, batch_Y)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            train_loss += loss.item() * batch_X.size(0)
            train_coord += l_coord.item() * batch_X.size(0)
            train_bone += l_bone.item() * batch_X.size(0)
            train_rom += l_rom.item() * batch_X.size(0)
            train_smooth += l_smooth.item() * batch_X.size(0)
            
            pbar.set_postfix({'loss': loss.item()})
            
        train_loss /= len(train_loader.dataset)
        train_coord /= len(train_loader.dataset)
        train_bone /= len(train_loader.dataset)
        train_rom /= len(train_loader.dataset)
        train_smooth /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_Y in val_loader:
                batch_X, batch_Y = batch_X.to(device), batch_Y.to(device)
                outputs = model(batch_X)
                loss, _, _, _, _ = criterion(outputs, batch_Y)
                val_loss += loss.item() * batch_X.size(0)
                
        val_loss /= len(val_loader.dataset)
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch+1} - Train Loss: {train_loss:.4f} (Coord: {train_coord:.4f}, Bone: {train_bone:.4f}, ROM: {train_rom:.4f}, Smooth: {train_smooth:.4f}) | Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "sthira_physgnn_best.pt")
            
    print("Training complete. Exporting to ONNX...")
    export_to_onnx(device)

def export_to_onnx(device):
    A_bone = get_anatomical_adjacency_matrix()
    model = SthiraPhysGNN(A_bone=A_bone).to(device)
    model.load_state_dict(torch.load("sthira_physgnn_best.pt", map_location=device, weights_only=True))
    model.eval()
    
    # Dummy input: (Batch=1, Time=5, Joints=33, Channels=4)
    dummy_input = torch.randn(1, 5, 33, 4, device=device)
    
    onnx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "sthira_physgnn.onnx")
    
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path, 
        export_params=True, 
        opset_version=14, 
        do_constant_folding=True,
        input_names=['input_tensor'],
        output_names=['output_tensor'],
        dynamic_axes={'input_tensor': {0: 'batch_size'}, 'output_tensor': {0: 'batch_size'}}
    )
    print(f"Model exported to {onnx_path}")

if __name__ == "__main__":
    train_model()
