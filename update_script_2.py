import sys
import math
import re

filepath = 'd:/HTCH/smart-rescue-dispatch-system-v2/django_app/portal/what3words_views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# find the start of URBAN_BOUNDS
start_match = re.search(r'# Nội thành: Quy Nhơn', content)
if not start_match:
    print('Start not found')
    sys.exit(1)

start_idx = start_match.start()

# find the end of api_grid_section
end_match = re.search(r"return JsonResponse\(\{'success': True, 'data': features\}\)", content)
if not end_match:
    print('End not found')
    sys.exit(1)

end_idx = end_match.end()

new_logic = """# Danh sách 4 đô thị lõi (3x3m)
URBAN_RECTS = [
    # Quy Nhơn
    {'south': 13.70, 'north': 13.85, 'west': 109.10, 'east': 109.30},
    # Pleiku
    {'south': 13.90, 'north': 14.05, 'west': 107.95, 'east': 108.10},
    # An Nhơn
    {'south': 13.82, 'north': 13.93, 'west': 109.02, 'east': 109.15},
    # Hoài Nhơn
    {'south': 14.35, 'north': 14.48, 'west': 108.95, 'east': 109.08},
]

# Vùng đệm (6x6m): mở rộng xung quanh 4 đô thị lõi
SUBURBAN_RECTS = []
for u in URBAN_RECTS:
    SUBURBAN_RECTS.append({
        'south': u['south'] - 0.05,
        'north': u['north'] + 0.05,
        'west': u['west'] - 0.05,
        'east': u['east'] + 0.05,
    })

# Gốc lưới chung (để đảm bảo các ô khớp nhau)
GRID_ORIGIN_LAT = 12.8
GRID_ORIGIN_LNG = 107.3

def get_zone(latitude, longitude):
    \"\"\"Trả về zone: 0=urban, 1=suburban, 2=rural\"\"\"
    for u in URBAN_RECTS:
        if u['south'] <= latitude <= u['north'] and u['west'] <= longitude <= u['east']:
            return 0  # urban

    for s in SUBURBAN_RECTS:
        if s['south'] <= latitude <= s['north'] and s['west'] <= longitude <= s['east']:
            return 1  # suburban

    return 2  # rural

def cell_size_m(zone):
    if zone == 0:
        return URBAN_CELL_M
    elif zone == 1:
        return SUBURBAN_CELL_M
    else:
        return RURAL_CELL_M

def cell_lat_size(zone):
    return cell_size_m(zone) / 111111.0

def cell_lng_size(zone, lat=10.765):
    return cell_size_m(zone) / (111111.0 * math.cos(math.radians(lat)))
"""

subtract_funcs = """
# ───────────────────────────────────────────────────────────────
# Helper line subtraction
# ───────────────────────────────────────────────────────────────
def subtract_rect_lng(segs, rects, lng):
    res = []
    for s_start, s_end in segs:
        current_segs = [(s_start, s_end)]
        for r in rects:
            if r['west'] <= lng <= r['east']:
                next_segs = []
                for cs, ce in current_segs:
                    if ce <= r['south'] or cs >= r['north']:
                        next_segs.append((cs, ce))
                    else:
                        if cs < r['south']: next_segs.append((cs, r['south']))
                        if ce > r['north']: next_segs.append((r['north'], ce))
                current_segs = next_segs
        res.extend(current_segs)
    return res

def subtract_rect_lat(segs, rects, lat):
    res = []
    for s_start, s_end in segs:
        current_segs = [(s_start, s_end)]
        for r in rects:
            if r['south'] <= lat <= r['north']:
                next_segs = []
                for cs, ce in current_segs:
                    if ce <= r['west'] or cs >= r['east']:
                        next_segs.append((cs, ce))
                    else:
                        if cs < r['west']: next_segs.append((cs, r['west']))
                        if ce > r['east']: next_segs.append((r['east'], ce))
                current_segs = next_segs
        res.extend(current_segs)
    return res

def get_segs_inside_rects_lng(vp_south, vp_north, rects, lng):
    res = []
    for r in rects:
        if r['west'] <= lng <= r['east']:
            s = max(vp_south, r['south'])
            n = min(vp_north, r['north'])
            if s < n:
                res.append((s, n))
    return res

def get_segs_inside_rects_lat(vp_west, vp_east, rects, lat):
    res = []
    for r in rects:
        if r['south'] <= lat <= r['north']:
            w = max(vp_west, r['west'])
            e = min(vp_east, r['east'])
            if w < e:
                res.append((w, e))
    return res
"""

api_grid_logic = """
@require_GET
def api_grid_section(request):
    try:
        south = float(request.GET.get('south'))
        west  = float(request.GET.get('west'))
        north = float(request.GET.get('north'))
        east  = float(request.GET.get('east'))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Khung bản đồ không hợp lệ.'}, status=400)

    # Giới hạn trong phạm vi HCM
    south = max(south, HCM_SOUTH)
    west  = max(west,  HCM_WEST)
    north = min(north, HCM_NORTH)
    east  = min(east,  HCM_EAST)

    if south >= north or west >= east:
        return JsonResponse({'success': False, 'error': 'Khung bản đồ nằm ngoài vùng.'}, status=400)

    features = []

    _ZONE_PARAMS = []
    vp_center_lat = (south + north) / 2
    for z in range(3):
        lat_sz = cell_lat_size(z)
        lng_sz = cell_lng_size(z, vp_center_lat)
        c_range = int((HCM_EAST - HCM_WEST) / lng_sz)
        r_range = int((HCM_NORTH - HCM_SOUTH) / lat_sz)
        _ZONE_PARAMS.append((c_range, r_range, lat_sz, lng_sz))

    for zone in range(3):
        col_range, row_range, lat_step, lng_step = _ZONE_PARAMS[zone]

        vp_south = south
        vp_north = north
        vp_west = west
        vp_east = east

        col_start = int(math.floor((vp_west  - GRID_ORIGIN_LNG) / lng_step))
        col_end   = int(math.ceil( (vp_east  - GRID_ORIGIN_LNG) / lng_step))
        row_start = int(math.floor((vp_south - GRID_ORIGIN_LAT) / lat_step))
        row_end   = int(math.ceil( (vp_north - GRID_ORIGIN_LAT) / lat_step))

        col_start = max(col_start, 0)
        col_end   = min(col_end,   col_range)
        row_start = max(row_start, 0)
        row_end   = min(row_end,   row_range)

        max_lines = 3000
        total_lines = (col_end - col_start + 1) + (row_end - row_start + 1)
        if total_lines > max_lines:
            continue

        for c in range(col_start, col_end + 1):
            lng = GRID_ORIGIN_LNG + c * lng_step
            if not (vp_west <= lng <= vp_east):
                continue
            
            segs = []
            if zone == 0:
                segs = get_segs_inside_rects_lng(vp_south, vp_north, URBAN_RECTS, lng)
            elif zone == 1:
                segs = get_segs_inside_rects_lng(vp_south, vp_north, SUBURBAN_RECTS, lng)
                segs = subtract_rect_lng(segs, URBAN_RECTS, lng)
            elif zone == 2:
                segs = [(vp_south, vp_north)]
                segs = subtract_rect_lng(segs, SUBURBAN_RECTS, lng)
                
            for seg_s, seg_n in segs:
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': [[lng, seg_s], [lng, seg_n]]},
                    'properties': {'zone': zone},
                })

        for r in range(row_start, row_end + 1):
            lat = GRID_ORIGIN_LAT + r * lat_step
            if not (vp_south <= lat <= vp_north):
                continue

            segs = []
            if zone == 0:
                segs = get_segs_inside_rects_lat(vp_west, vp_east, URBAN_RECTS, lat)
            elif zone == 1:
                segs = get_segs_inside_rects_lat(vp_west, vp_east, SUBURBAN_RECTS, lat)
                segs = subtract_rect_lat(segs, URBAN_RECTS, lat)
            elif zone == 2:
                segs = [(vp_west, vp_east)]
                segs = subtract_rect_lat(segs, SUBURBAN_RECTS, lat)
                
            for seg_w, seg_e in segs:
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': [[seg_w, lat], [seg_e, lat]]},
                    'properties': {'zone': zone},
                })

    return JsonResponse({'success': True, 'data': features})
"""

# Replace from URBAN_BOUNDS to cell_lng_size
pat1 = re.compile(r'# Nội thành: Quy Nhơn.*?def cell_lng_size.*?math.radians\(lat\)\)\)', re.DOTALL)
content = pat1.sub(new_logic, content)

# Replace from # ZONE_CLIP to api_grid_section definition
pat2 = re.compile(r'# ───────────────────────────────────────────────────────────────\n# Hộp bao địa lý cho từng zone.*?def api_grid_section', re.DOTALL)
content = pat2.sub(subtract_funcs + '\\n' + '@require_GET\\ndef api_grid_section', content)

# Replace api_grid_section body
pat3 = re.compile(r'@require_GET\ndef api_grid_section\(request\):.*?return JsonResponse\(\{[\'\"\s]+success[\'\"\s]+: True, [\'\"\s]+data[\'\"\s]+: features\}\)', re.DOTALL)
content = pat3.sub(api_grid_logic, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
