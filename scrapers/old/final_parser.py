import re
import json
import os

def parse_camera_data():
    input_file = r"d:\4_MasterBachKhoa\HK252\Thực tập 2\debug_api\158__Web_Library_AJAX_FolderAjax_VDMS_Web_Library_ashx.txt"
    output_file = "hcm_cameras_final.json"
    
    if not os.path.exists(input_file):
        print("File input không tồn tại!")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex mới để lấy cả tên đường/ngã tư:
    # 1. \"([0-9a-f]{24})\": ID camera
    # 2. \".*?\": Bỏ qua các trường trung gian
    # 3. \"(?:UP|DOWN|NOT_IMAGE)\": Trạng thái
    # 4. \".*?\": Bỏ qua tiếp
    # 5. ,(?:null|\d+),\"([^\"]+)\": Đây là tên đường/ngã tư
    # 6. .*?POINT\(([\d.]+) ([\d.]+)\): Tọa độ
    pattern = re.compile(r'\"([0-9a-f]{24})\",\".*?\",\".*?\",.*?,\"(?:UP|DOWN|NOT_IMAGE)\",.*?,(?:null|\d+),\"([^\"]+)\".*?POINT\(([\d.]+) ([\d.]+)\)')
    
    matches = pattern.findall(content)
    
    cameras = []
    seen_ids = set()
    
    for cam_id, street_name, lng, lat in matches:
        if cam_id not in seen_ids:
            # Làm sạch tên đường để dùng làm filename (bỏ dấu, đổi space thành _)
            clean_name = street_name.strip()
            
            cameras.append({
                "id": cam_id,
                "name": clean_name,
                "lat": float(lat),
                "lng": float(lng),
                "url": f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={cam_id}&bg=black&w=520&h=300"
            })
            seen_ids.add(cam_id)
            
    # Lưu kết quả
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cameras, f, ensure_ascii=False, indent=4)
        
    print(f" [+] Success! Extracted {len(cameras)} cameras with street names.")
    print(f" [+] Results saved to: {output_file}")

if __name__ == "__main__":
    parse_camera_data()
