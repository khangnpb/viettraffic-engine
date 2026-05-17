import os
import json
import time
import math
import requests
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import sys

# Ensure UTF-8 output encoding for Windows CMD
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH PACED MULTI-THREADING (30 GIÂY) ---
# Resolve input file relative to this script's directory (standard Python best practice)
script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v3.json"))
BASE_OUTPUT_DIR = r"A:\TrafficData\TrafficAssessmentbyGoogle Maps"
INTERVAL = 30  # Chu kỳ cào ảnh Google Maps Tile: 30 giây
MAX_WORKERS = 5  # Số luồng chạy song song
ZOOM_LEVEL = 17  # Mức thu phóng nút giao chi tiết

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def clean_filename(filename):
    if not filename: return "unknown"
    import re
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def latlng_to_tile(lat, lng, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lng + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def download_google_traffic_tile(lat, lng, zoom, filepath):
    x, y = latlng_to_tile(lat, lng, zoom)
    url = f"https://mt1.google.com/vt?lyrs=m,traffic&x={x}&y={y}&z={zoom}"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.google.com/maps"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        pass
    return False

def process_single_camera(camera, timestamp):
    cam_id = camera["id"]
    cam_name = clean_filename(camera["name"])
    lat = camera["lat"]
    lng = camera["lng"]
    
    folder_name = f"{cam_name}___{cam_id}"
    output_dir = os.path.join(BASE_OUTPUT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    tile_filepath = os.path.join(output_dir, f"{timestamp}_google_traffic.png")
    
    # Cào ảnh kẹt xe Google Maps (mỗi 30s)
    tile_success = download_google_traffic_tile(lat, lng, ZOOM_LEVEL, tile_filepath)
    return tile_success

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
        
    valid_cameras = [c for c in cameras if c.get("lat") is not None and c.get("lng") is not None]
    total_cams = len(valid_cameras)
    
    print(f"[*] Chế độ: QUÉT NHỊP ĐỘ SONG SONG (Staggered Google Traffic Tile Crawling).")
    print(f"[*] Chu kỳ cào ảnh Google Tile: {INTERVAL} giây | Số luồng song song: {MAX_WORKERS}")
    print(f"[*] Số lượng nút giao có tọa độ hợp lệ: {total_cams}")

    cycle_count = 0

    while True:
        cycle_start = time.time()
        now = datetime.now().strftime("%H:%M:%S")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        cycle_count += 1
        print(f"\n[{now}] --- Bắt đầu chu kỳ quét Google Maps #{cycle_count} ---")
        print("[*] Thu thập ảnh Google Maps Live Traffic (Free & Keyless)...")
            
        # Xáo trộn thứ tự để rải đều băng thông
        random.shuffle(valid_cameras)
        
        stagger_delay = INTERVAL / total_cams
        futures = []
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for idx, camera in enumerate(valid_cameras):
                t_start = time.time()
                
                # Submit task tải ảnh tile
                future = executor.submit(process_single_camera, camera, timestamp)
                futures.append(future)
                
                # Jitter rải nhịp độ request
                jitter = random.uniform(-0.01, 0.01)
                sleep_time = max(0.01, stagger_delay - (time.time() - t_start) + jitter)
                time.sleep(sleep_time)
                
                if (idx + 1) % 100 == 0:
                    print(f" -> Đã xếp lịch cào {idx + 1}/{total_cams} nút giao...")
            
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                    
        duration = time.time() - cycle_start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Hoàn tất chu kỳ. Thành công: {success_count}/{total_cams} ảnh tile. Tổng thời gian: {duration:.2f}s")
        
        wait_time = max(1, INTERVAL - duration)
        if wait_time > 1:
            print(f"[*] Chờ {wait_time:.1f} giây trước chu kỳ tiếp theo...\n")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
