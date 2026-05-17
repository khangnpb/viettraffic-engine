import torch
import torch.nn as nn

class TrafficLSTM(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=64, num_layers=2, output_dim=1):
        super(TrafficLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Lớp LSTM mạng hồi quy chuỗi thời gian
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        
        # Lớp tuyến tính ánh xạ đầu ra về giá trị PCU đơn lẻ dự đoán
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        # Thiết lập trạng thái ẩn ban đầu
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # Truyền qua mạng LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Chỉ lấy trạng thái ẩn ở bước thời gian cuối cùng (Last Time Step)
        out = self.fc(out[:, -1, :])
        return out
