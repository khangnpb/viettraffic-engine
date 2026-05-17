def calculate_los(total_pcu):
    """
    Quy đổi chỉ số PCU sang cấp độ phục vụ LOS (Level of Service) theo chuẩn giao thông.
    Dành cho viewport camera tĩnh HCMC (kích thước ~520x300):
    
    - LOS A & B: Rất thông thoáng (Xanh lá)
    - LOS C: Bình thường / Ổn định (Xanh lá sẫm)
    - LOS D: Bắt đầu đông (Vàng)
    - LOS E: Rất đông / Chậm chạp (Cam)
    - LOS F: Kẹt xe nghiêm trọng (Đỏ)
    """
    if total_pcu <= 5.0:
        return {
            "level": "A",
            "color": "#2ecc71",  # Xanh lục sáng (Green)
            "status": "Thông thoáng",
            "description": "Đường trống, các phương tiện di chuyển tự do với vận tốc tối đa."
        }
    elif total_pcu <= 15.0:
        return {
            "level": "C",
            "color": "#27ae60",  # Xanh lục đậm
            "status": "Ổn định",
            "description": "Lưu lượng trung bình, dòng xe di chuyển ổn định và trật tự."
        }
    elif total_pcu <= 25.0:
        return {
            "level": "D",
            "color": "#f1c40f",  # Vàng (Yellow)
            "status": "Đông đúc",
            "description": "Lưu lượng xe tăng cao, các xe di chuyển sát nhau nhưng chưa kẹt."
        }
    elif total_pcu <= 35.0:
        return {
            "level": "E",
            "color": "#e67e22",  # Cam (Orange)
            "status": "Ún ứ",
            "description": "Mật độ xe bão hòa, vận tốc giảm mạnh, xuất hiện ún ứ nhẹ."
        }
    else:
        return {
            "level": "F",
            "color": "#e74c3c",  # Đỏ (Red)
            "status": "Kẹt xe",
            "description": "Kẹt xe cục bộ/kéo dài, dòng xe tê liệt hoặc di chuyển cực kỳ khó khăn."
        }

def get_los_color(level):
    """Tiện ích trả về mã màu hex dựa trên level LOS."""
    colors = {
        "A": "#2ecc71",
        "B": "#2ecc71",
        "C": "#27ae60",
        "D": "#f1c40f",
        "E": "#e67e22",
        "F": "#e74c3c"
    }
    return colors.get(level, "#95a5a6")
