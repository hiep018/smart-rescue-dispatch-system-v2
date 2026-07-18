# Helper script to write what3words_views.py
import sys

filepath = 'd:/HTCH/smart-rescue-dispatch-system-v2/django_app/portal/what3words_views.py'

NEW_CONTENT = """import json
import math
import unicodedata
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Vùng hoạt động: Gia Lai + Bình Định
HCM_SOUTH = 12.8
HCM_WEST  = 107.3
HCM_NORTH = 14.8
HCM_EAST  = 109.5

# ZONE 0 — Nội thành (urban): 3m × 3m
URBAN_CELL_M = 3.0
# ZONE 1 — Vùng đệm (suburban): 6m × 6m
SUBURBAN_CELL_M = 6.0
# ZONE 2 — Ngoại ô / nông thôn (rural): 20m × 20m
RURAL_CELL_M = 20.0

# Danh sách 4 đô thị lõi (3x3m)
URBAN_RECTS = [
    {'south': 13.70, 'north': 13.85, 'west': 109.10, 'east': 109.30}, # Quy Nhơn
    {'south': 13.90, 'north': 14.05, 'west': 107.95, 'east': 108.10}, # Pleiku
    {'south': 13.82, 'north': 13.93, 'west': 109.02, 'east': 109.15}, # An Nhơn
    {'south': 14.35, 'north': 14.48, 'west': 108.95, 'east': 109.08}, # Hoài Nhơn
]

# Vùng đệm (6x6m): mở rộng xung quanh 4 đô thị lõi 0.05 độ
SUBURBAN_RECTS = []
for u in URBAN_RECTS:
    SUBURBAN_RECTS.append({
        'south': u['south'] - 0.05, 'north': u['north'] + 0.05,
        'west': u['west'] - 0.05, 'east': u['east'] + 0.05,
    })

def get_zone(latitude, longitude):
    for u in URBAN_RECTS:
        if u['south'] <= latitude <= u['north'] and u['west'] <= longitude <= u['east']:
            return 0
    for s in SUBURBAN_RECTS:
        if s['south'] <= latitude <= s['north'] and s['west'] <= longitude <= s['east']:
            return 1
    return 2

def cell_size_m(zone):
    if zone == 0: return URBAN_CELL_M
    elif zone == 1: return SUBURBAN_CELL_M
    else: return RURAL_CELL_M

def cell_lat_size(zone):
    return cell_size_m(zone) / 111111.0

def cell_lng_size(zone, lat=13.8):
    return cell_size_m(zone) / (111111.0 * math.cos(math.radians(lat)))

# 750 từ đơn giản, phổ biến, dễ đọc (ăn, ngủ, nghỉ, vui, vẻ,...)
VIETNAMESE_WORDS = [
    "an", "anh", "ao", "ba", "bà", "bác", "bạch", "bàn", "bán", "bánh", "bão", "bảo", "băng", "bằng", "bắp", "bắt", "bắc", "bến", "bếp", "biển", "biên", "biệt", "bình", "binh", "bò", "bó", "bọc", "bông", "bột", "bơ", "bờ", "bú", "bù", "búa", "bụi", "buồm", "buồn", "buồng", "bút", "bừa", "bữa", "bưởi", "bước", "bướm", "bạn", "bảng",
    "ca", "cà", "cá", "cả", "các", "cách", "cải", "cám", "cảm", "cạn", "cánh", "cạnh", "cáp", "cát", "cắt", "cầm", "cận", "cập", "cầu", "cấy", "cây", "còi", "cỏ", "cóc", "còi", "còng", "cọp", "cơ", "cờ", "cơm", "cú", "củ", "cục", "cúc", "cùng", "cuốc", "cuộn", "cường", "cưới", "cười", "cứu", "cực", "cửa",
    "da", "dạ", "dài", "dân", "dầu", "dây", "dế", "dễ", "dịch", "diều", "dừa", "dứa", "dương", "dưới", "dự", "đa", "đà", "đá", "đặc", "đầm", "đất", "đầu", "đậu", "đây", "đầy", "đăng", "đắt", "đắc", "đập", "đế", "để", "đền", "đêm", "đệm", "đẹp", "đi", "địa", "điểm", "điện", "điều", "đình", "đinh", "đỏ", "độ", "đốc", "đồi", "đổi", "đông", "đồng", "đống", "động", "đơn", "đủ", "đúng", "đuôi", "đường", "đứt",
    "em", "én", "eo", "ếch", "ga", "gà", "gạo", "gác", "gần", "gấp", "gật", "gấu", "gầy", "ghế", "ghi", "gỗ", "gốc", "gối", "gù", "gửi", "gương", "gạch", "giao",
    "hà", "há", "hạ", "hai", "hải", "hạn", "hạng", "hành", "hát", "hạt", "hằng", "hấp", "hầm", "hầu", "héo", "hè", "hẹn", "hẹp", "hết", "hiên", "hiệu", "hình", "hoa", "hòa", "hóa", "hỏa", "học", "hòm", "hòn", "hồng", "hông", "hột", "hơ", "hơi", "hơn", "hợp", "hũ", "hù", "hút", "hùng", "hướng", "hương", "hươu", "hưu",
    "kha", "khá", "khách", "khai", "khảo", "khăn", "khắp", "khấu", "khe", "khế", "khiêm", "khiên", "khiêng", "kho", "khó", "khóc", "khoai", "khoảng", "khoanh", "khóa", "khoa", "khỏe", "khói", "khôn", "không", "khớp", "khô", "khu", "khúc", "khung", "khuyên", "khuyết",
    "la", "là", "lá", "lạ", "lạc", "lai", "lam", "làm", "lan", "làn", "láng", "lãnh", "lạnh", "lát", "lăng", "lắp", "lâm", "lầm", "lập", "lầu", "lẩu", "lấy", "lên", "lịch", "liên", "liều", "lò", "lọ", "lòng", "lóng", "lọt", "lơ", "lờ", "lợi", "lợn", "lớp", "lũ", "lú", "lúa", "luộc", "luồn", "lưng", "lướt", "lưới", "lươn", "lượng", "lưu", "lực",
    "ma", "mà", "má", "mạ", "mác", "mạch", "mai", "mài", "mã", "màn", "máng", "mạnh", "mát", "mầm", "màu", "mẫu", "mây", "mấy", "mẹ", "miếng", "miền", "miệng", "mía", "mít", "mịn", "mỏ", "mọc", "mọi", "món", "mỏng", "móng", "mơ", "mờ", "mở", "mới", "mũ", "mù", "mụ", "mua", "múa", "múc", "mùi", "mũi", "muống", "muộn", "mướp", "mười", "mượn", "mương", "mưu", "mực",
    "na", "nà", "ná", "nạ", "nam", "năm", "nằm", "nắm", "nắng", "nặng", "nắp", "nấm", "nấu", "nếu", "nệm", "nếp", "nỉ", "ninh", "nóc", "nói", "nòng", "nóng", "nón", "nơ", "nở", "nơi", "nợ", "nụ", "nút", "nuôi", "nuốt", "nửa", "nước", "nướng", "nương", "nữ", "nực",
    "oanh", "oan", "ốc", "ôm", "ốm", "ông", "ống", "ơi", "ớt",
    "phà", "phá", "phải", "phản", "pháo", "pháp", "phát", "phạt", "phần", "phân", "phấn", "phật", "phế", "phê", "phép", "phí", "phía", "phiên", "phiếu", "phố", "phơi", "phù", "phủ", "phụ", "phun", "phút", "phương", "phức",
    "qua", "quà", "quá", "quạ", "quai", "quan", "quán", "quang", "quàng", "quảng", "quạt", "quân", "quần", "quận", "quất", "quầy", "que", "quốc", "quý", "quỳ", "quýt", "quyết", "quyền",
    "ra", "rà", "rá", "rác", "rạch", "rải", "rầm", "rậm", "răng", "rằng", "rắc", "râm", "rập", "rất", "râu", "rây", "rẻ", "rẽ", "rèm", "rèn", "rết", "rễ", "rỉ", "riêng", "rổ", "rõ", "rơ", "rờ", "rời", "rơm", "rỡ", "rùa", "ruột", "rừng", "rượu", "rực",
    "sa", "sà", "sả", "sạch", "sai", "sải", "săm", "sắm", "săn", "sắt", "sắc", "sâm", "sầm", "sập", "sân", "sầu", "sấy", "sẻ", "sét", "sên", "sếp", "sĩ", "sỉ", "sữa", "sườn", "sương", "sưu", "sức",
    "ta", "tà", "tá", "tạ", "tác", "tai", "tài", "tại", "tam", "tám", "tạm", "tan", "tàn", "tán", "tảo", "táp", "tát", "tắm", "tăng", "tặng", "tắt", "tắc", "tâm", "tầm", "tấm", "tập", "tây", "tẩy", "tê", "tệ", "tên", "tết", "ti", "tí", "tỉ", "tị", "tích", "tiệc", "tiêm", "tiền", "tiến", "tiện", "tiếp", "tiết", "tiêu", "tiểu", "tim", "tìm", "tím", "tình", "tỉnh", "tỏ", "tổ", "tóc", "tỏi", "tóm", "tòng", "tơ", "tờ", "tới", "tú", "tủ", "tua", "túc", "túi", "tuần", "tuốt", "tương", "tướng", "tuyển", "tuyệt", "từ", "tự", "tước", "tươi", "tưới", "tượng", "tử",
    "va", "và", "vá", "vạ", "vác", "vạch", "vai", "vài", "vải", "vạn", "vàng", "vào", "văn", "vắng", "vắt", "vắc", "vân", "vần", "vấn", "vận", "vật", "vây", "vấp", "vẽ", "vè", "vẻ", "về", "vệ", "vết", "vị", "ví", "vỉ", "vịt", "viên", "viết", "việc", "vỗ", "vỏ", "võ", "vôi", "vòng", "vơ", "vờ", "với", "vỡ", "vợ", "vớt", "vú", "vụ", "vua", "vực", "vườn", "vượt", "vượn",
    "xa", "xà", "xá", "xác", "xách", "xanh", "xào", "xăng", "xắp", "xắt", "xâm", "xây", "xe", "xẻ", "xem", "xếp", "xích", "xiên", "xòe", "xôi", "xong", "xơ", "xờ", "xú", "xù", "xúc", "xuống", "xương", "xưởng", "xử", "yên", "yếu", "yêu", "yếm",
    # Thêm các từ phổ biến khác
    "thanh", "bình", "tâm", "an", "nhàn", "phúc", "lộc", "thọ", "tài", "đức", "nhân", "trí", "tín", "nghĩa", "trung", "hiếu", "hòa", "thuận", "phát", "đạt", "thành", "công", "vinh", "quang", "sáng", "lạn", "hùng", "cường", "kiên", "trì", "nhẫn", "nại", "cố", "gắng", "nỗ", "lực", "quyết", "tâm", "dũng", "cảm", "can", "đảm", "anh", "dũng", "chiến", "thắng", "vượt", "qua", "gian", "khó", "thử", "thách", "chinh", "phục", "đỉnh", "cao", "ước", "mơ", "hoài", "bão", "khát", "vọng", "tương", "lai", "tươi", "sáng", "rạng", "rỡ", "niềm", "tin", "hy", "vọng", "lạc", "quan", "yêu", "đời", "vui", "vẻ", "hạnh", "phúc", "ấm", "no", "sung", "túc", "giàu", "sang", "phú", "quý", "thịnh", "vượng", "phồn", "vinh", "an", "khang", "thái", "bình", "yên", "ấm", "thanh", "thản", "nhẹ", "nhàng", "thư", "thái", "bình", "yên", "tĩnh", "lặng", "sâu", "lắng", "dạt", "dào", "mênh", "mông", "bao", "la", "bát", "ngát", "rộng", "lớn", "vĩ", "đại", "cao", "cả", "thiêng", "liêng", "trân", "trọng", "kính", "mến", "yêu", "thương", "quý", "mến", "tôn", "trọng", "ngưỡng", "mộ", "khâm", "phục", "tự", "hào", "hãnh", "diện", "kiêu", "hãnh", "tự", "tin", "bản", "lĩnh", "vững", "vàng", "chắc", "chắn", "kiên", "định", "quả", "quyết", "mạnh", "mẽ", "cứng", "cáp", "khỏe", "mạnh", "tráng", "kiện", "dẻo", "dai", "bền", "bỉ"
]

VIETNAMESE_WORDS = list(dict.fromkeys(VIETNAMESE_WORDS))
WORD_COUNT = len(VIETNAMESE_WORDS)

# TIGHT PACKING GRID BLOCKS
GRID_BLOCKS = []
_current_offset = 0

def add_blocks(zone, rects):
    global _current_offset
    lat_sz = cell_lat_size(zone)
    lng_sz = cell_lng_size(zone)
    for r in rects:
        rows = int(math.ceil((r['north'] - r['south']) / lat_sz))
        cols = int(math.ceil((r['east'] - r['west']) / lng_sz))
        GRID_BLOCKS.append({
            'zone': zone, 'rect': r, 'offset': _current_offset,
            'cols': cols, 'rows': rows, 'lat_sz': lat_sz, 'lng_sz': lng_sz
        })
        _current_offset += rows * cols

add_blocks(0, URBAN_RECTS)
add_blocks(1, SUBURBAN_RECTS)
add_blocks(2, [{'south': HCM_SOUTH, 'north': HCM_NORTH, 'west': HCM_WEST, 'east': HCM_EAST}])
TOTAL_CELLS = _current_offset

def coords_to_cell_id(lat, lng):
    zone = get_zone(lat, lng)
    for b in GRID_BLOCKS:
        if b['zone'] == zone and b['rect']['south'] <= lat <= b['rect']['north'] and b['rect']['west'] <= lng <= b['rect']['east']:
            row = int((lat - b['rect']['south']) / b['lat_sz'])
            col = int((lng - b['rect']['west']) / b['lng_sz'])
            row = max(0, min(row, b['rows'] - 1))
            col = max(0, min(col, b['cols'] - 1))
            return b['offset'] + row * b['cols'] + col
    return None

def cell_id_to_coords(cell_id):
    cell_id = cell_id % TOTAL_CELLS
    for b in GRID_BLOCKS:
        if b['offset'] <= cell_id < b['offset'] + b['rows'] * b['cols']:
            local_id = cell_id - b['offset']
            row = local_id // b['cols']
            col = local_id % b['cols']
            south = b['rect']['south'] + row * b['lat_sz']
            west = b['rect']['west'] + col * b['lng_sz']
            return b['zone'], row, col, south, west
    return None

def cell_id_to_words(cell_id):
    if cell_id is None or cell_id < 0: return "###"
    cell_id = cell_id % TOTAL_CELLS
    w3 = cell_id % WORD_COUNT
    cell_id //= WORD_COUNT
    w2 = cell_id % WORD_COUNT
    cell_id //= WORD_COUNT
    w1 = cell_id % WORD_COUNT
    return f"{VIETNAMESE_WORDS[w1]}.{VIETNAMESE_WORDS[w2]}.{VIETNAMESE_WORDS[w3]}"

def words_to_cell_id(words):
    words = words.strip().lower().removeprefix('#').removeprefix('///')
    parts = words.split('.')
    if len(parts) != 3: return -1
    try:
        i1 = VIETNAMESE_WORDS.index(parts[0])
        i2 = VIETNAMESE_WORDS.index(parts[1])
        i3 = VIETNAMESE_WORDS.index(parts[2])
        return (i1 * WORD_COUNT * WORD_COUNT) + (i2 * WORD_COUNT) + i3
    except ValueError:
        return -1

def coords_to_3wa(lat, lng):
    return coords_to_cell_id(lat, lng)

# Helper line subtraction
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

@require_GET
def api_coordinates_to_3wa(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Tọa độ không hợp lệ.'}, status=400)

    cell_id = coords_to_3wa(lat, lng)
    if cell_id is None:
        return JsonResponse({'success': False, 'error': 'Tọa độ ngoài phạm vi hoạt động.'}, status=400)

    words = cell_id_to_words(cell_id)
    ret = cell_id_to_coords(cell_id)
    if not ret:
        return JsonResponse({'success': False, 'error': 'Không thể ánh xạ cell.'}, status=400)
    
    zone, row, col, south, west = ret
    lat_sz = cell_lat_size(zone)
    lng_sz = cell_lng_size(zone)
    north = south + lat_sz
    east = west + lng_sz

    return JsonResponse({
        'success': True,
        'data': {
            'words': words,
            'zone': ['urban', 'suburban', 'rural'][zone],
            'cell_size_m': [URBAN_CELL_M, SUBURBAN_CELL_M, RURAL_CELL_M][zone],
            'coordinates': {'lat': lat, 'lng': lng},
            'square': {
                'southwest': {'lat': south, 'lng': west},
                'northeast': {'lat': north, 'lng': east}
            },
            'language': 'vi'
        }
    })

@require_GET
def api_3wa_to_coordinates(request):
    words = request.GET.get('words', '').strip().lower()
    cell_id = words_to_cell_id(words)
    if cell_id < 0:
        return JsonResponse({'success': False, 'error': 'Cụm từ này không tồn tại hoặc sai định dạng.'}, status=400)

    ret = cell_id_to_coords(cell_id)
    if not ret:
        return JsonResponse({'success': False, 'error': 'Tọa độ nằm ngoài phạm vi.'}, status=400)

    zone, row, col, south, west = ret
    lat_sz = cell_lat_size(zone)
    lng_sz = cell_lng_size(zone)
    north = south + lat_sz
    east = west + lng_sz
    center_lat = (south + north) / 2
    center_lng = (west + east) / 2

    return JsonResponse({
        'success': True,
        'data': {
            'words': words,
            'zone': ['urban', 'suburban', 'rural'][zone],
            'cell_size_m': [URBAN_CELL_M, SUBURBAN_CELL_M, RURAL_CELL_M][zone],
            'coordinates': {'lat': center_lat, 'lng': center_lng},
            'square': {
                'southwest': {'lat': south, 'lng': west},
                'northeast': {'lat': north, 'lng': east}
            },
            'language': 'vi'
        }
    })

@require_GET
def api_grid_section(request):
    try:
        south = float(request.GET.get('south'))
        west  = float(request.GET.get('west'))
        north = float(request.GET.get('north'))
        east  = float(request.GET.get('east'))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Khung bản đồ không hợp lệ.'}, status=400)

    south = max(south, HCM_SOUTH)
    west  = max(west,  HCM_WEST)
    north = min(north, HCM_NORTH)
    east  = min(east,  HCM_EAST)

    if south >= north or west >= east:
        return JsonResponse({'success': False, 'error': 'Khung bản đồ nằm ngoài vùng.'}, status=400)

    features = []
    _ZONE_PARAMS = []
    for z in range(3):
        lat_sz = cell_lat_size(z)
        lng_sz = cell_lng_size(z)
        c_range = int((HCM_EAST - HCM_WEST) / lng_sz)
        r_range = int((HCM_NORTH - HCM_SOUTH) / lat_sz)
        _ZONE_PARAMS.append((c_range, r_range, lat_sz, lng_sz))

    for zone in range(3):
        col_range, row_range, lat_step, lng_step = _ZONE_PARAMS[zone]
        
        # Để lấy origin ảo cho grid drawing
        GRID_ORIGIN_LAT = HCM_SOUTH
        GRID_ORIGIN_LNG = HCM_WEST

        col_start = int(math.floor((west  - GRID_ORIGIN_LNG) / lng_step))
        col_end   = int(math.ceil( (east  - GRID_ORIGIN_LNG) / lng_step))
        row_start = int(math.floor((south - GRID_ORIGIN_LAT) / lat_step))
        row_end   = int(math.ceil( (north - GRID_ORIGIN_LAT) / lat_step))

        max_lines = 3000
        if (col_end - col_start + 1) + (row_end - row_start + 1) > max_lines:
            continue

        for c in range(col_start, col_end + 1):
            lng = GRID_ORIGIN_LNG + c * lng_step
            if not (west <= lng <= east): continue
            
            segs = []
            if zone == 0:
                segs = get_segs_inside_rects_lng(south, north, URBAN_RECTS, lng)
            elif zone == 1:
                segs = get_segs_inside_rects_lng(south, north, SUBURBAN_RECTS, lng)
                segs = subtract_rect_lng(segs, URBAN_RECTS, lng)
            elif zone == 2:
                segs = [(south, north)]
                segs = subtract_rect_lng(segs, SUBURBAN_RECTS, lng)
                
            for seg_s, seg_n in segs:
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': [[lng, seg_s], [lng, seg_n]]},
                    'properties': {'zone': zone},
                })

        for r in range(row_start, row_end + 1):
            lat = GRID_ORIGIN_LAT + r * lat_step
            if not (south <= lat <= north): continue

            segs = []
            if zone == 0:
                segs = get_segs_inside_rects_lat(west, east, URBAN_RECTS, lat)
            elif zone == 1:
                segs = get_segs_inside_rects_lat(west, east, SUBURBAN_RECTS, lat)
                segs = subtract_rect_lat(segs, URBAN_RECTS, lat)
            elif zone == 2:
                segs = [(west, east)]
                segs = subtract_rect_lat(segs, SUBURBAN_RECTS, lat)
                
            for seg_w, seg_e in segs:
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'LineString', 'coordinates': [[seg_w, lat], [seg_e, lat]]},
                    'properties': {'zone': zone},
                })

    return JsonResponse({
        'success': True,
        'data': {
            'type': 'FeatureCollection',
            'features': features,
        }
    })
"""

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(NEW_CONTENT)

print("Updated successfully")
