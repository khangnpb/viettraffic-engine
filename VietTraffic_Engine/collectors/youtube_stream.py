import os
import subprocess
from datetime import datetime
from core.base_collector import BaseCollector

class YouTubeCollector(BaseCollector):
    def __init__(self, name, video_url, output_dir, segment_duration=600):
        """
        segment_duration: Độ dài mỗi clip (giây). Mặc định 10 phút.
        """
        super().__init__(name, video_url, output_dir, interval=5) # Check every 5s if process alive
        self.segment_duration = segment_duration

    def collect(self):
        # YouTube Collector khác biệt: Nó chạy một tiến trình con kéo dài
        # thay vì lặp lại theo interval. 
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{timestamp}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        # Lệnh yt-dlp để tải đoạn livestream
        cmd = [
            "yt-dlp",
            "--external-installer", "ffmpeg",
            "--external-installer-args", f"ffmpeg:-t {self.segment_duration}",
            "-o", filepath,
            self.source_url
        ]
        
        try:
            # Chạy và đợi tải xong clip
            result = subprocess.run(cmd, capture_output=True, text=True)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                return size
            return 0
        except Exception as e:
            raise e
