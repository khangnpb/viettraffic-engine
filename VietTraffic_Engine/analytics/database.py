import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traffic.db")

def get_connection():
    """Tạo kết nối tới SQLite Database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    return conn

def init_db():
    """Khởi tạo các bảng dữ liệu nếu chưa tồn tại."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu kết quả đếm xe và tính toán PCU thời gian thực
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,         -- Định dạng YYYY-MM-DD HH:MM:SS
        camera_id TEXT NOT NULL,
        camera_name TEXT NOT NULL,
        motorcycles INTEGER DEFAULT 0,
        cars INTEGER DEFAULT 0,
        trucks INTEGER DEFAULT 0,
        buses INTEGER DEFAULT 0,
        total_pcu REAL DEFAULT 0.0,
        los_level TEXT NOT NULL,         -- Cấp độ phục vụ: A, B, C, D, E, F
        image_path TEXT NOT NULL         -- Đường dẫn file ảnh đã xử lý
    )
    """)
    
    # Tạo index cho truy vấn nhanh hơn
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_history (timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_camera_id ON traffic_history (camera_id)")
    
    conn.commit()
    conn.close()
    print(f"[+] Da khoi tao CSDL SQLite tai: {DB_PATH}")

def insert_traffic_record(timestamp, camera_id, camera_name, motorcycles, cars, trucks, buses, total_pcu, los_level, image_path):
    """Ghi nhận một bản ghi lưu lượng xe mới vào CSDL."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO traffic_history (timestamp, camera_id, camera_name, motorcycles, cars, trucks, buses, total_pcu, los_level, image_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, camera_id, camera_name, motorcycles, cars, trucks, buses, total_pcu, los_level, image_path))
    
    conn.commit()
    conn.close()

def get_latest_traffic_status():
    """Lấy trạng thái giao thông mới nhất của tất cả camera."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Sử dụng Subquery để lấy dòng mới nhất cho mỗi camera_id
    cursor.execute("""
    SELECT t1.* 
    FROM traffic_history t1
    INNER JOIN (
        SELECT camera_id, MAX(timestamp) as max_ts
        FROM traffic_history
        GROUP BY camera_id
    ) t2 ON t1.camera_id = t2.camera_id AND t1.timestamp = t2.max_ts
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_camera_history(camera_id, limit=60):
    """Lấy dữ liệu lịch sử của một camera cụ thể để vẽ biểu đồ."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT timestamp, motorcycles, cars, trucks, buses, total_pcu, los_level
    FROM traffic_history
    WHERE camera_id = ?
    ORDER BY timestamp DESC
    LIMIT ?
    """, (camera_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    # Trả về theo thứ tự thời gian tăng dần để vẽ biểu đồ cho đẹp
    return [dict(row) for row in reversed(rows)]

def clear_old_records(days_to_keep=7):
    """(Dọn dẹp) Xóa các bản ghi quá cũ để tránh nặng Database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    DELETE FROM traffic_history 
    WHERE timestamp < datetime('now', '-' || ? || ' days')
    """, (days_to_keep,))
    
    conn.commit()
    conn.close()

# Khởi tạo CSDL ngay khi import module lần đầu
if not os.path.exists(DB_PATH):
    init_db()
