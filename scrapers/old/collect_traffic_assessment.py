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

# Đảm bảo xuất ra encoding UTF-8 để chạy trên Windows CMD không bị lỗi font
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH ĐƯỜNG DẪN & THAM SỐ ---
INPUT_FILE = "hcm_cameras_v3.json"
BASE_OUTPUT_DIR = r"A:\TrafficData\TrafficAssessmentbyGoogle Maps"
ZOOM_LEVEL = 17  # Mức thu phóng phố phường (Zoom 17 là tối ưu cho nút giao)

# Nếu bạn có API Key của TomTom, hãy điền vào đây để lấy thêm số liệu tốc độ (km/h) và thời gian trễ.
# Đăng ký miễn phí tại: https://developer.tomtom.com/ (Không cần thẻ tín dụng, 2,500 req/ngày)
TOMTOM_API_KEY = "Zuvrvk6H4sz77PvisuErQxR3rT3jLyer" 

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def clean_filename(filename):
    if not filename: return "unknown"
    import re
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def latlng_to_tile(lat, lng, zoom):
    """Quy đổi tọa độ Lat/Lng sang chỉ số Tile (X, Y) của Google/Slippy Map."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lng + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def download_google_traffic_tile(lat, lng, zoom, filepath):
    """
    Tải ảnh bản đồ kẹt xe trực tiếp từ Tile Server của Google Maps.
    Không cần API Key, hoàn toàn miễn phí.
    """
    x, y = latlng_to_tile(lat, lng, zoom)
    # Tile URL chứa lớp phủ traffic giao thông
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
        print(f"[!] Loi tai tile Google Maps tai ({lat}, {lng}): {e}")
    return False

def query_tomtom_traffic_flow(lat, lng, api_key):
    """
    Truy vấn số liệu tốc độ xe chạy thực tế và thời gian trễ từ TomTom Traffic Flow API.
    """
    if not api_key:
        return None
        
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative/10/json?key={api_key}&point={lat},{lng}&unit=KMPH"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            flow = data.get("flowSegmentData", {})
            
            current_speed = flow.get("currentSpeed", 0)
            free_flow_speed = flow.get("freeFlowSpeed", 0)
            
            # Tính chỉ số kẹt xe
            speed_ratio = round(current_speed / free_flow_speed, 2) if free_flow_speed > 0 else 1.0
            delay = flow.get("currentTravelTime", 0) - flow.get("freeFlowTravelTime", 0)
            delay = max(0, delay)
            
            # Đánh giá mức độ
            if speed_ratio >= 0.85:
                status = "Green (Thong thoang)"
            elif speed_ratio >= 0.55:
                status = "Yellow (Dong duc)"
            elif speed_ratio >= 0.35:
                status = "Orange (Un u nhe)"
            else:
                status = "Red (Ket xe)"
                
            return {
                "current_speed": current_speed,
                "free_flow_speed": free_flow_speed,
                "speed_ratio": speed_ratio,
                "delay_seconds": delay,
                "congestion_level": status
            }
        else:
            print(f"[!] TomTom API loi cho toa do ({lat}, {lng}): Status {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"[!] Loi ket noi TomTom: {e}")
    return None

def process_single_camera(session, camera, timestamp):
    cam_id = camera["id"]
    cam_name = clean_filename(camera["name"])
    lat = camera["lat"]
    lng = camera["lng"]
    
    # Tạo thư mục riêng cho từng camera trong thư mục yêu cầu
    folder_name = f"{cam_name}___{cam_id}"
    output_dir = os.path.join(BASE_OUTPUT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Đường dẫn file lưu ảnh tile Google Maps
    tile_filepath = os.path.join(output_dir, f"{timestamp}_google_traffic.png")
    # Đường dẫn file lưu log đánh giá dạng JSON
    log_filepath = os.path.join(output_dir, f"{timestamp}_assessment.json")
    
    # 1. Tải ảnh tile Google Maps kẹt xe
    tile_success = download_google_traffic_tile(lat, lng, ZOOM_LEVEL, tile_filepath)
    
    # 2. Truy vấn số liệu TomTom (nếu có API Key)
    tomtom_data = query_tomtom_traffic_flow(lat, lng, TOMTOM_API_KEY)
    
    # 3. Tổng hợp kết quả đánh giá giao thông
    assessment = {
        "camera_id": cam_id,
        "camera_name": camera["name"],
        "lat": lat,
        "lng": lng,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tile_downloaded": tile_success,
        "quantitative_data": tomtom_data if tomtom_data else ("Query TomTom That bai (vui long kiem tra key)" if TOMTOM_API_KEY else "Chua cau (Dien TOMTOM_API_KEY de kich hoat)")
    }
    
    # Lưu file JSON assessment
    with open(log_filepath, "w", encoding="utf-8") as f:
        json.dump(assessment, f, indent=4, ensure_ascii=False)
        
    return cam_name, tile_success, tomtom_data is not None

def main():
    print("==================================================")
    print("🚦 GOOGLE MAPS & TOMTOM TRAFFIC ASSESSMENT CRAWLER 🚦")
    print("==================================================")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[!] File camera nguồn '{INPUT_FILE}' khong ton tai!")
        sys.exit(1)
        
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        cameras = json.load(f)
        
    # Lọc các camera có tọa độ Lat/Lng hợp lệ
    valid_cameras = [c for c in cameras if c.get("lat") is not None and c.get("lng") is not None]
    total_cams = len(valid_cameras)
    
    print(f"[*] Tim thay {total_cams}/{len(cameras)} camera co tọa do hop le de danh gia.")
    print(f"[*] Thu muc luu tru: '{BASE_OUTPUT_DIR}'")
    
    if not TOMTOM_API_KEY:
        print("[*] Luu y: TOMTOM_API_KEY trong. Tool se chi tai anh ve tinh Google Traffic Tile (Mien phi, khong can key).")
    else:
        print("[+] Kich hoat dong thoi TomTom Traffic Flow API cho so lieu toc do!")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Chạy đa luồng cào song song có pacing để tránh quá tải server Google
    MAX_WORKERS = 5
    print(f"[*] Khoi dong ThreadPoolExecutor voi {MAX_WORKERS} luong...")
    
    success_count = 0
    start_time = time.time()
    
    session = requests.Session()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, cam in enumerate(valid_cameras):
            # Tạo độ trễ nhỏ (pacing) ~50ms giữa các luồng
            time.sleep(0.05)
            futures.append(executor.submit(process_single_camera, session, cam, timestamp))
            
        for future in as_completed(futures):
            try:
                cam_name, tile_ok, tomtom_ok = future.result()
                if tile_ok:
                    success_count += 1
                
                # In tiến độ định kỳ
                if success_count % 50 == 0 and success_count > 0:
                    print(f" -> Da danh gia {success_count}/{total_cams} nut giao...")
            except Exception as e:
                pass
                
    elapsed_time = time.time() - start_time
    print(f"\n[✓] Hoan thanh chu ky danh gia Google Maps!")
    print(f" -> Tong so camera co anh tile: {success_count}/{total_cams}")
    print(f" -> Thoi gian thuc hien: {elapsed_time:.2f} giay.")

if __name__ == "__main__":
    main()
