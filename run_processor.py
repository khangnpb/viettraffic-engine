#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VietTraffic - Live Image Processor & DB Sync Launcher (YOLOv8)
Author: Master Bach Khoa Student Project
"""

import sys
import os
import subprocess

# Append project root to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("[*] Đang khởi động Động cơ Xử lý Ảnh AI (YOLOv8 & DB Sync)...")
    
    # Đường dẫn tới file run_processor.py bên trong VietTraffic_Engine
    processor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "VietTraffic_Engine", "run_processor.py"))
    
    try:
        # Chạy file xử lý thô trong unbuffered mode
        subprocess.run([sys.executable, "-u", processor_path], check=True)
    except KeyboardInterrupt:
        print("\n[-] Đã dừng động cơ xử lý ảnh AI.")
    except Exception as e:
        print(f"[!] Lỗi khi khởi động động cơ: {e}")
