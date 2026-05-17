import folium
import os
import base64
import sys
import re
from datetime import datetime

def get_gmaps_tile_path(cctv_image_path):
    """
    Từ đường dẫn ảnh YOLO (annotated CCTV snapshot),
    suy ra đường dẫn ảnh Live Traffic tương ứng từ Google Maps.
    Nếu không có file trùng khít giây, tự động tìm file có thời gian gần nhất trong vòng 5 phút.
    """
    if not cctv_image_path:
        return None
    try:
        norm_path = os.path.normpath(cctv_image_path)
        parts = norm_path.split(os.sep)
        
        # annotated\<folder_name>\annotated_<timestamp>.jpg
        folder_name = parts[-2]
        filename = parts[-1]
        
        # Bóc tách YYYYMMDD_HHMMSS từ tên file CCTV
        match = re.search(r'(\d{8}_\d{6})', filename)
        if not match:
            return None
            
        cctv_ts_str = match.group(1)
        cctv_dt = datetime.strptime(cctv_ts_str, "%Y%m%d_%H%M%S")
        
        gmap_folder = os.path.join(r"A:\TrafficData\TrafficAssessmentbyGoogle Maps", folder_name)
        if not os.path.exists(gmap_folder):
            return None
            
        # Liệt kê tất cả các file trong folder gmap để tìm file có thời gian tiệm cận nhất
        gmap_files = os.listdir(gmap_folder)
        best_path = None
        min_diff = float('inf')
        
        for f in gmap_files:
            if f.endswith("_google_traffic.png"):
                m = re.search(r'(\d{8}_\d{6})', f)
                if m:
                    gmap_ts_str = m.group(1)
                    try:
                        gmap_dt = datetime.strptime(gmap_ts_str, "%Y%m%d_%H%M%S")
                        diff = abs((cctv_dt - gmap_dt).total_seconds())
                        
                        # Chấp nhận sai lệch thời gian tối đa 5 phút (300 giây)
                        if diff < 300 and diff < min_diff:
                            min_diff = diff
                            best_path = os.path.join(gmap_folder, f)
                    except ValueError:
                        pass
        
        return best_path
    except Exception as e:
        print(f"[!] Lỗi khi tìm đường dẫn Google Maps tile: {e}")
    return None

# Đảm bảo import được các module khác
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.geocoder import load_clean_cameras
from analytics.database import get_latest_traffic_status
from analytics.density import get_los_color, calculate_los

def get_base64_image(image_path):
    """Đọc ảnh từ đĩa và mã hóa base64 để nhúng trực tiếp vào Folium Popup."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"[!] Lỗi chuyển base64 ảnh {image_path}: {e}")
        return None

def generate_traffic_map():
    """
    Tạo bản đồ số Folium, nạp các camera từ sources.json và 
    hiển thị mật độ giao thông thời gian thực từ CSDL SQLite.
    """
    # Khởi tạo bản đồ Quận 1, TP.HCM làm tâm
    hcm_center = [10.7769, 106.7009]
    m = folium.Map(location=hcm_center, zoom_start=13, tiles="cartodbpositron")
    
    # Load metadata của tất cả camera có tọa độ
    cameras = load_clean_cameras(auto_geocode=False)
    
    # Load trạng thái giao thông mới nhất từ CSDL
    latest_statuses = get_latest_traffic_status()
    # Chuyển thành dict để tra cứu O(1) theo camera_id
    status_dict = {status["camera_id"]: status for status in latest_statuses}
    
    for cam_id, cam_info in cameras.items():
        lat = cam_info["lat"]
        lng = cam_info["lng"]
        name = cam_info["name"]
        
        # Kiểm tra xem camera đã có bản ghi trong DB chưa
        if cam_id in status_dict:
            status = status_dict[cam_id]
            pcu = status["total_pcu"]
            los_level = status["los_level"]
            motorcycles = status["motorcycles"]
            cars = status["cars"]
            trucks = status["trucks"]
            buses = status["buses"]
            timestamp = status["timestamp"]
            image_path = status["image_path"]
            
            # Tính toán phân cấp LOS và màu sắc
            los_info = calculate_los(pcu)
            color = los_info["color"]
            los_status = los_info["status"]
            los_desc = los_info["description"]
            
            # Nhúng ảnh YOLO đã vẽ bounding box vào popup dạng base64
            img_base64 = get_base64_image(image_path)
            
            # Nhúng ảnh Google Maps Traffic Tile tương ứng dạng base64
            gmap_path = get_gmaps_tile_path(image_path)
            gmap_base64 = get_base64_image(gmap_path) if gmap_path else None
            
            # Khởi tạo khung HTML Popup cực kỳ chuyên nghiệp rộng ngang 240px
            # Sử dụng transition để thu nhỏ/phóng to mượt mà
            popup_html = f"""
            <style>
                .leaflet-popup-content-wrapper {{
                    width: auto !important;
                    transition: width 0.2s ease-in-out !important;
                }}
                .leaflet-popup-content {{
                    width: auto !important;
                    transition: width 0.2s ease-in-out !important;
                    margin: 12px 14px !important;
                }}
            </style>
            <div id="popup-container-{cam_id}" style="font-family: 'Arial', sans-serif; width: 240px; font-size: 13px; transition: width 0.2s; overflow: hidden;">
                <h4 style="margin: 0 0 5px 0; color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 3px;">
                    🚦 {name}
                </h4>
                <p style="margin: 3px 0;"><b>Trạng thái:</b> <span style="color: {color}; font-weight: bold;">{los_status} (LOS {los_level})</span></p>
                <p style="margin: 3px 0;"><b>Mật độ quy đổi:</b> {pcu} PCU</p>
                <p style="margin: 3px 0;"><b>Thời gian quét:</b> {timestamp}</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 11px; text-align: center;">
                    <tr style="background-color: #f8f9fa; border-bottom: 1px solid #ddd;">
                        <th style="padding: 3px;">🏍️ Xe máy</th>
                        <th style="padding: 3px;">🚗 Ô tô</th>
                        <th style="padding: 3px;">🚛 Xe tải</th>
                        <th style="padding: 3px;">🚌 Buýt</th>
                    </tr>
                    <tr>
                        <td style="padding: 3px; font-weight: bold;">{motorcycles}</td>
                        <td style="padding: 3px; font-weight: bold;">{cars}</td>
                        <td style="padding: 3px; font-weight: bold;">{trucks}</td>
                        <td style="padding: 3px; font-weight: bold;">{buses}</td>
                    </tr>
                </table>
            """
            
            if img_base64 or gmap_base64:
                # Hiển thị nằm ngang (Flexbox side-by-side)
                popup_html += '<div style="display: flex; gap: 8px; margin-top: 10px; justify-content: space-between;">'
                if img_base64:
                    popup_html += f"""
                    <div style="flex: 1; border: 1px solid #ddd; border-radius: 6px; padding: 4px; background: #fcfcfc; text-align: center; min-width: 100px;">
                        <div style="font-size: 9px; font-weight: bold; color: #2c3e50; margin-bottom: 2px; text-align: left;">📸 YOLOv8:</div>
                        <img src="{img_base64}" style="width: 100%; max-width: 100px; height: auto; border-radius: 4px; display: block; margin: 0 auto; transition: max-width 0.2s; cursor: zoom-in;"
                             onclick="
                               var parent = document.getElementById('popup-container-{cam_id}');
                               if(this.style.maxWidth=='100px') {{
                                 this.style.maxWidth='260px';
                                 this.style.cursor='zoom-out';
                                 parent.style.width='480px';
                               }} else {{
                                 this.style.maxWidth='100px';
                                 this.style.cursor='zoom-in';
                                 var imgs = parent.getElementsByTagName('img');
                                 var all_small = true;
                                 for(var i=0; i<imgs.length; i++) {{
                                   if(imgs[i] !== this && imgs[i].style.maxWidth === '260px') {{
                                     all_small = false;
                                   }}
                                 }}
                                 if(all_small) parent.style.width='240px';
                               }}
                             "
                        />
                    </div>
                    """
                if gmap_base64:
                    popup_html += f"""
                    <div style="flex: 1; border: 1px solid #ddd; border-radius: 6px; padding: 4px; background: #fcfcfc; text-align: center; min-width: 100px;">
                        <div style="font-size: 9px; font-weight: bold; color: #2c3e50; margin-bottom: 2px; text-align: left;">🗺️ GMap:</div>
                        <img src="{gmap_base64}" style="width: 100%; max-width: 100px; height: auto; border-radius: 4px; display: block; margin: 0 auto; transition: max-width 0.2s; cursor: zoom-in;"
                             onclick="
                               var parent = document.getElementById('popup-container-{cam_id}');
                               if(this.style.maxWidth=='100px') {{
                                 this.style.maxWidth='260px';
                                 this.style.cursor='zoom-out';
                                 parent.style.width='480px';
                               }} else {{
                                 this.style.maxWidth='100px';
                                 this.style.cursor='zoom-in';
                                 var imgs = parent.getElementsByTagName('img');
                                 var all_small = true;
                                 for(var i=0; i<imgs.length; i++) {{
                                   if(imgs[i] !== this && imgs[i].style.maxWidth === '260px') {{
                                     all_small = false;
                                   }}
                                 }}
                                 if(all_small) parent.style.width='240px';
                               }}
                             "
                        />
                    </div>
                    """
                popup_html += '</div>'
            else:
                popup_html += """
                <div style="margin-top: 10px; background-color: #f1f2f6; height: 100px; line-height: 100px; text-align: center; color: #7f8c8d; border-radius: 4px;">
                    Chưa có hình ảnh preview
                </div>
                """
                
            popup_html += "</div>"
            
        else:
            # Chưa có dữ liệu xử lý trong DB cho camera này
            color = "#7f8c8d"  # Màu xám (Gray)
            popup_html = f"""
            <div style="font-family: 'Arial', sans-serif; width: 220px; font-size: 13px;">
                <h4 style="margin: 0 0 5px 0; color: #7f8c8d; border-bottom: 2px solid #7f8c8d; padding-bottom: 3px;">
                    🚦 {name}
                </h4>
                <p style="margin: 5px 0; color: #e67e22; font-weight: bold;">⚠️ Đang chờ đồng bộ dữ liệu...</p>
                <p style="font-size: 11px; color: #7f8c8d; margin: 3px 0;">
                    Ảnh snapshot của camera này đang được cào ngầm và đợi YOLOv8 xử lý. Vui lòng bật `run_processor.py`.
                </p>
            </div>
            """
            
        # Thêm CircleMarker thể hiện điểm nút giao động trên bản đồ
        folium.CircleMarker(
            location=[lat, lng],
            radius=8,
            popup=folium.Popup(popup_html, max_width=500),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=1.5
        ).add_to(m)
        
    return m

if __name__ == "__main__":
    # Test thử hàm sinh map
    m = generate_traffic_map()
    m.save("test_map.html")
    print("[+] Sinh bản đồ mẫu test_map.html thành công!")
