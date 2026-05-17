import os
import time
import shutil

def benchmark_drive(drive_letter, file_size_mb=500):
    test_file = os.path.join(f"{drive_letter}:\\", "test_speed.bin")
    print(f"\n--- Đang kiểm tra ổ {drive_letter}: ---")
    
    # 1. Đo tốc độ GHI (Write Speed)
    data = os.urandom(1024 * 1024) # 1MB dữ liệu ngẫu nhiên
    start_time = time.time()
    try:
        with open(test_file, 'wb') as f:
            for _ in range(file_size_mb):
                f.write(data)
        end_time = time.time()
        write_speed = file_size_mb / (end_time - start_time)
        print(f"[*] Tốc độ Ghi (Sequential Write): {write_speed:.2f} MB/s")
    except Exception as e:
        print(f"[!] Lỗi khi ghi ổ {drive_letter}: {e}")
        return

    # 2. Đo tốc độ ĐỌC (Read Speed)
    start_time = time.time()
    try:
        with open(test_file, 'rb') as f:
            while f.read(1024 * 1024):
                pass
        end_time = time.time()
        read_speed = file_size_mb / (end_time - start_time)
        print(f"[*] Tốc độ Đọc (Sequential Read): {read_speed:.2f} MB/s")
    except Exception as e:
        print(f"[!] Lỗi khi đọc ổ {drive_letter}: {e}")

    # Xóa file tạm
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    # Thay đổi danh sách ổ đĩa bạn muốn kiểm tra ở đây
    drives = ['D', 'A']
    
    for drive in drives:
        if os.path.exists(f"{drive}:\\"):
            benchmark_drive(drive)
        else:
            print(f"\n[!] Không tìm thấy ổ {drive}:")
