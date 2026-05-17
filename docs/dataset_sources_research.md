# Kế hoạch thu thập dữ liệu Video Giao thông Việt Nam

## 1. Danh sách nguồn THỦ CÔNG (Cần sức người)
- **App iHanoi (Hà Nội):** Tải app trên điện thoại, vào mục Camera giao thông. Cách lấy: Dùng tính năng quay màn hình hoặc chụp ảnh thủ công.
- **App TTGT TP.HCM (Sài Gòn):** Tương tự iHanoi, cung cấp ảnh snapshot từ hơn 800 camera.
- **Zalo OA:** Tìm "Thông tin giao thông TP.HCM" -> Menu "Camera" -> Chọn khu vực.
- **Group Facebook:** 
    - *OtoFun*: Nhiều clip camera hành trình chất lượng cao.
    - *Bạn hữu đường xa*: Clip thực tế từ tài xế.
- **Yêu cầu Dataset học thuật:**
    - *UIT-VinaDeveS22*: Cần gửi mail đăng ký với nhóm nghiên cứu UIT để lấy link full.

## 2. Danh sách nguồn TỰ ĐỘNG (Dùng Tool)
- **YouTube Livestreams:** 
    - Search: `Vietnam traffic livestream`, `Hanoi live cam`.
    - Tool: `yt-dlp` (Tự động tải luồng m3u8).
- **Roboflow Universe:**
    - Link: [Vietnam Vehicle Detection](https://universe.roboflow.com/search?q=vietnam%20traffic)
    - Tool: `roboflow` python library (Cần API Key).
- **Kaggle:**
    - Link: [Vietnamese Vehicles Dataset](https://www.kaggle.com/datasets)
    - Tool: `kaggle` CLI.
- **Websites Camera (Snapshot):** 
    - Một số tỉnh như Vũng Tàu, Đà Nẵng có trang web xem camera. Có thể dùng Python để crawl ảnh mỗi 10-30s.

## 3. Cấu trúc lưu trữ khuyến nghị
`A:/TrafficData/`
  ├── `raw_videos/` (Video gốc từ YouTube/App)
  ├── `processed_frames/` (Ảnh trích xuất từ video)
  └── `metadata.csv` (Lưu thông tin: ID, Vị trí, Thời gian, Nguồn)

---
*Ghi chú: Ưu tiên lấy data từ Roboflow trước vì đã có nhãn, sau đó mới tự crawl video từ YouTube.*
