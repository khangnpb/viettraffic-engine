import os
import re
import glob
from datetime import datetime
import sys

# Đảm bảo import được các module khác
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor.detector import VehicleDetector
from analytics.database import get_connection, insert_traffic_record
from analytics.density import calculate_los

SNAPSHOTS_DIR = r"A:\TrafficData\snapshots"
ANNOTATED_DIR = r"A:\TrafficData\annotated"

def parse_folder_name(folder_name):
    """Phân tách tên camera và ID từ tên thư mục dạng: CamName___ID"""
    parts = folder_name.split("___")
    if len(parts) == 2:
        return parts[0], parts[1]
    return folder_name, "unknown"

def parse_timestamp(filename):
    """
    Chuyển đổi tên file dạng 20260517_103000.jpg thành chuỗi thời gian 
    định dạng SQLite YYYY-MM-DD HH:MM:SS
    """
    name_without_ext = os.path.splitext(filename)[0]
    match = re.search(r'(\d{8})_(\d{6})', name_without_ext)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

class SyncEngine:
    def __init__(self):
        self.detector = VehicleDetector()
        
    def get_processed_files(self):
        """Lấy danh sách các cặp (camera_id, timestamp) đã xử lý trong DB."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT camera_id, timestamp FROM traffic_history")
        rows = cursor.fetchall()
        conn.close()
        # Trả về dạng set để tra cứu O(1)
        return {(row["camera_id"], row["timestamp"]) for row in rows}

    def sync_once(self):
        """Thực hiện quét thư mục và xử lý các ảnh mới chưa có trong DB."""
        if not os.path.exists(SNAPSHOTS_DIR):
            print(f"[!] Thu muc snapshots khong ton tai: {SNAPSHOTS_DIR}")
            return
            
        print("[*] Dang tai danh sach cac file da xu ly...")
        processed_set = self.get_processed_files()
        
        # Danh sách lưu các tác vụ cần xử lý
        pending_jobs = []
        
        # Quét tất cả các thư mục camera
        for folder_name in os.listdir(SNAPSHOTS_DIR):
            folder_path = os.path.join(SNAPSHOTS_DIR, folder_name)
            if not os.path.isdir(folder_path):
                continue
                
            cam_name, cam_id = parse_folder_name(folder_name)
            
            # Quét tất cả ảnh JPG trong thư mục camera
            image_files = glob.glob(os.path.join(folder_path, "*.jpg"))
            if not image_files:
                continue
                
            # Sắp xếp ảnh mới nhất lên đầu để ưu tiên xử lý trước!
            image_files.sort(key=os.path.getctime, reverse=True)
            
            for img_path in image_files:
                filename = os.path.basename(img_path)
                db_timestamp = parse_timestamp(filename)
                
                if not db_timestamp:
                    continue  # Bỏ qua nếu tên file không đúng định dạng
                    
                # Nếu chưa xử lý ảnh này
                if (cam_id, db_timestamp) not in processed_set:
                    pending_jobs.append({
                        "image_path": img_path,
                        "camera_id": cam_id,
                        "camera_name": cam_name,
                        "timestamp": db_timestamp,
                        "filename": filename,
                        "folder_name": folder_name
                    })
        
        total_pending = len(pending_jobs)
        if total_pending == 0:
            print("[*] Tat ca cac anh da duoc dong bo day du. Khong co anh moi.")
            return
            
        print(f"[+] Tim thay {total_pending} anh moi can xu ly.")
        
        # Ưu tiên xử lý ảnh mới nhất trước để hiển thị Live lên Bản đồ
        # Chúng ta chỉ xử lý tối đa 20 ảnh/mỗi chu kỳ quét (nếu dồn ứ nhiều ảnh cũ) để tránh treo hệ thống
        # và giữ luồng xử lý luôn trơn tru.
        pending_jobs.sort(key=lambda x: x["timestamp"], reverse=True)
        jobs_to_process = pending_jobs[:30]  # Giới hạn 30 ảnh một chu kỳ quét
        
        processed_count = 0
        for job in jobs_to_process:
            img_path = job["image_path"]
            cam_id = job["camera_id"]
            cam_name = job["camera_name"]
            timestamp = job["timestamp"]
            
            # Thư mục lưu ảnh có vẽ bounding box của YOLO
            save_annotated_dir = os.path.join(ANNOTATED_DIR, job["folder_name"])
            
            print(f"[*] Dang nhan dien [{cam_name}] ({timestamp})...")
            try:
                res = self.detector.detect_vehicles(img_path, save_annotated_dir=save_annotated_dir)
                if res:
                    counts = res["counts"]
                    pcu = res["total_pcu"]
                    annotated_path = res["annotated_path"]
                    
                    # Tính LOS
                    los_data = calculate_los(pcu)
                    los_level = los_data["level"]
                    
                    # Ghi vào SQLite
                    insert_traffic_record(
                        timestamp=timestamp,
                        camera_id=cam_id,
                        camera_name=cam_name,
                        motorcycles=counts["motorcycle"],
                        cars=counts["car"],
                        trucks=counts["truck"],
                        buses=counts["bus"],
                        total_pcu=pcu,
                        los_level=los_level,
                        image_path=annotated_path if annotated_path else img_path
                    )
                    processed_count += 1
            except Exception as e:
                print(f"[!] Loi khi xu ly anh {img_path}: {e}")
                
        print(f"[✓] Hoan thanh chu ky dong bo. Da xu ly thanh cong {processed_count}/{len(jobs_to_process)} anh.")

if __name__ == "__main__":
    engine = SyncEngine()
    engine.sync_once()
