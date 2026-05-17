import json
import os
import requests
from urllib.parse import quote

# Đường dẫn tới file hcm_cameras_v3.json nằm ở thư mục cha của dự án (trong data/)
CAMERAS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "hcm_cameras_v3.json")

def geocode_intersection(name):
    """
    Sử dụng Nominatim OpenStreetMap API để lấy tọa độ từ tên nút giao/tên đường.
    Độ trễ tối thiểu 1s theo chính sách OSM.
    """
    try:
        # Làm sạch tên nút giao (ví dụ: Thay thế "–" hoặc "-" thành "," để tìm kiếm tốt hơn)
        search_query = name.replace("–", ",").replace("-", ",") + ", Ho Chi Minh City, Vietnam"
        url = f"https://nominatim.openstreetmap.org/search?q={quote(search_query)}&format=json&limit=1"
        
        headers = {
            "User-Agent": "VietTraffic_Engine_DigitalTwin_v1.0 (academic_contact@hcmut.edu.vn)"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                print(f"[+] Geocoded thanh cong '{name}': ({lat}, {lng})")
                return lat, lng
    except Exception as e:
        print(f"[!] Loi geocode '{name}': {e}")
    return None, None

def load_clean_cameras(auto_geocode=False):
    """
    Đọc hcm_cameras_v3.json, lọc các camera có tọa độ hợp lệ.
    Nếu auto_geocode=True, sẽ thử điền tọa độ cho các nút giao có tên rõ ràng.
    """
    if not os.path.exists(CAMERAS_JSON_PATH):
        print(f"[!] Khong tim thay file cau hinh camera tai: {CAMERAS_JSON_PATH}")
        return {}

    with open(CAMERAS_JSON_PATH, "r", encoding="utf-8") as f:
        cameras = json.load(f)

    clean_cameras = {}
    null_count = 0
    geocoded_count = 0
    
    for cam in cameras:
        cam_id = cam.get("id")
        name = cam.get("name")
        lat = cam.get("lat")
        lng = cam.get("lng")
        
        # Nếu tọa độ bị null và có cờ tự động geocode
        if (lat is None or lng is None) and auto_geocode:
            # Chỉ geocode nếu tên không phải dạng mã hiệu TTH/ITS
            if not any(code in name.upper() for code in ["TTH", "ITS", "BR", "IDICO"]):
                lat_geo, lng_geo = geocode_intersection(name)
                if lat_geo and lng_geo:
                    lat = lat_geo
                    lng = lng_geo
                    geocoded_count += 1
        
        # Chỉ nhận các camera có tọa độ hợp lệ để vẽ lên bản đồ local
        if lat is not None and lng is not None:
            clean_cameras[cam_id] = {
                "id": cam_id,
                "name": name,
                "lat": float(lat),
                "lng": float(lng),
                "url": cam.get("url"),
                "status": cam.get("status", "UP")
            }
        else:
            null_count += 1

    print(f"[*] Da tai {len(clean_cameras)} camera hop le. (Bo qua/Null: {null_count}, Tu dong Geocode: {geocoded_count})")
    return clean_cameras

if __name__ == "__main__":
    # Test thử hàm load
    cams = load_clean_cameras(auto_geocode=False)
    print(f"Vi du 1 camera: {list(cams.values())[0] if cams else 'Khong co'}")
