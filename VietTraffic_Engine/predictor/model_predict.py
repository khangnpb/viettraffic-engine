import os
import json
import torch
import numpy as np
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.database import get_camera_history
from predictor.model import TrafficLSTM

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
MODEL_PATH = os.path.join(MODEL_DIR, "lstm_model.pth")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.json")

def predict_future_pcu(camera_id):
    """
    Dự báo mật độ PCU của camera_id sau 15-30 phút tiếp theo.
    - Ưu tiên sử dụng mô hình học sâu PyTorch LSTM đã huấn luyện.
    - Tự động fallback về thuật toán trượt thích ứng kết hợp sin wave tuần hoàn
      nếu chưa có file weights model, đảm bảo hệ thống KHÔNG bao giờ crash.
    """
    # Lấy 10 bước lịch sử gần nhất từ DB
    history = get_camera_history(camera_id, limit=10)
    
    if not history or len(history) < 3:
        # Fallback cơ bản nếu chưa có dữ liệu lịch sử trong DB
        return 0.0, 0.0, "Không có dữ liệu lịch sử"
        
    latest_pcu = history[-1]["total_pcu"]
    
    # Kiểm tra xem có file weights của model LSTM không
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and len(history) >= 10:
        try:
            # Load thông số chuẩn hóa MinMax Scaler
            with open(SCALER_PATH, "r", encoding="utf-8") as f:
                scaler = json.load(f)
                
            pcu_min = scaler["min"]
            pcu_max = scaler["max"]
            
            # Chuẩn bị chuỗi dữ liệu 10 bước gần nhất
            seq = [h["total_pcu"] for h in history]
            seq_scaled = [(x - pcu_min) / (pcu_max - pcu_min) for x in seq]
            
            # Định hình đầu vào tensor PyTorch: (1, Sequence_Length, Input_Dim)
            x_tensor = torch.tensor(seq_scaled, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            
            # Khởi tạo model LSTM và nạp weights
            model = TrafficLSTM(input_dim=1, hidden_dim=64, num_layers=2, output_dim=1)
            model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
            model.eval()
            
            with torch.no_grad():
                pred_scaled = model(x_tensor).item()
                
            # Giải chuẩn hóa (Inverse Scaling)
            pred_pcu = pred_scaled * (pcu_max - pcu_min) + pcu_min
            pred_pcu = max(0.0, round(pred_pcu, 2))
            
            trend = round(pred_pcu - latest_pcu, 2)
            return latest_pcu, pred_pcu, f"Dự báo bằng LSTM (Mô hình học sâu)"
            
        except Exception as e:
            print(f"[!] Lỗi khi chạy inference LSTM: {e}. Đang fallback về giải thuật thích ứng...")
            
    # --- THUẬT TOÁN FALLBACK THÍCH ỨNG (Adaptive Exponential Extrapolation + Sine wave) ---
    # Phù hợp với tính chất giao thông HCMC tuần hoàn, hoạt động tức thì
    pcu_list = [h["total_pcu"] for h in history]
    
    # Tính sai số chênh lệch trung bình giữa các bước gần đây
    diffs = np.diff(pcu_list)
    ema_diff = diffs[-1] if len(diffs) > 0 else 0.0
    for i in range(len(diffs) - 1):
        ema_diff = 0.7 * ema_diff + 0.3 * diffs[i]  # Làm mượt EMA xu hướng ngắn hạn
        
    # Mô phỏng tính chất tuần hoàn (Sine wave theo giờ thực tế để giả lập cao điểm sáng/chiều)
    current_hour = datetime.now().hour
    # Giờ cao điểm (7-9h sáng, 17-19h chiều) -> sin wave tạo đỉnh
    time_factor = np.sin((current_hour - 6) * np.pi / 6) * 4.0
    
    # Ước lượng mật độ tương lai
    pred_pcu = latest_pcu + (ema_diff * 1.5) + time_factor
    # Khống chế giới hạn dưới 0 và trên 100 PCU
    pred_pcu = max(0.0, min(100.0, round(pred_pcu, 2)))
    
    return latest_pcu, pred_pcu, "Dự báo bằng Adaptive Trend (Thuật toán thích ứng)"
