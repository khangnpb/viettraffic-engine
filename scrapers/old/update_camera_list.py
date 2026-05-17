import json
import os
import sys
import re

# Set output encoding to UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
DEBUG_FILE = r'd:\4_MasterBachKhoa\HK252\Thực tập 2\debug_api\158__Web_Library_AJAX_FolderAjax_VDMS_Web_Library_ashx.txt'
OLD_JSON = r'd:\4_MasterBachKhoa\HK252\Thực tập 2\hcm_cameras_final.json'
OUTPUT_JSON = r'd:\4_MasterBachKhoa\HK252\Thực tập 2\hcm_cameras_v2.json'

def parse_debug_log(file_path):
    print(f"Parsing debug log: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The file contains NodeInfo objects for cameras.
    # They look like: {"__type":"VDMS.Sense.Helper.Model.NodeInfo, ... "Type":"file", ...}
    # We can use regex to find each one.
    
    # Each node starts with this specific string
    node_marker = '{"__type":"VDMS.Sense.Helper.Model.NodeInfo'
    
    # We split by marker and process each chunk
    chunks = content.split(node_marker)
    
    cameras = []
    print(f"Found {len(chunks)-1} potential nodes.")
    
    for chunk in chunks[1:]:
        # We need to find the end of this object. 
        # Since it's a nested structure, we look for the end of the NodeInfo object.
        # A simple way is to find the next node marker or the end of the properties array.
        # However, for our purposes, we just need CamId and Title which are usually at the start.
        
        # We'll try to parse as much as possible until it fails
        # Or better, just use regex to extract the specific fields we need from the chunk
        
        # Extract Title
        title_match = re.search(r'"Title":"(.*?)"', chunk)
        title = title_match.group(1) if title_match else "Unknown"
        
        # Extract CamId (it's inside Properties)
        # Properties looks like: "Properties":[{"__type":...,"Name":"CamId",...,"Value":"ID_HERE",...}, ...]
        cam_id_match = re.search(r'"Name":"CamId".*?"Value":"(.*?)"', chunk)
        cam_id = cam_id_match.group(1) if cam_id_match else None
        
        # Extract Status
        status_match = re.search(r'"Name":"CamStatus".*?"Value":"(.*?)"', chunk)
        status = status_match.group(1) if status_match else "UNKNOWN"

        # Check if it's a camera (Type: file)
        type_match = re.search(r'"Type":"(.*?)"', chunk)
        node_type = type_match.group(1) if type_match else ""
        
        if cam_id and node_type == "file":
            cameras.append({
                'id': cam_id,
                'title': title,
                'status': status
            })
            
    return cameras

def merge_data():
    # Load old data
    if os.path.exists(OLD_JSON):
        with open(OLD_JSON, 'r', encoding='utf-8') as f:
            old_cameras = json.load(f)
        print(f"Loaded {len(old_cameras)} cameras from existing list.")
    else:
        old_cameras = []
        print("Existing camera list not found. Starting from scratch.")
    
    old_map = {c['id']: c for c in old_cameras}
    
    # Parse new data
    new_nodes = parse_debug_log(DEBUG_FILE)
    print(f"Parsed {len(new_nodes)} nodes from debug log.")
    
    merged_list = []
    for node in new_nodes:
        cam_id = node['id']
        
        if cam_id in old_map:
            # Keep old metadata but use new ID (it's the same anyway)
            cam = old_map[cam_id].copy()
            # Update/Ensure URL is standard
            cam['url'] = f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={cam_id}&bg=black&w=520&h=300"
            # Add status
            cam['status'] = node.get('status', 'UNKNOWN')
            merged_list.append(cam)
        else:
            # NEW camera
            cam = {
                "id": cam_id,
                "name": node['title'],
                "lat": None,
                "lng": None,
                "url": f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={cam_id}&bg=black&w=520&h=300",
                "status": node.get('status', 'UNKNOWN')
            }
            merged_list.append(cam)
    
    # Save output
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully merged. Total cameras in v2: {len(merged_list)}")
    print(f"Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    merge_data()
