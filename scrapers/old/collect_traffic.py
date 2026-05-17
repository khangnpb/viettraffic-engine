import os
import time
import cv2
import subprocess

class TrafficCollector:
    def __init__(self, base_path="A:/TrafficData"):
        # Kiểm tra xem ổ đĩa có tồn tại không
        drive = os.path.splitdrive(base_path)[0]
        if not os.path.exists(drive):
            print(f"[!] CẢNH BÁO: Không tìm thấy ổ đĩa {drive}. Vui lòng kiểm tra lại kết nối ổ cứng rời.")
            # Nếu không thấy ổ A, có thể tạm thời chuyển về D hoặc báo lỗi
            return

        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            os.makedirs(os.path.join(base_path, "videos"))
            os.makedirs(os.path.join(base_path, "snapshots"))
            print(f"[+] Đã khởi tạo cấu trúc thư mục tại: {base_path}")

    def download_youtube_stream(self, url, duration_sec=60, filename="stream.mp4"):
        """
        Tải một đoạn livestream từ YouTube bằng yt-dlp.
        Cần cài đặt yt-dlp: pip install yt-dlp
        """
        output_path = os.path.join(self.base_path, "videos", filename)
        print(f"[*] Đang tải stream từ YouTube: {url}")
        # Lệnh yt-dlp để tải đoạn video với thời gian giới hạn
        # Lưu ý: Cần có ffmpeg trong máy
        cmd = [
            "yt-dlp",
            "--external-installer", "ffmpeg",
            "--external-installer-args", f"ffmpeg:-t {duration_sec}",
            "-o", output_path,
            url
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"[+] Đã lưu video tại: {output_path}")
        except Exception as e:
            print(f"[!] Lỗi khi tải YouTube: {e}")

    def capture_snapshot(self, img_url, intersection_name="nga_tu"):
        """
        Chụp ảnh snapshot từ một URL ảnh định kỳ (thường là camera giao thông web).
        """
        import requests
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        folder = os.path.join(self.base_path, "snapshots", intersection_name)
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        filepath = os.path.join(folder, f"{intersection_name}_{timestamp}.jpg")
        try:
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"[+] Đã chụp ảnh: {filepath}")
            else:
                print(f"[!] Không thể lấy ảnh. Status code: {response.status_code}")
        except Exception as e:
            print(f"[!] Lỗi: {e}")

if __name__ == "__main__":
    collector = TrafficCollector()
    
    # Ví dụ 1: Tải 30 giây từ một kênh livestream (Thay URL bằng link thật)
    # collector.download_youtube_stream("https://www.youtube.com/watch?v=EXAMPLE", duration_sec=30)
    
    # Ví dụ 2: Chụp ảnh định kỳ (Lặp lại bằng loop nếu muốn)
    # image_url = "http://giaothong.hochiminhcity.gov.vn/render/ImageHandler.ashx?id=..."
    # collector.capture_snapshot(image_url, "Nga_Tu_Hang_Xanh")
    
    print("\n[!] Script đã sẵn sàng. Hãy điền URL vào phần ví dụ để bắt đầu.")
