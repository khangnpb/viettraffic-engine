import os
import time
import abc
import logging
from datetime import datetime

class BaseCollector(abc.ABC):
    def __init__(self, name, source_url, output_dir, interval=30, web_url=None):
        self.name = name
        self.source_url = source_url
        self.web_url = web_url if web_url else source_url
        self.output_dir = output_dir
        self.interval = interval
        self.is_running = False
        self.status = "Stopped"
        self.last_run = None
        self.total_downloaded = 0  # Bytes
        self.count = 0  # Number of files
        
        # Setup logging
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    @abc.abstractmethod
    def collect(self):
        """Hàm thực hiện việc cào dữ liệu, phải được override ở lớp con."""
        pass

    def run(self, shared_status_dict):
        """Vòng lặp chính chạy trong tiến trình riêng."""
        self.is_running = True
        self.status = "Running"
        print(f"[*] Bắt đầu tiến trình cào: {self.name}")
        
        while self.is_running:
            try:
                # Cập nhật trạng thái cho Manager/UI
                shared_status_dict[self.name] = {
                    "status": self.status,
                    "last_run": str(datetime.now().strftime("%H:%M:%S")),
                    "total_mb": round(self.total_downloaded / (1024*1024), 2),
                    "count": self.count,
                    "web_url": self.web_url
                }
                
                # Thực hiện cào
                size = self.collect()
                if size:
                    self.total_downloaded += size
                    self.count += 1
                
                time.sleep(self.interval)
            except Exception as e:
                print(f"[!] Lỗi trong collector {self.name}: {e}")
                self.status = f"Error: {str(e)[:50]}"
                time.sleep(10) # Đợi trước khi thử lại

    def stop(self):
        self.is_running = False
        self.status = "Stopped"
