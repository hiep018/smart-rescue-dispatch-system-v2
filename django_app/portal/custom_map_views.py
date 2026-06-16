"""
custom_map_views.py
===================
Điều phối cứu hộ sử dụng thuật toán A* + OpenStreetMap (Leaflet.js).

Kiến trúc:
  - A* Node Graph   : Xây dựng đồ thị các trạm cứu hộ theo tọa độ thực
  - Heuristic       : Khoảng cách Haversine (đường chim bay) làm h(n)
  - g(n)            : Khoảng cách thực tế qua OSRM (đường ô tô)
  - f(n) = g(n) + h(n)
  - Kết quả         : Trả về tuyến đường GeoJSON + metadata điều phối

URLs cần khai báo trong urls.py (đã có sẵn):
  path("api/custom-map/data/",           api_custom_map_data,  name="api_custom_map_data")
  path("api/rescue/requests/<int>/dispatch/", api_custom_dispatch, name="api_dispatch_rescue")
"""

import heapq
import json
import math
import urllib.error
import urllib.parse
import urllib.request

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import RescueLog, RescueStation, VictimReport


# =====================================================
# CẤU HÌNH
# =====================================================

OSRM_BASE_URL = 'https://router.project-osrm.org'
AVG_SPEED_KMH  = 40   # Tốc độ trung bình xe cứu hộ (km/h)


# =====================================================
# THUẬT TOÁN A*
# =====================================================

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách đường chim bay (Haversine) giữa hai tọa độ.
    Đây là hàm heuristic h(n) của thuật toán A*.

    Đảm bảo tính admissible (h(n) <= h*(n)) vì đường chim bay
    luôn ngắn hơn hoặc bằng đường thực tế trên đường bộ.

    Trả về: khoảng cách tính bằng km (float)
    """
    R = 6371.0  # Bán kính Trái Đất (km)

    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_road_distance_km(lat1, lon1, lat2, lon2):
    """
    Gọi OSRM để lấy khoảng cách đường bộ thực tế giữa hai điểm.
    Đây là chi phí thực g(n) của thuật toán A*.

    Trả về: (distance_km, duration_minutes, geometry_geojson)
    Raise:  RuntimeError nếu OSRM không phản hồi hoặc lỗi
    """
    coords = f'{float(lon1)},{float(lat1)};{float(lon2)},{float(lat2)}'
    params = urllib.parse.urlencode({
        'overview': 'full',
        'geometries': 'geojson',
        'steps': 'false',
        'alternatives': 'false',
    })
    url = f'{OSRM_BASE_URL}/route/v1/driving/{coords}?{params}'

    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'RescueSystem-AStarRouter/1.0'}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'OSRM HTTP {e.code}') from e
    except urllib.error.URLError as e:
        raise RuntimeError('Không thể kết nối OSRM') from e
    except TimeoutError as e:
        raise RuntimeError('OSRM phản hồi quá chậm') from e

    if result.get('code') != 'Ok' or not result.get('routes'):
        raise RuntimeError(
            result.get('message', 'OSRM không tìm thấy tuyến đường')
        )

    route = result['routes'][0]
    distance_km = round(route['distance'] / 1000, 2)
    duration_min = max(1, round(route['duration'] / 60))
    geometry = route.get('geometry')

    return distance_km, duration_min, geometry


class AStarNode:
    """
    Một node trong đồ thị A*.

    Mỗi node đại diện cho một trạm cứu hộ.
    f(n) = g(n) + h(n)
      g(n) = chi phí đường bộ thực tế từ điểm xuất phát đến node này
      h(n) = heuristic Haversine từ node này đến đích (hiện trường)
    """

    __slots__ = ('station_id', 'g', 'h', 'f',
                 'distance_km', 'duration_min', 'geometry')

    def __init__(self, station_id, g, h, distance_km, duration_min, geometry):
        self.station_id  = station_id
        self.g           = g             # chi phí tích lũy (km)
        self.h           = h             # heuristic còn lại (km)
        self.f           = g + h         # tổng ước lượng
        self.distance_km = distance_km  # đường bộ thực tế
        self.duration_min = duration_min
        self.geometry    = geometry

    def __lt__(self, other):
        # Heap ưu tiên node có f nhỏ nhất; nếu bằng ưu tiên g nhỏ hơn
        if self.f == other.f:
            return self.g < other.g
        return self.f < other.f


def astar_find_best_station(victim_lat, victim_lon):
    """
    Thuật toán A* tìm trạm cứu hộ tối ưu.

    Mô hình hoá bài toán:
      - Trạng thái: vị trí hiện tại (trạm xuất phát)
      - Mục tiêu: đến hiện trường cứu hộ (victim_lat, victim_lon)
      - Đồ thị: mỗi trạm sẵn sàng là một node ứng viên
      - g(n): khoảng cách đường bộ từ trạm n đến hiện trường (OSRM)
      - h(n): Haversine từ trạm n đến hiện trường (admissible heuristic)
      - f(n) = g(n) + h(n)

    Chiến lược A*:
      1. Tính h(n) cho tất cả trạm → sắp xếp ưu tiên vào open set
      2. Pop node có f nhỏ nhất → gọi OSRM lấy g(n) thực
      3. Cập nhật f(n) → nếu đây là node tốt nhất đã expand → đó là đáp án
      4. Lặp cho đến khi hết node

    Tối ưu: Không gọi OSRM cho tất cả trạm cùng lúc — chỉ gọi
    theo thứ tự ưu tiên h(n), tiết kiệm API call đáng kể.

    Trả về:
      (best_node: AStarNode, best_station: RescueStation, errors: list)
      hoặc (None, None, errors) nếu không tìm thấy
    """

    stations = RescueStation.objects.filter(
        status='available',
        vehicle_count__gt=0
    ).order_by('station_code')

    if not stations:
        return None, None, []

    # --- Bước 1: Khởi tạo open set với h(n) ---
    # Mỗi phần tử: (h_estimate, station_id, station_object)
    open_heap = []
    station_map = {}

    for station in stations:
        h = haversine_km(
            station.latitude, station.longitude,
            victim_lat, victim_lon
        )
        heapq.heappush(open_heap, (h, station.id, station))
        station_map[station.id] = station

    best_node    = None
    visited      = set()
    errors       = []

    # --- Bước 2: Vòng lặp A* ---
    while open_heap:
        h_est, station_id, station = heapq.heappop(open_heap)

        if station_id in visited:
            continue
        visited.add(station_id)

        # Gọi OSRM để lấy g(n) thực tế
        try:
            dist_km, dur_min, geometry = get_road_distance_km(
                station.latitude, station.longitude,
                victim_lat, victim_lon
            )
        except RuntimeError as e:
            errors.append({
                'station_id': station.id,
                'station_name': station.name,
                'error': str(e),
            })
            continue

        # g(n) = khoảng cách thực tế đến hiện trường
        # h(n) = 0 vì đây là node đích (đã đến hiện trường)
        # → f(n) = g(n) + 0 = g(n)
        node = AStarNode(
            station_id=station_id,
            g=dist_km,
            h=0,  # đến đích rồi
            distance_km=dist_km,
            duration_min=dur_min,
            geometry=geometry,
        )

        # --- Bước 3: Cập nhật best ---
        if best_node is None:
            best_node = node
            best_station = station
        else:
            # So sánh f(n): thời gian ưu tiên hơn khoảng cách
            if dur_min < best_node.duration_min:
                best_node = node
                best_station = station
            elif (
                dur_min == best_node.duration_min
                and dist_km < best_node.distance_km
            ):
                best_node = node
                best_station = station

        # Tối ưu early stopping:
        # Nếu node tiếp theo trong heap có h_est > best g hiện tại,
        # không thể tìm được kết quả tốt hơn → dừng sớm
        if open_heap:
            next_h = open_heap[0][0]
            if next_h >= best_node.distance_km:
                break

    if best_node is None:
        return None, None, errors

    return best_node, best_station, errors


# =====================================================
# API: DỮ LIỆU BẢN ĐỒ (Leaflet.js)
# =====================================================

@require_http_methods(['GET'])
def api_custom_map_data(request):
    """
    Trả về dữ liệu cho bản đồ Leaflet.js:
    - Danh sách trạm cứu hộ (markers)
    - Danh sách yêu cầu cứu hộ đang hoạt động (markers)
    - Tuyến đường đang điều phối (GeoJSON polyline)

    Frontend dùng dữ liệu này để vẽ lên OpenStreetMap.
    """

    # --- Trạm cứu hộ ---
    stations = RescueStation.objects.all().order_by('station_code')
    station_data = []

    for s in stations:
        station_data.append({
            'id': s.id,
            'station_code': s.station_code,
            'name': s.name,
            'phone': s.phone,
            'address': s.address,
            'latitude': float(s.latitude),
            'longitude': float(s.longitude),
            'status': s.status,
            'status_display': s.get_status_display(),
            'vehicle_count': s.vehicle_count,
            'is_available': s.is_available,
        })

    # --- Yêu cầu cứu hộ đang hoạt động ---
    active_reports = (
        VictimReport.objects
        .select_related('assigned_station')
        .filter(status__in=['pending', 'assigned', 'on_the_way'])
        .order_by('-created_at')
    )
    report_data = []

    for r in active_reports:
        assigned = None
        if r.assigned_station:
            assigned = {
                'id': r.assigned_station.id,
                'name': r.assigned_station.name,
                'station_code': r.assigned_station.station_code,
            }

        # Lấy tuyến đường mới nhất nếu có
        latest_log = (
            r.rescue_logs
            .order_by('-assigned_at')
            .first()
        )
        route_geojson = None
        algorithm_used = None
        if latest_log:
            route_geojson  = latest_log.route_data
            algorithm_used = latest_log.algorithm

        report_data.append({
            'id': r.id,
            'victim_name': r.victim_name or 'Chưa xác định',
            'phone': r.phone,
            'address': r.address,
            'latitude': float(r.latitude),
            'longitude': float(r.longitude),
            'emergency_level': r.emergency_level,
            'emergency_level_display': r.get_emergency_level_display(),
            'status': r.status,
            'status_display': r.get_status_display(),
            'assigned_station': assigned,
            'route_geojson': route_geojson,
            'algorithm': algorithm_used,
            'created_at': r.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'data': {
            'stations': station_data,
            'active_reports': report_data,
        }
    })


# =====================================================
# API: ĐIỀU PHỐI A* + LƯU LOG
# =====================================================

@csrf_exempt
@require_http_methods(['POST'])
def api_custom_dispatch(request, report_id):
    """
    Điều phối cứu hộ cho một yêu cầu cụ thể bằng thuật toán A*.

    Quy trình:
      1. Lấy VictimReport theo report_id
      2. Chạy A* tìm trạm tối ưu
      3. Lưu RescueLog với thông tin tuyến đường
      4. Cập nhật trạng thái VictimReport + RescueStation
      5. Trả về dữ liệu điều phối (bao gồm GeoJSON cho Leaflet)

    Response format:
    {
      "success": true,
      "data": {
        "report_id": ...,
        "algorithm": "A*",
        "algorithm_detail": { "g": ..., "h": ..., "f": ... },
        "station": { ... },
        "victim": { ... },
        "distance_km": ...,
        "estimated_time_minutes": ...,
        "route_geojson": { GeoJSON geometry },
        "all_stations_considered": [ ... ],
        "errors": [ ... ]
      }
    }
    """

    report = get_object_or_404(
        VictimReport.objects.select_related('assigned_station'),
        id=report_id
    )

    # Không điều phối lại nếu đã hoàn thành / huỷ
    if report.status in ['completed', 'cancelled']:
        return JsonResponse({
            'success': False,
            'error': (
                f'Yêu cầu #{report_id} đã ở trạng thái '
                f'"{report.get_status_display()}", không thể điều phối lại.'
            )
        }, status=400)

    victim_lat = float(report.latitude)
    victim_lon = float(report.longitude)

    # --- Chạy A* ---
    best_node, best_station, errors = astar_find_best_station(
        victim_lat, victim_lon
    )

    if best_node is None or best_station is None:
        return JsonResponse({
            'success': False,
            'error': 'Không tìm thấy trạm cứu hộ sẵn sàng.',
            'errors': errors,
        }, status=503)

    # Tính h(n) thực — Haversine từ trạm đến hiện trường
    h_straight = haversine_km(
        best_station.latitude, best_station.longitude,
        victim_lat, victim_lon
    )

    algorithm_detail = {
        'g_road_km'     : round(best_node.distance_km, 3),
        'h_straight_km' : round(h_straight, 3),
        'f_total_km'    : round(best_node.distance_km + h_straight, 3),
        'description'   : (
            'g(n) = khoảng cách đường bộ thực tế (OSRM); '
            'h(n) = Haversine đường chim bay (admissible heuristic); '
            'f(n) = g(n) + h(n)'
        ),
    }

    # --- Lưu database ---
    with transaction.atomic():
        # Cập nhật report
        report.assigned_station = best_station
        report.status           = 'assigned'
        report.save()

        # Cập nhật trạng thái trạm
        from .auto_dispatch import sync_station_status
        sync_station_status(best_station)

        # Lưu RescueLog
        rescue_log = RescueLog.objects.create(
            report               = report,
            station              = best_station,
            route_distance_km    = best_node.distance_km,
            estimated_time_minutes = best_node.duration_min,
            route_data           = best_node.geometry,
            algorithm            = 'A*',
            status               = 'assigned',
            notes=(
                f'A* dispatch: g={best_node.distance_km}km, '
                f'h={round(h_straight, 2)}km, '
                f'f={round(best_node.distance_km + h_straight, 2)}km'
            ),
        )

    return JsonResponse({
        'success': True,
        'message': (
            f'Đã điều phối trạm {best_station.name} '
            f'đến hiện trường (A*, {best_node.distance_km} km, '
            f'~{best_node.duration_min} phút).'
        ),
        'data': {
            'report_id'  : report.id,
            'log_id'     : rescue_log.id,
            'algorithm'  : 'A*',
            'algorithm_detail': algorithm_detail,

            'station': {
                'id'           : best_station.id,
                'station_code' : best_station.station_code,
                'name'         : best_station.name,
                'phone'        : best_station.phone,
                'address'      : best_station.address,
                'latitude'     : float(best_station.latitude),
                'longitude'    : float(best_station.longitude),
            },

            'victim': {
                'name'      : report.victim_name or 'Chưa xác định',
                'phone'     : report.phone,
                'address'   : report.address,
                'latitude'  : victim_lat,
                'longitude' : victim_lon,
            },

            'distance_km'            : best_node.distance_km,
            'estimated_time_minutes' : best_node.duration_min,
            'route_geojson'          : best_node.geometry,
            'status'                 : report.status,
            'status_display'         : report.get_status_display(),
            'errors'                 : errors,
        }
    })