# 🚦 VietTraffic Engine - Hệ thống giám sát giao thông thông minh

Chào mừng bạn đến với **VietTraffic Engine** – hệ thống giám sát và chuyển đổi số giao thông số hóa thời gian thực (Digital Twin) dành cho TP. Hồ Chí Minh. Hệ thống này bao gồm các tiến trình thu thập hình ảnh camera GTVT tự động, tích hợp tình trạng kẹt xe thời gian thực từ bản đồ vệ tinh Google Maps không cần API key, và cung cấp một Dashboard phân tích trực quan nâng cao.

---

## 📂 Kiến trúc thư mục dự án (Project Architecture)

Thư mục dự án đã được tối ưu hóa cấu trúc theo các tiêu chuẩn quốc tế (**PEP 8 & Clean Architecture**):

```text
Thực tập 2/
├── data/                          # Dữ liệu cấu hình camera và tọa độ địa lý
│   ├── hcm_cameras_v3.json        # Danh sách 709 camera đã sửa lỗi tọa độ chuẩn 100%
│   ├── hcm_cameras_v4_clean.json  # Dữ liệu trích xuất sạch từ API Sở GTVT
│   ├── hcm_cameras_v3_backup.json # Bản sao lưu tọa độ gốc để đối chứng
│   └── debug_api/                 # File log API thô từ hệ thống
│
├── docs/                          # Tài liệu nghiên cứu và kế hoạch phát triển AI
│   ├── dataset_sources_research.md# Nghiên cứu nguồn dữ liệu video giao thông
│   └── yolo_detection_plan.md     # Kế hoạch fine-tune model YOLOv8n nhận diện phương tiện
│
├── crawlers/                      # Các động cơ cào dữ liệu tự động (Background Engine)
│   ├── __init__.py
│   ├── cctv_crawler.py            # Cào ảnh camera trực tiếp từ cổng Sở GTVT (Paced Staggered)
│   ├── gmaps_crawler.py           # Cào ảnh kẹt xe Google Maps Live Traffic (Free & Keyless)
│   └── unified_crawler.py         # ĐỘNG CƠ HỢP NHẤT: Cào cả CCTV và Google Maps song song cực nhanh
│
├── scrapers/                      # Các công cụ trích xuất, phân tích log API thô một lần
│   ├── __init__.py
│   ├── hcm_api_scraper.py         # Capture gói tin mạng từ cổng giao thông
│   ├── extract_camera_ids.py      # Bóc tách ID camera
│   ├── parse_ashx_log.py          # Bộ parser đệ quy ngoặc (Bracket) bóc tách dữ liệu Sở GTVT
│   ├── merge_camera_list.py       # Hợp nhất và ánh xạ lại tọa độ chính xác vào file v3.json
│   └── old/                       # Kho lưu trữ các mã nguồn lịch sử
│
├── utils/                         # Các công cụ kiểm tra chẩn đoán hệ thống
│   ├── __init__.py
│   ├── check_connection.py        # Kiểm tra ping/kết nối mạng đến máy chủ GTVT
│   └── benchmark_disks.py         # Kiểm tra tốc độ đọc/ghi IOPS của ổ cứng lưu trữ
│
├── logs/                          # Thư mục lưu nhật ký hoạt động của hệ thống
│   └── operational_log_backup.log # Nhật ký hoạt động cũ của hệ thống
│
├── VietTraffic_Engine/            # Bộ não hiển thị Dashboard và Mô hình AI
│   ├── __init__.py
│   ├── analytics/                 # Tính toán mật độ giao thông và mức độ phục vụ (LOS)
│   ├── processor/                 # Nhận diện phương tiện giao thông (YOLOv8)
│   ├── predictor/                 # Dự đoán lưu lượng kẹt xe tương lai (LSTM model)
│   └── ui/                        # Giao diện Streamlit & Bản đồ tương tác Folium
│
├── run_dashboard.py               # ROOT LAUNCHER: Khởi động giao diện chính Streamlit
├── run_crawlers.py                # ROOT LAUNCHER: Khởi động ĐỘNG CƠ HỢP NHẤT (Tải CCTV & Google Maps)
├── run_processor.py               # ROOT LAUNCHER: Khởi động ĐỘNG CƠ XỬ LÝ ẢNH AI (YOLOv8 & DB Sync)
└── requirements.txt               # Danh sách các thư viện Python phụ thuộc
```

---

## ⚡ Hướng dẫn Khởi chạy (How to Run)

Dự án được trang bị sẵn các Launcher tối giản, cực kỳ tiện lợi ngay tại thư mục gốc:

### 1. Khởi động Giao diện chính (Streamlit Dashboard)
```bash
python run_dashboard.py
```
*Lệnh này sẽ tự động khởi chạy môi trường Streamlit trực quan trên trình duyệt của bạn.*

### 2. Khởi chạy Động cơ Cào Hợp nhất (Unified Traffic & Google Maps Crawler)
```bash
python run_crawlers.py
```
*Tiến trình sẽ chạy tuần hoàn song song, tự động giãn cách nhịp độ cứ mỗi 30 giây để chụp snapshot từ 709 camera và tải ảnh Live Traffic kẹt xe tương ứng từ Google Maps vệ tinh.*

### 3. Khởi chạy Động cơ Xử lý Ảnh AI (YOLOv8 & DB Sync)
```bash
python run_processor.py
```
*Tiến trình sẽ tự động quét các ảnh thô cào về ở đĩa `A:`, chạy nhận diện phương tiện giao thông bằng YOLOv8, tính PCU và ghi nhận vào cơ sở dữ liệu SQLite.*

---

## ⚙️ Thiết lập Môi trường (Setup Environment)

Trước khi khởi chạy lần đầu tiên, hãy cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

---

## 🛠️ Diagnostics & Công cụ phát triển

Nếu gặp sự cố về đường truyền hoặc ổ cứng lưu trữ (ví dụ ổ `A:` bị ngắt kết nối):
* Kiểm tra băng thông và mạng: `python utils/check_connection.py`
* Đo hiệu suất đĩa ghi dữ liệu: `python utils/benchmark_disks.py`
