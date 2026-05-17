import json
import os
import sys

# Set output encoding to UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = r'd:\4_MasterBachKhoa\HK252\Thực tập 2\hcm_cameras_v2.json'
OUTPUT_FILE = r'd:\4_MasterBachKhoa\HK252\Thực tập 2\hcm_cameras_v3.json'

def filter_cameras():
    if not os.path.exists(INPUT_FILE):
        print(f"LỖI: Không tìm thấy file {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        cameras = json.load(f)
    
    initial_count = len(cameras)
    # Lọc bỏ những camera có status là NOT_IMAGE
    filtered_cameras = [c for c in cameras if c.get('status') != 'NOT_IMAGE']
    final_count = len(filtered_cameras)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_cameras, f, ensure_ascii=False, indent=4)
    
    print(f"Đã lọc xong!")
    print(f"- Tổng số ban đầu: {initial_count}")
    print(f"- Đã loại bỏ: {initial_count - final_count} camera (NOT_IMAGE)")
    print(f"- Tổng số còn lại (v3): {final_count}")
    print(f"- Lưu tại: {OUTPUT_FILE}")

if __name__ == "__main__":
    filter_cameras()
