import os
import json
import time
import requests
from datetime import datetime
import re
import urllib3
import random
import sys

# Set output encoding to UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH STEALTH MODE (3 PHÚT) ---
INPUT_FILE = "hcm_cameras_v3.json"
BASE_OUTPUT_DIR = r"A:\TrafficData\snapshots"
INTERVAL = 60  # Chu kỳ quét: 180 giây (3 phút)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def clean_filename(filename):
    if not filename: return "unknown"
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def download_camera(session, camera):
    cam_id = camera['id']
    cam_name = clean_filename(camera['name'])
    url = camera['url']
    
    # Cấu trúc thư mục: Tên___ID
    folder_name = f"{cam_name}___{cam_id}"
    output_dir = os.path.join(BASE_OUTPUT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{timestamp}.jpg")
    
    try:
        # Giả lập hoàn hảo header trình duyệt
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://giaothong.hochiminhcity.gov.vn/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        # Thêm timestamp tránh cache
        final_url = f"{url}&t={int(time.time() * 1000)}"
        
        response = session.get(final_url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
        return False
    except Exception:
        return False

def main():
    if not os.path.exists(r"A:"):
        print("[!] LỖI: Không tìm thấy ổ đĩa A:. Vui lòng kiểm tra kết nối.")
        return

    print(f"[*] Đang tải danh sách camera từ {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        cameras = json.load(f)

    total_cams = len(cameras)
    print(f"[*] Đang chạy ở chế độ TÀNG HÌNH (Quét tuần tự rải đều trong {INTERVAL/60} phút).")
    print(f"[*] Tổng số camera cần cào: {total_cams}")

    session = requests.Session()

    while True:
        cycle_start = time.time()
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] --- Bắt đầu chu kỳ quét mới ---")
        
        # BƯỚC QUAN TRỌNG: Truy cập trang chủ trước để lấy Session Cookies (.VDMS, ASP.NET_SessionId)
        # Server cổng 8007 bắt buộc phải có các cookie này nếu không sẽ trả về 403 Forbidden.
        print("[*] Đang khởi tạo session và lấy cookies từ trang chủ...")
        try:
            homepage_headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://giaothong.hochiminhcity.gov.vn/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive"
            }
            r_home = session.get("https://giaothong.hochiminhcity.gov.vn/", headers=homepage_headers, timeout=15, verify=False)
            if r_home.status_code == 200:
                print(f"[+] Lấy cookies thành công: {list(session.cookies.keys())}")
            else:
                print(f"[!] Cảnh báo: Lấy cookies trang chủ thất bại (Status: {r_home.status_code})")
        except Exception as e:
            print(f"[!] Lỗi kết nối trang chủ để lấy cookies: {e}")

        # Xáo trộn danh sách mỗi chu kỳ để tránh gửi request theo thứ tự cố định
        random.shuffle(cameras)
        
        # 180s / 709 cam = ~0.25s giãn cách mục tiêu
        target_delay = INTERVAL / total_cams
        
        success_count = 0
        
        for idx, camera in enumerate(cameras):
            req_start = time.time()
            
            success = download_camera(session, camera)
            if success:
                success_count += 1
            
            # Tính thời gian thực tế đã tốn để gửi request
            elapsed = time.time() - req_start
            
            # Tính toán delay động để giữ nhịp độ ổn định suốt 3 phút
            # Thêm jitter nhỏ ngẫu nhiên (-0.05s đến +0.05s) để chống pattern-matching của WAF
            jitter = random.uniform(-0.05, 0.05)
            delay = max(0.05, target_delay - elapsed + jitter)
            
            time.sleep(delay)
            
            # Hiển thị tiến độ mỗi 50 camera
            if (idx + 1) % 50 == 0:
                print(f" -> Đã quét {idx + 1}/{total_cams} camera. Thành công: {success_count}")

        duration = time.time() - cycle_start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Hoàn tất chu kỳ. Thành công: {success_count}/{total_cams}. Tổng thời gian quét: {duration:.2f}s")
        
        # Nếu chu kỳ quét kết thúc sớm, chờ nốt thời gian còn lại
        wait_time = max(1, INTERVAL - duration)
        if wait_time > 1:
            print(f"[*] Chờ {wait_time:.1f} giây trước chu kỳ tiếp theo...\n")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
