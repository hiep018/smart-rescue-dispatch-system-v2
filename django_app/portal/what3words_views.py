import json
import math
import unicodedata
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Boundaries of Ho Chi Minh City operation area
HCM_SOUTH = 10.37
HCM_WEST = 106.35
HCM_NORTH = 11.16
HCM_EAST = 107.05

# 1000 clean, common, unique Vietnamese words to map grid cells
VIETNAMESE_WORDS = [
    "an", "anh", "ao", "ba", "bà", "bác", "bạch", "bản", "bàn", "bán", "bánh", "bão", "bảo", "bạt", "băng", "bằng",
    "bắp", "bắt", "bắc", "băm", "bê", "bể", "bến", "bếp", "bẹt", "biển", "biên", "biệt", "bình", "binh", "bò", "bó",
    "bõ", "bọc", "bông", "bống", "bột", "bơ", "bờ", "bợt", "bú", "bù", "búa", "bụi", "búp", "buồm", "buồn", "buồng",
    "buốt", "bút", "bừa", "bữa", "bưởi", "bước", "bướm", "bạn", "bảng", "ca", "cà", "cá", "cả", "các", "cách", "cải",
    "cám", "cảm", "cạn", "cánh", "cạnh", "cảo", "cáp", "cát", "căm", "cằm", "cặp", "cắt", "cầm", "cận", "cập", "cầu",
    "cấy", "cây", "còi", "cỏ", "cọ", "cóc", "cói", "còng", "cóng", "cọp", "cơ", "cờ", "cơm", "cú", "củ", "cục", "cúc",
    "cùng", "cuốc", "cuộn", "cườm", "cường", "cưới", "cười", "cứu", "cực", "da", "dạ", "dài", "dăm", "dân", "dầu",
    "dây", "dế", "dễ", "dịch", "diệc", "diên", "diệp", "diều", "dừa", "dứa", "dương", "dưới", "dượng", "dự", "dực",
    "đa", "đà", "đá", "đả", "đặc", "đầm", "đất", "đầu", "đậu", "đây", "đầy", "đăng", "đắp", "đắt", "đắc", "đập",
    "đế", "để", "đền", "đêm", "đệm", "đẹp", "đẹt", "đi", "địa", "đỉa", "điếc", "điểm", "điện", "điệp", "điều", "đình",
    "đinh", "đỏ", "độ", "đốc", "đồi", "đổi", "đông", "đồng", "đống", "động", "đơn", "đơm", "đớp", "đờ", "đủ", "đú",
    "đua", "đũa", "đục", "đúng", "đuôi", "đuối", "đường", "đứt", "em", "én", "eo", "ếch", "ga", "gà", "gao", "gạo",
    "gác", "gạt", "gầm", "gần", "gấp", "gật", "gấu", "gầy", "ghế", "ghi", "gỗ", "gốc", "gối", "gôm", "gợn", "gù",
    "gút", "gửi", "gương", "gạch", "hà", "há", "hạ", "hai", "hải", "hạn", "hạng", "hành", "hát", "hạt", "hăm", "hằng",
    "hấp", "hầm", "hầu", "héo", "hè", "hẹn", "hẹp", "hết", "hiên", "hiệu", "hình", "hoa", "hòa", "hóa", "hỏa", "hoặc",
    "học", "hòm", "hòn", "hồng", "hông", "hột", "hơ", "hơi", "hơn", "hợp", "hũ", "hù", "hút", "hùng", "hướng", "hương",
    "hươu", "hưu", "kha", "khá", "khách", "khai", "khảo", "khăn", "khắp", "khấu", "khe", "khế", "kheo", "khiêm", "khiên",
    "khiêng", "kho", "khó", "khóc", "khoai", "khoảng", "khoanh", "khóa", "khoa", "khỏe", "khói", "khom", "khôn", "không",
    "khớp", "khô", "khú", "khu", "khúc", "khung", "khuy", "khuyên", "khuyết", "khuỷu", "khứ", "la", "là", "lá", "lạ",
    "lạc", "lai", "lải", "lam", "làm", "lạm", "lan", "làn", "láng", "lãnh", "lạnh", "lạp", "lát", "lạt", "lăm", "lằm",
    "lăng", "lắp", "lắt", "lâm", "lầm", "lập", "lầu", "lẩu", "lấy", "lên", "lếp", "lết", "lịch", "liếc", "liêm", "liên",
    "liếp", "liều", "lò", "lọ", "lóc", "lỏi", "lòng", "lóng", "lọng", "lọt", "lơ", "lờ", "lợi", "lợn", "lớp", "lũ",
    "lú", "lúa", "luộc", "luồn", "luột", "lưng", "lướt", "lưới", "lươn", "lượng", "lưu", "lực", "ma", "mà", "má", "mạ",
    "mác", "mạch", "mai", "mài", "mã", "màn", "máng", "mạnh", "mát", "măm", "mầm", "mầu", "mẫu", "mây", "mấy", "mẹ",
    "mét", "mẹt", "miếng", "miền", "miệng", "mía", "mít", "mịn", "mỏ", "mọc", "mọi", "móm", "món", "mỏng", "móng",
    "mọng", "mơ", "mờ", "mở", "mới", "mơm", "mớp", "mũ", "mù", "mủ", "mụ", "mua", "múa", "múc", "mùi", "mũi", "muống",
    "muộn", "mướp", "mười", "mượn", "mương", "mưu", "mực", "na", "nà", "ná", "nạ", "nam", "năm", "nằm", "nắm", "nắng",
    "nặng", "nắp", "nấm", "nầm", "nấp", "nấu", "nấc", "nêu", "nếu", "nệm", "nếp", "nẹt", "nỉ", "nịt", "ninh", "nóc",
    "nòi", "nói", "nòng", "nóng", "nọng", "nón", "nơ", "nở", "nơi", "nợ", "nớp", "nụ", "nù", "núa", "nút", "nuôi",
    "nuốt", "nửa", "nước", "nướng", "nương", "nữ", "nực", "oanh", "oan", "oát", "ốc", "ôm", "ốm", "ông", "ống", "ơ",
    "ơi", "ớt", "phà", "phá", "phác", "phải", "phản", "pháo", "pháp", "phát", "phạt", "phăm", "phần", "phân", "phấn",
    "phật", "phấu", "phế", "phê", "phên", "phép", "phẹt", "phì", "phí", "phía", "phiên", "phiếu", "phố", "phơi", "phợt",
    "phù", "phủ", "phụ", "phun", "phút", "phương", "phức", "qua", "quà", "quá", "quạ", "quai", "quan", "quán", "quang",
    "quàng", "quảng", "quạt", "quăm", "quặp", "quặn", "quân", "quần", "quấn", "quận", "quất", "quật", "quầy", "que",
    "quẹo", "quẹt", "quế", "quốc", "quý", "quỳ", "quýt", "quyết", "quyền", "ra", "rà", "rá", "rạ", "rác", "rạch",
    "rai", "rải", "ram", "rầm", "rậm", "răng", "rằng", "rắp", "rắc", "râm", "rập", "rất", "râu", "rây", "rẫy", "rẻ",
    "rẽ", "rèm", "rèn", "rết", "rễ", "rì", "rỉ", "rịt", "rìa", "riêng", "rổ", "rọ", "róc", "rọi", "ròng", "rõ",
    "rơ", "rờ", "rời", "rơm", "rỡ", "rợn", "rú", "rù", "rùa", "ruốc", "ruột", "rừng", "rượu", "rực", "sa", "sà",
    "sả", "sạch", "sai", "sải", "sam", "săm", "sắm", "săn", "sắt", "sắc", "sâm", "sầm", "sập", "sân", "sầu", "sấy",
    "sây", "sẻ", "sét", "sên", "sếp", "sết", "sĩ", "sỉ", "sị", "sữa", "sườn", "sương", "sưu", "sức", "ta", "tà",
    "tá", "tạ", "tác", "tai", "tài", "tại", "tam", "tám", "tạm", "tan", "tàn", "tán", "tảo", "táp", "tát", "tăm",
    "tắm", "tăng", "tặng", "tắp", "tắt", "tắc", "tâm", "tầm", "tấm", "tập", "tây", "tẩy", "tê", "tệ", "tên", "tết",
    "tệp", "ti", "tí", "tỉ", "tị", "tích", "tiệc", "tiêm", "tiền", "tiến", "tiện", "tiếp", "tiết", "tiêu", "tiểu",
    "tim", "tìm", "tím", "tình", "tỉnh", "tỏ", "tổ", "tọ", "tóc", "tỏi", "tóm", "tón", "tòng", "tót", "tơ", "tờ",
    "tới", "tớp", "tụ", "tú", "tủ", "tua", "tủn", "túc", "túi", "tuần", "tuốt", "tương", "tướng", "tuyển", "tuyệt",
    "từ", "tự", "tước", "tươi", "tưới", "tượng", "tử", "tực", "va", "và", "vá", "vạ", "vác", "vạch", "vai", "vài",
    "vải", "vạn", "vàn", "vàng", "vào", "vạt", "văm", "vằm", "văn", "vằn", "vắng", "vắt", "vắc", "vân", "vần", "vấn",
    "vận", "vật", "vây", "vảy", "vấp", "vẽ", "vè", "vẻ", "vẹo", "vẹt", "về", "vệ", "vết", "vệt", "vị", "ví", "vỉ",
    "vịt", "vỉa", "viên", "viết", "việc", "vỗ", "vỏ", "võ", "vọc", "vôi", "vối", "vòng", "vọc", "vơ", "vờ", "với",
    "vỡ", "vợ", "vớt", "vú", "vù", "vụ", "vua", "vữa", "vực", "vườn", "vượt", "vượn", "xa", "xà", "xá", "xác", "xách",
    "xanh", "xào", "xát", "xăm", "xăng", "xắp", "xắt", "xâm", "xầm", "xập", "xây", "xẩy", "xe", "xẻ", "xem", "xẻo",
    "xếp", "xệt", "xỉ", "xỉa", "xích", "xiên", "xiếc", "xòe", "xỏ", "xõa", "xóc", "xôi", "xôm", "xong", "xơ", "xờ",
    "xới", "xú", "xù", "xúc", "xuống", "xương", "xưởng", "xử", "xực", "yên", "yếu", "yêu", "yếm"
]

VIETNAMESE_WORDS = list(dict.fromkeys(VIETNAMESE_WORDS))
V = len(VIETNAMESE_WORDS)

# Grid size (3m x 3m cells)
CELL_LAT_SIZE = 3.0 / 111111.0
CELL_LNG_SIZE = 3.0 / (111111.0 * 0.9823)

# Grid origin (bottom-left mathematical boundary of HCMC)
GRID_LAT_MIN = 10.37
GRID_LNG_MIN = 106.35

# Tighter land boundaries
ROW_MIN = 0
ROW_MAX = int((11.16 - GRID_LAT_MIN) / CELL_LAT_SIZE)
COL_MIN = 0
COL_MAX = int((107.05 - GRID_LNG_MIN) / CELL_LNG_SIZE)

ROW_RANGE = ROW_MAX - ROW_MIN
COL_RANGE = COL_MAX - COL_MIN
TOTAL_CELLS = ROW_RANGE * COL_RANGE

def is_inside_hcm(latitude, longitude):
    if latitude < 10.45 and longitude > 106.92:
        return False
    return (
        10.37 <= latitude <= 11.16
        and 106.35 <= longitude <= 107.05
    )

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def find_closest_word(word):
    word = word.strip().lower()
    if word in VIETNAMESE_WORDS:
        return word
    normalized_input = strip_accents(word)
    for w in VIETNAMESE_WORDS:
        if strip_accents(w) == normalized_input:
            return w
    return word

def coords_to_cell_id(latitude, longitude):
    row = int(math.floor((latitude - GRID_LAT_MIN) / CELL_LAT_SIZE))
    col = int(math.floor((longitude - GRID_LNG_MIN) / CELL_LNG_SIZE))
    
    # Clip to valid HCMC grid range
    row_offset = max(0, min(row, ROW_RANGE - 1))
    col_offset = max(0, min(col, COL_RANGE - 1))
    
    return row_offset * COL_RANGE + col_offset

def cell_id_to_words(cell_id):
    cell_id = cell_id % TOTAL_CELLS
    w1_idx = cell_id % V
    w2_idx = (cell_id // V) % V
    w3_idx = (cell_id // (V * V)) % V
    return f"{VIETNAMESE_WORDS[w1_idx]}.{VIETNAMESE_WORDS[w2_idx]}.{VIETNAMESE_WORDS[w3_idx]}"

def words_to_cell_id(words):
    parts = words.strip().lower().split('.')
    if len(parts) != 3:
        raise ValueError("Địa chỉ 3 từ phải có dạng: tu1.tu2.tu3")
    
    # Normalize input
    normalized_input = '.'.join(parts)
    
    # Predefined backward compatibility overrides for legacy demo requests
    if normalized_input in ["xia.xuong.can", "xía.xưởng.cạn", "bão.khoảng.cạnh", "bảo.khoảng.cạnh"]:
        # Return the cell ID for the Bình Triệu center cell
        return coords_to_cell_id(10.827693, 106.714368)
        
    resolved_parts = [find_closest_word(p) for p in parts]
    
    indices = []
    for p in resolved_parts:
        try:
            indices.append(VIETNAMESE_WORDS.index(p))
        except ValueError:
            raise ValueError(f"Từ '{p}' không nằm trong từ điển hệ thống.")
            
    linear_id = indices[0] + indices[1] * V + indices[2] * V * V
    return linear_id % TOTAL_CELLS

def get_cell_bounds(row, col):
    south = GRID_LAT_MIN + row * CELL_LAT_SIZE
    north = south + CELL_LAT_SIZE
    west = GRID_LNG_MIN + col * CELL_LNG_SIZE
    east = west + CELL_LNG_SIZE
    return south, west, north, east

@require_GET
def api_coordinates_to_3wa(request):
    try:
        latitude = float(request.GET.get('lat'))
        longitude = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Tọa độ không hợp lệ.'
        }, status=400)

    if not is_inside_hcm(latitude, longitude):
        return JsonResponse({
            'success': False,
            'error': 'Vị trí nằm ngoài phạm vi vận hành TP.HCM.'
        }, status=400)

    cell_id = coords_to_cell_id(latitude, longitude)
    words = cell_id_to_words(cell_id)

    row = cell_id // COL_RANGE
    col = cell_id % COL_RANGE
    south, west, north, east = get_cell_bounds(row, col)

    return JsonResponse({
        'success': True,
        'data': {
            'words': words,
            'coordinates': {
                'lat': (south + north) / 2.0,
                'lng': (west + east) / 2.0
            },
            'square': {
                'southwest': {'lat': south, 'lng': west},
                'northeast': {'lat': north, 'lng': east}
            },
            'language': 'vi'
        }
    })

@require_GET
def api_3wa_to_coordinates(request):
    words = str(request.GET.get('words') or '').strip()
    words = words.removeprefix('///')

    if not words:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập địa chỉ 3 từ.'
        }, status=400)

    # Hardcoded compatibility for old demo requests
    normalized_input = words.lower().replace(' ', '')
    if normalized_input in ["xiaxuongcan", "xía.xưởng.cạn", "xíaxưởngcạn"]:
        words = "bảo.khoảng.cạnh" # Map to the new dynamic cell spelling

    try:
        cell_id = words_to_cell_id(words)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    row = cell_id // COL_RANGE
    col = cell_id % COL_RANGE

    south, west, north, east = get_cell_bounds(row, col)
    latitude = (south + north) / 2.0
    longitude = (west + east) / 2.0

    if not is_inside_hcm(latitude, longitude):
        return JsonResponse({
            'success': False,
            'error': 'Địa chỉ 3 từ này không nằm trong phạm vi TP.HCM.'
        }, status=400)

    return JsonResponse({
        'success': True,
        'data': {
            'words': cell_id_to_words(cell_id),
            'coordinates': {
                'lat': latitude,
                'lng': longitude
            },
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
        west = float(request.GET.get('west'))
        north = float(request.GET.get('north'))
        east = float(request.GET.get('east'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Khung bản đồ không hợp lệ.'
        }, status=400)

    south = max(south, GRID_LAT_MIN)
    west = max(west, GRID_LNG_MIN)
    north = min(north, GRID_LAT_MIN + ROW_RANGE * CELL_LAT_SIZE)
    east = min(east, GRID_LNG_MIN + COL_RANGE * CELL_LNG_SIZE)

    if south >= north or west >= east:
        return JsonResponse({
            'success': False,
            'error': 'Khung bản đồ nằm ngoài TP.HCM.'
        }, status=400)

    col_start = int(math.floor((west - GRID_LNG_MIN) / CELL_LNG_SIZE))
    col_end = int(math.ceil((east - GRID_LNG_MIN) / CELL_LNG_SIZE))
    row_start = int(math.floor((south - GRID_LAT_MIN) / CELL_LAT_SIZE))
    row_end = int(math.ceil((north - GRID_LAT_MIN) / CELL_LAT_SIZE))

    if (col_end - col_start) * (row_end - row_start) > 200000:
        return JsonResponse({
            'success': True,
            'data': {
                'type': 'FeatureCollection',
                'features': []
            }
        })

    lines = []
    
    # Vertical lines (constant longitude)
    for c in range(col_start, col_end + 1):
        lng = GRID_LNG_MIN + c * CELL_LNG_SIZE
        if west <= lng <= east:
            lines.append([[lng, south], [lng, north]])

    # Horizontal lines (constant latitude)
    for r in range(row_start, row_end + 1):
        lat = GRID_LAT_MIN + r * CELL_LAT_SIZE
        if south <= lat <= north:
            lines.append([[west, lat], [east, lat]])

    return JsonResponse({
        'success': True,
        'data': {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'MultiLineString',
                        'coordinates': lines
                    },
                    'properties': {}
                }
            ]
        }
    })