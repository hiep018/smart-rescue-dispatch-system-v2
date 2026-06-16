import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import transaction
from django.db.models import (
    Case,
    IntegerField,
    Value,
    When,
)

# auto_dispatch.py nằm cùng thư mục với models.py
from .models import (
    RescueLog,
    RescueStation,
    VictimReport,
)


# Những trạng thái đang chiếm một phương tiện của trạm
ACTIVE_REPORT_STATUSES = (
    'assigned',
    'on_the_way',
)


# =====================================================
# KHẢ NĂNG TIẾP NHẬN CỦA TRẠM
# =====================================================

def get_station_capacity(station):
    """
    Tính số xe của trạm:

    - vehicle_count: tổng số xe
    - active_count: số xe đang làm nhiệm vụ
    - available_vehicles: số xe còn trống
    """

    active_count = VictimReport.objects.filter(
        assigned_station=station,
        status__in=ACTIVE_REPORT_STATUSES,
    ).count()

    vehicle_count = max(
        int(station.vehicle_count or 0),
        0,
    )

    available_vehicles = max(
        vehicle_count - active_count,
        0,
    )

    return {
        'vehicle_count': vehicle_count,
        'active_count': active_count,
        'available_vehicles': available_vehicles,
    }


def sync_station_status(station):
    """
    Đồng bộ trạng thái trạm theo số xe còn trống.

    Trạm inactive:
        Giữ nguyên vì đã bị tạm ngừng thủ công.

    Trạm còn xe:
        available.

    Trạm hết xe:
        busy.
    """

    capacity = get_station_capacity(station)

    if station.status == 'inactive':
        return capacity

    if capacity['available_vehicles'] > 0:
        new_status = 'available'
    else:
        new_status = 'busy'

    if station.status != new_status:
        station.status = new_status

        station.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

    return capacity


def count_stations_with_capacity():
    """
    Đếm số trạm còn ít nhất một phương tiện trống.

    Một trạm có nhiều xe vẫn được xem là sẵn sàng
    nếu chưa sử dụng hết toàn bộ xe.
    """

    available_station_count = 0

    stations = (
        RescueStation.objects
        .exclude(status='inactive')
        .filter(vehicle_count__gt=0)
    )

    for station in stations:
        capacity = sync_station_status(station)

        if capacity['available_vehicles'] > 0:
            available_station_count += 1

    return available_station_count


# =====================================================
# OSRM - LẤY TUYẾN ĐƯỜNG THỰC TẾ
# =====================================================

def get_osrm_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Gọi OSRM để tìm tuyến đường giao thông thực tế.

    OSRM nhận tọa độ theo thứ tự:

        kinh độ,vĩ độ
    """

    base_url = getattr(
        settings,
        'OSRM_BASE_URL',
        'https://router.project-osrm.org',
    ).rstrip('/')

    coordinates = (
        f'{float(start_longitude)},'
        f'{float(start_latitude)};'
        f'{float(end_longitude)},'
        f'{float(end_latitude)}'
    )

    query_string = urllib.parse.urlencode({
        'overview': 'full',
        'geometries': 'geojson',
        'steps': 'false',
        'alternatives': 'false',
    })

    url = (
        f'{base_url}/route/v1/driving/'
        f'{coordinates}?{query_string}'
    )

    osrm_request = urllib.request.Request(
        url,
        headers={
            'User-Agent':
                'Django-Auto-Rescue-Dispatch/1.0',
        },
    )

    try:
        with urllib.request.urlopen(
            osrm_request,
            timeout=20,
        ) as response:

            response_content = (
                response
                .read()
                .decode('utf-8')
            )

            result = json.loads(
                response_content
            )

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f'OSRM trả về lỗi HTTP {error.code}.'
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            'Không thể kết nối dịch vụ tìm đường OSRM.'
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            'Dịch vụ tìm đường phản hồi quá chậm.'
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            'Dữ liệu tuyến đường OSRM không hợp lệ.'
        ) from error

    if result.get('code') != 'Ok':
        raise RuntimeError(
            result.get(
                'message',
                'OSRM không tìm thấy tuyến đường phù hợp.',
            )
        )

    routes = result.get('routes', [])

    if not routes:
        raise RuntimeError(
            'OSRM không trả về tuyến đường.'
        )

    route = routes[0]

    geometry = route.get('geometry')

    if not geometry:
        raise RuntimeError(
            'Tuyến đường không có dữ liệu hình học.'
        )

    distance_meters = float(
        route.get('distance', 0)
    )

    duration_seconds = float(
        route.get('duration', 0)
    )

    distance_km = round(
        distance_meters / 1000,
        2,
    )

    duration_minutes = max(
        1,
        round(duration_seconds / 60),
    )

    return {
        'distance_km': distance_km,
        'duration_minutes': duration_minutes,
        'geometry': geometry,
    }


# =====================================================
# XẾP HẠNG CÁC TRẠM
# =====================================================

def rank_stations_for_report(report):
    """
    Lấy các trạm còn xe rồi xếp hạng theo:

    1. Thời gian di chuyển ngắn nhất.
    2. Khoảng cách ngắn nhất.
    3. Ít nhiệm vụ đang xử lý hơn.
    4. Nhiều phương tiện còn trống hơn.
    """

    ranked_stations = []
    route_errors = []

    stations = (
        RescueStation.objects
        .exclude(status='inactive')
        .filter(vehicle_count__gt=0)
        .order_by('station_code')
    )

    for station in stations:
        capacity = get_station_capacity(station)

        # Trạm đã sử dụng hết phương tiện
        if capacity['available_vehicles'] <= 0:
            sync_station_status(station)
            continue

        try:
            route = get_osrm_route(
                start_latitude=
                    station.latitude,

                start_longitude=
                    station.longitude,

                end_latitude=
                    report.latitude,

                end_longitude=
                    report.longitude,
            )

        except RuntimeError as error:
            route_errors.append({
                'station_id':
                    station.id,

                'station_code':
                    station.station_code,

                'station_name':
                    station.name,

                'error':
                    str(error),
            })

            continue

        ranked_stations.append({
            'station':
                station,

            'distance_km':
                route['distance_km'],

            'duration_minutes':
                route['duration_minutes'],

            'geometry':
                route['geometry'],

            'vehicle_count':
                capacity['vehicle_count'],

            'active_count':
                capacity['active_count'],

            'available_vehicles':
                capacity['available_vehicles'],
        })

    ranked_stations.sort(
        key=lambda item: (
            item['duration_minutes'],
            item['distance_km'],
            item['active_count'],
            -item['available_vehicles'],
        )
    )

    return ranked_stations, route_errors


# =====================================================
# DỮ LIỆU TRẢ VỀ CHO GIAO DIỆN
# =====================================================

def build_dispatch_data(
    report,
    rescue_log,
):
    """
    Chuẩn hóa dữ liệu trả về cho trang chủ
    và dashboard.
    """

    station = rescue_log.station

    capacity = get_station_capacity(
        station
    )

    return {
        'report_id':
            report.id,

        'log_id':
            rescue_log.id,

        'auto_dispatched':
            True,

        'station': {
            'id':
                station.id,

            'station_code':
                station.station_code,

            'name':
                station.name,

            'phone':
                station.phone,

            'address':
                station.address,

            'latitude':
                float(station.latitude),

            'longitude':
                float(station.longitude),

            'vehicle_count':
                capacity['vehicle_count'],

            'active_count':
                capacity['active_count'],

            'available_vehicles':
                capacity['available_vehicles'],
        },

        'victim': {
            'name':
                report.victim_name
                or 'Chưa xác định',

            'phone':
                report.phone,

            'address':
                report.address,

            'latitude':
                float(report.latitude),

            'longitude':
                float(report.longitude),
        },

        'distance_km':
            rescue_log.route_distance_km,

        'estimated_time_minutes':
            rescue_log.estimated_time_minutes,

        'algorithm':
            rescue_log.algorithm,

        'route_geojson':
            rescue_log.route_data,

        'status':
            report.status,

        'status_display':
            report.get_status_display(),
    }


# =====================================================
# KIỂM TRA NGUYÊN NHÂN KHÔNG THỂ ĐIỀU PHỐI
# =====================================================

def get_dispatch_unavailable_result(
    route_errors,
):
    """
    Trả về nguyên nhân chưa điều phối được.
    """

    active_stations = (
        RescueStation.objects
        .exclude(status='inactive')
        .filter(vehicle_count__gt=0)
    )

    if not active_stations.exists():
        return {
            'success': False,
            'code': 'no_station',
            'message': (
                'Chưa có trạm cứu hộ nào '
                'đang hoạt động.'
            ),
            'route_errors': route_errors,
        }

    station_with_capacity_exists = False

    for station in active_stations:
        capacity = get_station_capacity(
            station
        )

        if capacity['available_vehicles'] > 0:
            station_with_capacity_exists = True
            break

    if not station_with_capacity_exists:
        return {
            'success': False,
            'code': 'no_capacity',
            'message': (
                'Tất cả trạm hiện đã sử dụng '
                'hết phương tiện.'
            ),
            'route_errors': route_errors,
        }

    return {
        'success': False,
        'code': 'routing_unavailable',
        'message': (
            'Có trạm còn phương tiện nhưng '
            'dịch vụ tìm đường hiện không phản hồi.'
        ),
        'route_errors': route_errors,
    }


# =====================================================
# TỰ ĐỘNG ĐIỀU PHỐI MỘT YÊU CẦU
# =====================================================

def dispatch_report(report):
    """
    Tự động chọn trạm phù hợp nhất.

    Nếu trạm gần nhất vừa hết xe,
    hệ thống sẽ thử trạm tiếp theo.
    """

    report.refresh_from_db()

    # Yêu cầu đã được phân công trước đó
    if (
        report.status in ACTIVE_REPORT_STATUSES
        and report.assigned_station_id
    ):
        latest_log = (
            report.rescue_logs
            .select_related('station')
            .order_by('-assigned_at')
            .first()
        )

        if latest_log:
            return {
                'success': True,
                'already_dispatched': True,
                'message':
                    'Yêu cầu đã được điều phối trước đó.',
                'data':
                    build_dispatch_data(
                        report,
                        latest_log,
                    ),
            }

    if report.status == 'completed':
        return {
            'success': False,
            'code': 'completed',
            'message':
                'Yêu cầu cứu hộ đã hoàn thành.',
        }

    if report.status == 'cancelled':
        return {
            'success': False,
            'code': 'cancelled',
            'message':
                'Yêu cầu cứu hộ đã bị hủy.',
        }

    ranked_stations, route_errors = (
        rank_stations_for_report(report)
    )

    if not ranked_stations:
        return get_dispatch_unavailable_result(
            route_errors
        )

    # Thử lần lượt từng trạm theo bảng xếp hạng
    for candidate in ranked_stations:

        with transaction.atomic():

            locked_report = (
                VictimReport.objects
                .select_for_update()
                .select_related(
                    'assigned_station'
                )
                .get(pk=report.pk)
            )

            # Có request khác vừa phân công yêu cầu này
            if (
                locked_report.status
                in ACTIVE_REPORT_STATUSES
                and locked_report.assigned_station_id
            ):
                latest_log = (
                    locked_report.rescue_logs
                    .select_related('station')
                    .order_by('-assigned_at')
                    .first()
                )

                if latest_log:
                    return {
                        'success':
                            True,

                        'already_dispatched':
                            True,

                        'message':
                            'Yêu cầu đã được điều phối.',

                        'data':
                            build_dispatch_data(
                                locked_report,
                                latest_log,
                            ),
                    }

            station = (
                RescueStation.objects
                .select_for_update()
                .get(
                    pk=candidate['station'].pk
                )
            )

            if station.status == 'inactive':
                continue

            capacity = get_station_capacity(
                station
            )

            # Trạm vừa hết xe, thử trạm tiếp theo
            if capacity['available_vehicles'] <= 0:
                sync_station_status(station)
                continue

            locked_report.assigned_station = (
                station
            )

            locked_report.status = (
                'assigned'
            )

            locked_report.save(
                update_fields=[
                    'assigned_station',
                    'status',
                    'updated_at',
                ]
            )

            route_feature = {
                'type': 'Feature',

                'properties': {
                    'report_id':
                        locked_report.id,

                    'station_id':
                        station.id,

                    'station_code':
                        station.station_code,

                    'station_name':
                        station.name,

                    'automatic_dispatch':
                        True,
                },

                'geometry':
                    candidate['geometry'],
            }

            rescue_log = (
                RescueLog.objects.create(
                    report=
                        locked_report,

                    station=
                        station,

                    route_distance_km=
                        candidate[
                            'distance_km'
                        ],

                    estimated_time_minutes=
                        candidate[
                            'duration_minutes'
                        ],

                    route_data=
                        route_feature,

                    algorithm=
                        'OSRM Auto Dispatch',

                    status=
                        'assigned',

                    notes=(
                        'Hệ thống tự động chọn '
                        'trạm còn phương tiện có '
                        'thời gian di chuyển '
                        'ngắn nhất.'
                    ),
                )
            )

            sync_station_status(
                station
            )

        return {
            'success':
                True,

            'already_dispatched':
                False,

            'message': (
                'Hệ thống đã tự động chọn '
                'trạm cứu hộ phù hợp nhất.'
            ),

            'data':
                build_dispatch_data(
                    locked_report,
                    rescue_log,
                ),
        }

    return {
        'success': False,
        'code': 'no_capacity',
        'message': (
            'Các trạm vừa sử dụng hết '
            'phương tiện. Yêu cầu được '
            'giữ trong hàng chờ.'
        ),
        'route_errors': route_errors,
    }


# =====================================================
# TỰ ĐỘNG XỬ LÝ HÀNG CHỜ
# =====================================================

def dispatch_pending_reports(limit=20):
    """
    Điều phối các yêu cầu đang chờ theo thứ tự:

    1. Khẩn cấp.
    2. Cao.
    3. Trung bình.
    4. Thấp.
    5. Yêu cầu gửi trước được ưu tiên trước.
    """

    priority_order = Case(
        When(
            emergency_level='critical',
            then=Value(4),
        ),

        When(
            emergency_level='high',
            then=Value(3),
        ),

        When(
            emergency_level='medium',
            then=Value(2),
        ),

        When(
            emergency_level='low',
            then=Value(1),
        ),

        default=Value(0),

        output_field=IntegerField(),
    )

    pending_reports = (
        VictimReport.objects
        .filter(status='pending')
        .annotate(
            dispatch_priority=
                priority_order
        )
        .order_by(
            '-dispatch_priority',
            'created_at',
        )[:limit]
    )

    dispatched_reports = []

    for report in pending_reports:
        result = dispatch_report(
            report
        )

        if result.get('success'):
            dispatched_reports.append(
                result['data']
            )

            continue

        error_code = result.get(
            'code'
        )

        # Hết toàn bộ xe thì chưa cần thử
        # các yêu cầu tiếp theo.
        if error_code == 'no_capacity':
            break

        # Không có trạm hoạt động
        if error_code == 'no_station':
            break

        # OSRM lỗi: không nên gọi liên tục
        if error_code == 'routing_unavailable':
            break

    return dispatched_reports