import os
import json
import time
import requests
from datetime import datetime
import re
import urllib3
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Set output encoding to UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH PACED MULTI-THREADING (30 GIÂY) ---
# Resolve input file relative to this script's directory (standard Python best practice)
script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v3.json"))
BASE_OUTPUT_DIR = r"A:\TrafficData\snapshots"
INTERVAL = 30  # Chu kỳ quét: 30 giây
MAX_WORKERS = 5  # Tăng lên 5 luồng để đạt được mốc 30s

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
    if not os.path.exists(INPUT_FILE):
        print(f"[!] LỖI: Không tìm thấy file danh sách camera tại {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        cameras = json.load(f)

    total_cams = len(cameras)
    print(f"[*] Chế độ: PHÂN PHỐI NHỊP ĐỘ SONG SONG (Staggered Concurrent Crawling).")
    print(f"[*] Chu kỳ: {INTERVAL} giây | Số luồng tối đa: {MAX_WORKERS}")
    print(f"[*] Tổng số camera cần cào: {total_cams}")

    session = requests.Session()

    while True:
        cycle_start = time.time()
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] --- Bắt đầu chu kỳ quét mới ---")
        
        # BƯỚC QUAN TRỌNG: Truy cập trang chủ trước để lấy Session Cookies (.VDMS, ASP.NET_SessionId)
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

        # Xáo trộn danh sách mỗi chu kỳ
        random.shuffle(cameras)
        
        # Tính toán giãn cách staggered bắt đầu giữa các task
        # 60s / 709 cam = ~0.084s (84 ms) giãn cách giữa các lượt khởi chạy
        stagger_delay = INTERVAL / total_cams
        
        futures = []
        success_count = 0
        
        # Sử dụng ThreadPoolExecutor để chạy song song
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for idx, camera in enumerate(cameras):
                t_start = time.time()
                
                # Submit task vào ThreadPool
                future = executor.submit(download_camera, session, camera)
                futures.append(future)
                
                # Giãn cách thời gian submit để rải đều request trên đường truyền WAN
                # Jitter ngẫu nhiên nhỏ để tăng tính tự nhiên
                jitter = random.uniform(-0.01, 0.01)
                sleep_time = max(0.01, stagger_delay - (time.time() - t_start) + jitter)
                time.sleep(sleep_time)
                
                # Hiển thị tiến độ submit mỗi 100 camera
                if (idx + 1) % 100 == 0:
                    print(f" -> Đã xếp lịch quét {idx + 1}/{total_cams} camera...")
            
            # Chờ các luồng hoàn tất và đếm kết quả thành công
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                    
        duration = time.time() - cycle_start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Hoàn tất chu kỳ. Thành công: {success_count}/{total_cams}. Tổng thời gian quét: {duration:.2f}s")
        
        wait_time = max(1, INTERVAL - duration)
        if wait_time > 1:
            print(f"[*] Chờ {wait_time:.1f} giây trước chu kỳ tiếp theo...\n")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
