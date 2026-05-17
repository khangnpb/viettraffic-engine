import os
import cv2
from ultralytics import YOLO

# Cấu hình đường dẫn model yolov8n.pt nằm trong config/
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
MODEL_PATH = os.path.join(CONFIG_DIR, "yolov8n.pt")

class VehicleDetector:
    def __init__(self):
        """Khởi tạo detector và tải mô hình YOLOv8n."""
        print(f"[*] Dang tai mo hinh YOLO tu: {MODEL_PATH}...")
        # Nếu chưa có model, YOLO sẽ tự động tải về MODEL_PATH
        self.model = YOLO(MODEL_PATH)
        
        # COCO class IDs cho các phương tiện giao thông thông dụng
        self.target_classes = {
            2: "car",          # Ô tô con
            3: "motorcycle",   # Xe máy
            5: "bus",          # Xe buýt / xe khách
            7: "truck"         # Xe tải
        }

    def detect_vehicles(self, image_path, save_annotated_dir=None):
        """
        Nhận diện phương tiện trong ảnh, tính PCU và vẽ bounding boxes nếu được yêu cầu.
        """
        if not os.path.exists(image_path):
            print(f"[!] File anh khong ton tai: {image_path}")
            return None

        # Chạy inference
        results = self.model(image_path, verbose=False)
        result = results[0]  # Lấy kết quả cho ảnh đầu tiên
        
        # Khởi tạo đếm
        counts = {"motorcycle": 0, "car": 0, "bus": 0, "truck": 0}
        
        # Duyệt qua các đối tượng nhận dạng được
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            if cls_id in self.target_classes:
                vehicle_type = self.target_classes[cls_id]
                counts[vehicle_type] += 1
                
        # Tính PCU quy đổi (Quy chuẩn giao thông Việt Nam)
        pcu = (
            counts["motorcycle"] * 0.3 +
            counts["car"] * 1.0 +
            counts["truck"] * 2.5 +
            counts["bus"] * 3.0
        )
        # Làm tròn PCU 2 chữ số thập phân
        pcu = round(pcu, 2)
        
        annotated_path = None
        # Vẽ bounding box và lưu ảnh preview nếu có yêu cầu
        if save_annotated_dir:
            os.makedirs(save_annotated_dir, exist_ok=True)
            # Tạo tên file ảnh annotated
            base_name = os.path.basename(image_path)
            annotated_path = os.path.join(save_annotated_dir, f"annotated_{base_name}")
            
            # Sử dụng hàm plot() tích hợp sẵn của YOLO để vẽ bounding box đẹp mắt
            annotated_img = result.plot()
            cv2.imwrite(annotated_path, annotated_img)

        return {
            "counts": counts,
            "total_pcu": pcu,
            "annotated_path": annotated_path
        }

if __name__ == "__main__":
    # Test thử detector độc lập
    detector = VehicleDetector()
    print("[+] Khoi tao YOLOv8 Detector thanh cong!")
