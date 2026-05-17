import sqlite3
import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import sys

# Đảm bảo import được các module khác
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.database import get_connection
from predictor.model import TrafficLSTM

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_SAVE_PATH = os.path.join(MODEL_DIR, "lstm_model.pth")
SCALER_SAVE_PATH = os.path.join(MODEL_DIR, "scaler.json")

def load_data_from_db():
    """Tải toàn bộ chuỗi dữ liệu PCU từ CSDL SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT camera_id, timestamp, total_pcu 
    FROM traffic_history 
    ORDER BY camera_id, timestamp ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def prepare_sequences(data, lookback=10, step_ahead=30):
    """
    Xây dựng các chuỗi huấn luyện (sequences).
    - lookback: số bước thời gian quá khứ (ví dụ: 10 bước ~ 5 phút cào)
    - step_ahead: số bước dự đoán trước (ví dụ: 30 bước ~ 15 phút cào với chu kỳ 30s)
    """
    # Gom nhóm dữ liệu theo camera
    camera_data = {}
    for row in data:
        cam_id = row["camera_id"]
        pcu = row["total_pcu"]
        if cam_id not in camera_data:
            camera_data[cam_id] = []
        camera_data[cam_id].append(pcu)
        
    X, y = [], []
    
    for cam_id, pcu_list in camera_data.items():
        if len(pcu_list) < (lookback + step_ahead):
            continue
            
        for i in range(len(pcu_list) - lookback - step_ahead + 1):
            seq = pcu_list[i : i + lookback]
            target = pcu_list[i + lookback + step_ahead - 1]
            X.append(seq)
            y.append(target)
            
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def train_model(epochs=10, batch_size=16, lr=0.005):
    """Huấn luyện mô hình LSTM trên dữ liệu hiện có."""
    print("[*] Đang tải dữ liệu từ CSDL...")
    db_rows = load_data_from_db()
    
    if len(db_rows) < 100:
        print(f"[!] Số lượng mẫu ({len(db_rows)}) quá ít để huấn luyện LSTM. Yêu cầu tối thiểu 100 mẫu.")
        return False
        
    X, y = prepare_sequences(db_rows, lookback=10, step_ahead=15) # Dự đoán trước 15 bước (~7.5 phút)
    
    if len(X) == 0:
        print("[!] Không tạo được chuỗi dữ liệu hợp lệ. Vui lòng cào thêm ảnh snapshots.")
        return False
        
    print(f"[+] Tạo thành công {len(X)} chuỗi huấn luyện.")
    
    # Chuẩn hóa dữ liệu MinMax Scaling [0, 1]
    pcu_min = float(np.min(X))
    pcu_max = float(np.max(X))
    
    # Phòng ngừa chia cho 0
    if pcu_max == pcu_min:
        pcu_max += 1.0
        
    X_scaled = (X - pcu_min) / (pcu_max - pcu_min)
    y_scaled = (y - pcu_min) / (pcu_max - pcu_min)
    
    # Định hình lại đầu vào cho LSTM: (N, Sequence_Length, Input_Dim)
    X_scaled = np.expand_dims(X_scaled, axis=-1)
    
    # Chuyển đổi thành PyTorch Tensors
    X_tensor = torch.tensor(X_scaled)
    y_tensor = torch.tensor(y_scaled).unsqueeze(-1)
    
    # Khởi tạo model LSTM
    model = TrafficLSTM(input_dim=1, hidden_dim=64, num_layers=2, output_dim=1)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    print("[*] Đang huấn luyện TrafficLSTM...")
    model.train()
    
    dataset_size = len(X_tensor)
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        # Huấn luyện theo các Batch nhỏ
        permutation = torch.randperm(dataset_size)
        
        for i in range(0, dataset_size, batch_size):
            indices = permutation[i:i+batch_size]
            batch_x, batch_y = X_tensor[indices], y_tensor[indices]
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * len(batch_x)
            
        avg_loss = epoch_loss / dataset_size
        print(f"    Epoch [{epoch+1}/{epochs}] - Loss: {avg_loss:.6f}")
        
    # Lưu weights mô hình
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    
    # Lưu thông số chuẩn hóa MinMax Scaler để dùng khi dự đoán
    scaler_params = {"min": pcu_min, "max": pcu_max}
    with open(SCALER_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(scaler_params, f)
        
    print(f"[✓] Đã lưu Weights mô hình tại: {MODEL_SAVE_PATH}")
    print(f"[✓] Đã lưu thông số chuẩn hóa tại: {SCALER_SAVE_PATH}")
    return True

if __name__ == "__main__":
    train_model(epochs=5)
