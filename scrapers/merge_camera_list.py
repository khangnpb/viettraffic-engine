import json
import os

def merge_and_update():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    old_path = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v3.json"))
    clean_path = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v4_clean.json"))
    backup_path = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v3_backup.json"))

    if not os.path.exists(old_path) or not os.path.exists(clean_path):
        print("Required files not found!")
        return

    with open(old_path, "r", encoding="utf-8") as f:
        old_cams = json.load(f)

    with open(clean_path, "r", encoding="utf-8") as f:
        clean_cams = json.load(f)

    clean_map = {c['id']: c for c in clean_cams}

    # Backup the original v3
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(old_cams, f, ensure_ascii=False, indent=4)
        print(f"Backed up original camera list to {backup_path}")

    old_coords_count = len([c for c in old_cams if c.get('lat') is not None])
    
    updated_count = 0
    new_coords_count = 0
    mismatched_cams_before_after = []

    for c in old_cams:
        cam_id = c['id']
        if cam_id in clean_map:
            clean_cam = clean_map[cam_id]
            old_lat, old_lng = c.get('lat'), c.get('lng')
            new_lat, new_lng = clean_cam.get('lat'), clean_cam.get('lng')
            
            # Update coordinate and name if mismatch or to be 100% correct
            c['lat'] = new_lat
            c['lng'] = new_lng
            
            if new_lat is not None:
                new_coords_count += 1
                
            if old_lat != new_lat or old_lng != new_lng:
                updated_count += 1
                if len(mismatched_cams_before_after) < 5:
                    mismatched_cams_before_after.append({
                        "name": c['name'],
                        "old_coord": (old_lat, old_lng),
                        "new_coord": (new_lat, new_lng)
                    })

    # Save the updated v3
    with open(old_path, "w", encoding="utf-8") as f:
        json.dump(old_cams, f, ensure_ascii=False, indent=4)

    print(f"Successfully updated {old_path}!")
    print(f"Total cameras in list: {len(old_cams)}")
    print(f"Old cameras with coordinates: {old_coords_count}")
    print(f"New cameras with coordinates: {new_coords_count}")
    print(f"Total cameras updated/shifted to correct coordinates: {updated_count}")
    print("\nSample corrections:")
    for m in mismatched_cams_before_after:
        print(f"- {m['name']}:")
        print(f"  Old: {m['old_coord']}")
        print(f"  New: {m['new_coord']}")

if __name__ == "__main__":
    merge_and_update()
