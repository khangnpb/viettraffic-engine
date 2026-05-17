import subprocess
import sys
import os

if __name__ == "__main__":
    print("[*] Đang khởi động VietTraffic Data Engine...")
    # Đường dẫn tới file app.py
    app_path = os.path.join("VietTraffic_Engine", "ui", "app.py")
    
    # Chạy lệnh streamlit run
    try:
        subprocess.run(["streamlit", "run", app_path], check=True)
    except KeyboardInterrupt:
        print("\n[-] Đã dừng hệ thống.")
    except Exception as e:
        print(f"[!] Lỗi khi khởi động: {e}")
