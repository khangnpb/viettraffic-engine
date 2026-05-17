import re
import json
import os

def parse_safely():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(os.path.join(script_dir, "..", "data", "debug_api", "158__Web_Library_AJAX_FolderAjax_VDMS_Web_Library_ashx.txt"))
    if not os.path.exists(file_path):
        print("Input file not found!")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the main data rows array
    # It starts after: [["Title","System.Object"],...,["DynamicProperties","System.Object"]],[
    # and ends before: ],null
    # Let's use re to find the big DataTable call
    match = re.search(r'new Ajax\.Web\.DataTable\(\[\["Title".*?\]\],\[(.*?)\]\),null', content)
    if not match:
        print("Could not find main DataTable in raw text!")
        # Fallback to search using parts
        return

    rows_str = match.group(1)
    
    # Since rows are separated by ],[ in the outer list, let's find all rows.
    # Note that inside each row, there is a nested new Ajax.Web.DataTable(..., [...]), so simple split('],[')
    # might split the nested DataTable array. 
    # To split correctly, we can scan the string and track nested bracket depth, or use a regex to match
    # each camera row structurally.
    # Structurally, a camera row looks like:
    # ["Title", null/desc, "CamId", "Code", new Ajax.Web.DataTable(..., [[...]]), null/url, "CamType", ..., "DisplayName", ...]
    
    # Let's parse it by scanning character by character or using a state machine to split by outer commas that are at level 1 nesting!
    # Let's write a robust bracket tokenizer:
    rows = []
    current_row = []
    current_token = []
    in_quotes = False
    quote_char = None
    bracket_depth = 0
    i = 0
    n = len(rows_str)
    
    while i < n:
        char = rows_str[i]
        
        # Handle escape characters
        if char == '\\' and i + 1 < n:
            current_token.append(char)
            current_token.append(rows_str[i+1])
            i += 2
            continue
            
        # Handle quotes
        if (char == '"' or char == "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current_token.append(char)
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current_token.append(char)
        elif in_quotes:
            current_token.append(char)
        else:
            # Not in quotes, track brackets
            if char in ('[', '('):
                bracket_depth += 1
                current_token.append(char)
            elif char in (']', ')'):
                bracket_depth -= 1
                current_token.append(char)
            elif char == ',' and bracket_depth == 0:
                # We hit a column separator for the row
                col_val = "".join(current_token).strip()
                current_row.append(col_val)
                current_token = []
            elif char == '\n' or char == '\r':
                pass # skip whitespaces
            else:
                current_token.append(char)
        i += 1
        
    # Append last token
    if current_token:
        current_row.append("".join(current_token).strip())
        
    # Now we have all column values in a single flat list. But wait! The outer list is a list of rows, so:
    # rows_str was: ["Row1Col1", ...], ["Row2Col1", ...]
    # So we can group by bracket depth 0 at the row level!
    # Let's write a simple bracket depth tracker to split rows first, then parse columns!
    print("Parsing outer rows...")
    
def parse_by_row_bracketing():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(os.path.join(script_dir, "..", "data", "debug_api", "158__Web_Library_AJAX_FolderAjax_VDMS_Web_Library_ashx.txt"))
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find the start of the rows array
    header_marker = '[["Title","System.Object"]'
    start_pos = content.find(header_marker)
    if start_pos == -1:
        print("Header marker not found!")
        return
        
    # Find the opening '[' of the rows list
    # It is right after the schemas definition: ... ]],[ ...
    idx = content.find(']],[', start_pos)
    if idx == -1:
        print("Rows start list not found!")
        return
        
    rows_start_idx = idx + 3 # Points to the '[' of the rows list: [[row1], [row2], ...]
    
    # Let's trace the outer list elements
    # We want to extract each [row] from [[row1], [row2], ..., [rowN]]
    bracket_depth = 0
    in_quotes = False
    escape = False
    current_row = []
    
    cameras = []
    
    i = rows_start_idx + 1 # Skip the opening '[' of the rows list
    n = len(content)
    row_count = 0
    
    while i < n:
        char = content[i]
        
        if escape:
            current_row.append(char)
            escape = False
            i += 1
            continue
            
        if char == '\\':
            current_row.append(char)
            escape = True
            i += 1
            continue
            
        if char == '"':
            in_quotes = not in_quotes
            current_row.append(char)
            i += 1
            continue
            
        if in_quotes:
            current_row.append(char)
            i += 1
            continue
            
        # Outside quotes
        if char == '[':
            bracket_depth += 1
            current_row.append(char)
        elif char == ']':
            bracket_depth -= 1
            current_row.append(char)
            if bracket_depth == 0:
                # Finished a row!
                row_str = "".join(current_row).strip()
                # Parse the columns of this row
                parse_row_cols(row_str, cameras)
                current_row = []
                row_count += 1
        elif char == ',' and bracket_depth == 0:
            # This is the separator between rows, skip it
            pass
        elif char == ']' and bracket_depth == -1:
            # We reached the end of the rows list!
            break
        else:
            current_row.append(char)
        i += 1
        
    print(f"Extracted {len(cameras)} valid cameras with proper coordinates.")
    
    # Save output to clean camera file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(script_dir, "..", "data", "hcm_cameras_v4_clean.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cameras, f, ensure_ascii=False, indent=4)
    print(f"Saved cleaned cameras to {output_path}")

def parse_row_cols(row_str, cameras):
    # A row string looks like: ["TTH 406",null,"662b86c41afb9c00172dd31c","TTH 406",new Ajax.Web.DataTable([["GeoId","System.Object"],["Shape","System.Object"],["Number","System.Object"],["Street","System.Object"],["Ward","System.Object"],["District","System.Object"],["Province","System.Object"],["Description","System.Object"]],[["1f7c2a70-f4ea-41ac-8fd9-670b28ec73f3","POINT(106.691054105759 10.7918902432446)",null,null,null,null,null,null]]),null,"tth",null,"True",null,"UP","True",null,"Trần Quang Khải - Trần Khắc Chân",null,0,null,"687ce800-704f-4abf-9589-e7688ff2b527","/root/vdms/tangthu/data/layerdata/camera/8c5fb875-b91d-4552-8b5d-4507c64d41f0","\/Date(1714374229803)\/","\/Date(1778736092564)\/",null]
    # Let's extract columns:
    # 1. Title/Name
    # 2. CamId (24 hex characters)
    # 3. Location coordinates (from the nested POINT)
    # 4. Status (UP/DOWN/NOT_IMAGE)
    # 5. DisplayName
    
    # To do this safely, let's extract:
    # - CamId: 24 hex char in quotes
    # - POINT(lng lat): match POINT\(([\d.]+) ([\d.]+)\)
    # - DisplayName: is the string right before null,0,null or similar, or let's use regex to find the display name column.
    # Looking at the schema:
    # 0: Title ("TTH 406")
    # 1: Description (null)
    # 2: CamId ("662b86c41afb9c00172dd31c")
    # 3: Code ("TTH 406")
    # 4: Location (nested DataTable containing POINT)
    # 5: SnapshotUrl (null or string)
    # 6: CamType ("tth")
    # 7: District (null or string)
    # 8: Publish ("True")
    # 9: ManagementUnit (null or string)
    # 10: CamStatus ("UP" or "DOWN")
    # 11: PTZ ("True")
    # 12: Angle (null)
    # 13: DisplayName ("Trần Quang Khải - Trần Khắc Chân")
    
    # Let's split the columns of the row using the same bracket depth tracker!
    cols = []
    current_col = []
    bracket_depth = 0
    in_quotes = False
    escape = False
    
    # Remove leading '[' and trailing ']' of the row
    if row_str.startswith('[') and row_str.endswith(']'):
        row_body = row_str[1:-1]
    else:
        row_body = row_str
        
    i = 0
    n = len(row_body)
    while i < n:
        char = row_body[i]
        
        if escape:
            current_col.append(char)
            escape = False
            i += 1
            continue
            
        if char == '\\':
            current_col.append(char)
            escape = True
            i += 1
            continue
            
        if char == '"':
            in_quotes = not in_quotes
            current_col.append(char)
            i += 1
            continue
            
        if in_quotes:
            current_col.append(char)
            i += 1
            continue
            
        if char in ('[', '('):
            bracket_depth += 1
            current_col.append(char)
        elif char in (']', ')'):
            bracket_depth -= 1
            current_col.append(char)
        elif char == ',' and bracket_depth == 0:
            cols.append("".join(current_col).strip())
            current_col = []
        else:
            current_col.append(char)
        i += 1
        
    if current_col:
        cols.append("".join(current_col).strip())
        
    # Check if we have at least 14 columns
    if len(cols) >= 14:
        cam_id_raw = cols[2]
        display_name_raw = cols[13]
        location_raw = cols[4]
        status_raw = cols[10]
        
        # Clean quotes
        def clean_val(val):
            if val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            if val == 'null':
                return None
            return val
            
        cam_id = clean_val(cam_id_raw)
        name = clean_val(display_name_raw)
        status = clean_val(status_raw)
        
        # Fallback to Title if DisplayName is null
        if not name:
            name = clean_val(cols[0])
            
        # Extract coordinates
        lat = None
        lng = None
        point_match = re.search(r'POINT\(([\d.]+) ([\d.]+)\)', location_raw)
        if point_match:
            lng = float(point_match.group(1))
            lat = float(point_match.group(2))
            
        if cam_id:
            cameras.append({
                "id": cam_id,
                "name": name,
                "lat": lat,
                "lng": lng,
                "url": f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={cam_id}&bg=black&w=520&h=300",
                "status": status if status else "UNKNOWN"
            })

if __name__ == "__main__":
    parse_by_row_bracketing()
