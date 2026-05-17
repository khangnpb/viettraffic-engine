import os
import json
import time
import math
import requests
from datetime import datetime
import re
import urllib3
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Ensure UTF-8 output encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH PACED MULTI-THREADING (30 GIÂY) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v3.json"))

BASE_CCTV_DIR = r"A:\TrafficData\snapshots"
BASE_GMAP_DIR = r"A:\TrafficData\TrafficAssessmentbyGoogle Maps"

INTERVAL = 30      # Chu kỳ quét: 30 giây
MAX_WORKERS = 6    # Tăng nhẹ số luồng lên 6 để gộp 2 tác vụ mượt mà
ZOOM_LEVEL = 17    # Mức zoom chi tiết nút giao trên Google Maps

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def clean_filename(filename):
    if not filename: return "unknown"
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def latlng_to_tile(lat, lng, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lng + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def download_cctv(session, camera, folder_name, timestamp):
    url = camera['url']
    output_dir = os.path.join(BASE_CCTV_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{timestamp}.jpg")
    
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://giaothong.hochiminhcity.gov.vn/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        final_url = f"{url}&t={int(time.time() * 1000)}"
        response = session.get(final_url, headers=headers, timeout=8, verify=False)
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False

def download_gmaps(lat, lng, zoom, folder_name, timestamp):
    output_dir = os.path.join(BASE_GMAP_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{timestamp}_google_traffic.png")
    
    x, y = latlng_to_tile(lat, lng, zoom)
    url = f"https://mt1.google.com/vt?lyrs=m,traffic&x={x}&y={y}&z={zoom}"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.google.com/maps"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=8, verify=False)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False

def download_unified(session, camera, timestamp):
    cam_id = camera['id']
    cam_name = clean_filename(camera['name'])
    folder_name = f"{cam_name}___{cam_id}"
    
    lat = camera.get('lat')
    lng = camera.get('lng')
    
    # 1. Tải ảnh CCTV GTVT
    cctv_ok = download_cctv(session, camera, folder_name, timestamp)
    
    # 2. Tải ảnh kẹt xe Google Maps (nếu có tọa độ hợp lệ)
    gmaps_ok = False
    if lat is not None and lng is not None:
        gmaps_ok = download_gmaps(lat, lng, ZOOM_LEVEL, folder_name, timestamp)
        
    return cctv_ok, gmaps_ok

def main():
    if not os.path.exists(r"A:"):
        print("[!] LỖI: Không tìm thấy ổ đĩa A:. Vui lòng kết nối ổ đĩa để lưu trữ.")
        return

    print(f"[*] Đang tải danh sách camera từ {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"[!] LỖI: Không tìm thấy file danh sách camera tại {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        cameras = json.load(f)

    total_cams = len(cameras)
    gmap_cams = len([c for c in cameras if c.get("lat") is not None])
    
    print(f"[*] Chế độ: ĐỘNG CƠ CÀO HỢP NHẤT (Unified Traffic & Google Maps Crawler).")
    print(f"[*] Chu kỳ: {INTERVAL} giây | Số luồng tối đa: {MAX_WORKERS}")
    print(f"[*] Số camera CCTV: {total_cams} | Số camera có tọa độ Google Maps: {gmap_cams}")

    session = requests.Session()
    cycle_count = 0

    while True:
        cycle_start = time.time()
        now = datetime.now().strftime("%H:%M:%S")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cycle_count += 1
        
        print(f"\n[{now}] --- Bắt đầu chu kỳ quét Hợp nhất #{cycle_count} ---")
        
        # BƯỚC KHỞI TẠO COOKIES SỞ GTVT
        print("[*] Đang khởi tạo session và lấy cookies từ trang chủ Sở GTVT...")
        try:
            homepage_headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://giaothong.hochiminhcity.gov.vn/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive"
            }
            r_home = session.get("https://giaothong.hochiminhcity.gov.vn/", headers=homepage_headers, timeout=12, verify=False)
            if r_home.status_code == 200:
                print(f"[+] Lấy cookies thành công: {list(session.cookies.keys())}")
            else:
                print(f"[!] Cảnh báo: Lấy cookies trang chủ thất bại (Status: {r_home.status_code})")
        except Exception as e:
            print(f"[!] Lỗi kết nối trang chủ để lấy cookies: {e}")

        # Xáo trộn camera để rải đều băng thông
        random.shuffle(cameras)
        
        stagger_delay = INTERVAL / total_cams
        futures = []
        cctv_success = 0
        gmaps_success = 0
        
        # ThreadPoolExecutor quản lý chung
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for idx, camera in enumerate(cameras):
                t_start = time.time()
                
                # Submit tác vụ tải hợp nhất
                future = executor.submit(download_unified, session, camera, timestamp)
                futures.append(future)
                
                # Giãn cách staggered bắt đầu giữa các camera
                jitter = random.uniform(-0.005, 0.005)
                sleep_time = max(0.005, stagger_delay - (time.time() - t_start) + jitter)
                time.sleep(sleep_time)
                
                if (idx + 1) % 100 == 0:
                    print(f" -> Đã xếp lịch cào {idx + 1}/{total_cams} nút giao...")
            
            # Đếm kết quả thành công từ các luồng
            for future in as_completed(futures):
                cctv_ok, gmaps_ok = future.result()
                if cctv_ok:
                    cctv_success += 1
                if gmaps_ok:
                    gmaps_success += 1
                    
        duration = time.time() - cycle_start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Hoàn tất chu kỳ Hợp nhất.")
        print(f" [+] CCTV thành công: {cctv_success}/{total_cams} ảnh.")
        print(f" [+] Google Maps thành công: {gmaps_success}/{gmap_cams} ảnh tile.")
        print(f" [+] Tổng thời gian thực hiện: {duration:.2f}s")
        
        wait_time = max(1, INTERVAL - duration)
        if wait_time > 1:
            print(f"[*] Chờ {wait_time:.1f} giây trước chu kỳ tiếp theo...\n")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
