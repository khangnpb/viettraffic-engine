import requests
import os
import time
from datetime import datetime
from core.base_collector import BaseCollector

class HCMCCollector(BaseCollector):
    def __init__(self, name, camera_id, output_dir, interval=30):
        # Cập nhật URL theo mẫu người dùng cung cấp (Port 8007)
        w = 520
        h = 300
        self.camera_id = camera_id
        source_url = f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={camera_id}&bg=black&w={w}&h={h}"
        web_url = "https://giaothong.hochiminhcity.gov.vn/"
        super().__init__(name, source_url, output_dir, interval, web_url=web_url)

    def collect(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Giả lập trình duyệt để tránh bị server chặn
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://giaothong.hochiminhcity.gov.vn/"
            }
            # Thêm tham số t để tránh cache
            current_url = f"{self.source_url}&t={int(time.time() * 1000)}"
            response = requests.get(current_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return len(response.content)
            else:
                return 0
        except Exception as e:
            raise e
