import requests
import json

def get_full_camera_list():
    # Đây là API ẩn của Sở GTVT TP.HCM để lấy danh sách toàn bộ camera
    url = "https://giaothong.hochiminhcity.gov.vn/Services/Handler/CameraHandler.ashx?Method=GetCameras"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://giaothong.hochiminhcity.gov.vn/map.aspx",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    print("[*] Đang kết nối tới API để lấy danh sách Camera...")
    
    try:
        # Gửi request POST (thông thường API này nhận POST)
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Cấu trúc JSON thường là { "Data": [ { "CameraID": "...", "CameraName": "..." }, ... ] }
            cameras_raw = data.get("Data", [])
            
            print(f"[+] Tìm thấy tổng cộng {len(cameras_raw)} camera trên toàn thành phố!")
            
            final_list = []
            for cam in cameras_raw:
                final_list.append({
                    "name": cam.get("Description", cam.get("CameraName", "Unnamed")),
                    "id": cam.get("CameraID"),
                    "interval": 30
                })
            return final_list
        else:
            print(f"[!] Lỗi API: Status code {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[!] Lỗi khi gọi API: {e}")
        return []

if __name__ == "__main__":
    camera_list = get_full_camera_list()
    
    if camera_list:
        config_path = "VietTraffic_Engine/config/sources.json"
        
        # Đọc file config hiện tại
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # Cập nhật danh sách camera (Ví dụ lấy 100 cái để test hiệu năng)
        config["hcm_cameras"] = camera_list[:100] 
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        print(f"\n[SUCCESS] Đã cập nhật {len(config['hcm_cameras'])} camera vào sources.json!")
        print("[TIP] Bạn có thể sửa code để lấy toàn bộ (bỏ [:100]) nếu ổ cứng A: của bạn đủ mạnh.")
