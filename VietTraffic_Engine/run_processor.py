import time
import os
import sys

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processor.sync_engine import SyncEngine

if __name__ == "__main__":
    print("==================================================")
    print("   VIETTRAFFIC LIVE IMAGE PROCESSOR & DB SYNC    ")
    print("==================================================")
    print("[*] Khoi tao YOLOv8 Detector...")
    
    try:
        engine = SyncEngine()
        print("[+] YOLOv8 Detector khoi tao THANH CONG!")
    except Exception as e:
        print(f"[!] That bai khi khoi tao YOLOv8 Detector: {e}")
        sys.exit(1)
        
    print("[*] Bat dau chay vong lap dong bo ngam (Chu ky: 10 giay).")
    print("[*] Dang quet snapshots o o dia A: va ghi nhan ket qua dem xe vao SQLite...")
    print("[*] Nhan Ctrl+C de tat chuong trinh.")
    
    while True:
        try:
            engine.sync_once()
            # Ngủ 10 giây trước khi quét đợt tiếp theo
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n[-] Dang tat tien trinh xu ly anh nen. Da thoat an toan!")
            break
        except Exception as e:
            print(f"[!] Loi phat sinh trong chu ky xu ly: {e}")
            time.sleep(10)
