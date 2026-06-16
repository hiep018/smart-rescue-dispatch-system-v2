import json
import os
import urllib.error
import urllib.parse
import urllib.request
import cv2
import numpy as np

from django.db import transaction
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    RescueLog,
    RescueStation,
    VictimReport,
    FirstAidGuide
)

# =====================================================
# CẤU HÌNH DỊCH VỤ ĐỊNH TUYẾN
# =====================================================

OSRM_BASE_URL = 'https://router.project-osrm.org'


# =====================================================
# HÀM HỖ TRỢ CHUNG
# =====================================================

def parse_json_body(request):
    """
    Đọc dữ liệu JSON từ request.
    """
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def validate_coordinates(latitude, longitude):
    """
    Kiểm tra vĩ độ và kinh độ.
    """
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return (None, None, 'Tọa độ GPS không hợp lệ.')

    if not -90 <= latitude <= 90:
        return (None, None, 'Vĩ độ phải nằm trong khoảng -90 đến 90.')

    if not -180 <= longitude <= 180:
        return (None, None, 'Kinh độ phải nằm trong khoảng -180 đến 180.')

    return latitude, longitude, None


def get_osrm_route(start_latitude, start_longitude, end_latitude, end_longitude):
    """
    Gọi OSRM để tìm tuyến đường ô tô thực tế.
    """
    coordinates = (
        f'{float(start_longitude)},{float(start_latitude)};'
        f'{float(end_longitude)},{float(end_latitude)}'
    )

    query_string = urllib.parse.urlencode({
        'overview': 'full',
        'geometries': 'geojson',
        'steps': 'true',
        'alternatives': 'false',
    })

    url = f'{OSRM_BASE_URL}/route/v1/driving/{coordinates}?{query_string}'

    osrm_request = urllib.request.Request(
        url,
        headers={'User-Agent': 'Django-Rescue-Routing-System/1.0'}
    )

    try:
        with urllib.request.urlopen(osrm_request, timeout=20) as response:
            result = json.loads(response.read().decode('utf-8'))

    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Dịch vụ định tuyến trả về lỗi HTTP {error.code}.') from error
    except urllib.error.URLError as error:
        raise RuntimeError('Không thể kết nối dịch vụ định tuyến OSRM.') from error
    except TimeoutError as error:
        raise RuntimeError('Dịch vụ định tuyến phản hồi quá chậm.') from error
    except json.JSONDecodeError as error:
        raise RuntimeError('Dữ liệu tuyến đường trả về không hợp lệ.') from error

    if result.get('code') != 'Ok':
        raise RuntimeError(result.get('message', 'Không tìm thấy tuyến đường phù hợp.'))

    routes = result.get('routes', [])
    if not routes:
        raise RuntimeError('Dịch vụ không trả về tuyến đường.')

    route = routes[0]
    distance_meters = route.get('distance', 0)
    duration_seconds = route.get('duration', 0)
    geometry = route.get('geometry')

    if not geometry:
        raise RuntimeError('Tuyến đường không có dữ liệu hình học.')

    distance_km = round(distance_meters / 1000, 2)
    duration_minutes = max(1, round(duration_seconds / 60))

    return {
        'distance_km': distance_km,
        'duration_minutes': duration_minutes,
        'geometry': geometry,
    }


def find_best_station_by_road(victim_latitude, victim_longitude):
    """
    Tìm tuyến đường từ từng trạm đang sẵn sàng đến người gặp nạn.
    """
    stations = RescueStation.objects.filter(
        status='available',
        vehicle_count__gt=0
    ).order_by('station_code')

    best_result = None
    route_errors = []

    for station in stations:
        try:
            route = get_osrm_route(
                start_latitude=station.latitude,
                start_longitude=station.longitude,
                end_latitude=victim_latitude,
                end_longitude=victim_longitude,
            )

            candidate = {
                'station': station,
                'distance_km': route['distance_km'],
                'duration_minutes': route['duration_minutes'],
                'geometry': route['geometry'],
            }

            if best_result is None:
                best_result = candidate
                continue

            if candidate['duration_minutes'] < best_result['duration_minutes']:
                best_result = candidate
            elif (
                    candidate['duration_minutes'] == best_result['duration_minutes']
                    and candidate['distance_km'] < best_result['distance_km']
            ):
                best_result = candidate

        except RuntimeError as error:
            route_errors.append({
                'station_id': station.id,
                'station_name': station.name,
                'error': str(error),
            })

    return best_result, route_errors


def build_dispatch_response(report, rescue_log):
    """
    Chuẩn hóa dữ liệu điều phối trả về cho giao diện.
    """
    station = rescue_log.station
    return {
        'report_id': report.id,
        'log_id': rescue_log.id,
        'station': {
            'id': station.id,
            'station_code': station.station_code,
            'name': station.name,
            'phone': station.phone,
            'address': station.address,
            'latitude': float(station.latitude),
            'longitude': float(station.longitude),
        },
        'victim': {
            'name': report.victim_name or 'Chưa xác định',
            'phone': report.phone,
            'address': report.address,
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
        },
        'distance_km': rescue_log.route_distance_km,
        'estimated_time_minutes': rescue_log.estimated_time_minutes,
        'algorithm': rescue_log.algorithm,
        'route_geojson': rescue_log.route_data,
        'status': report.status,
        'status_display': report.get_status_display(),
    }


# =====================================================
# GIAO DIỆN CHÍNH
# =====================================================

def home(request):
    """Trang dành cho người gửi yêu cầu cứu hộ."""
    total_stations = RescueStation.objects.count()
    available_stations = RescueStation.objects.filter(status='available', vehicle_count__gt=0).count()
    active_requests = VictimReport.objects.filter(status__in=['pending', 'assigned', 'on_the_way']).count()
    completed_today = VictimReport.objects.filter(status='completed', updated_at__date=timezone.now().date()).count()

    context = {
        'total_stations': total_stations,
        'available_stations': available_stations,
        'active_requests': active_requests,
        'completed_today': completed_today,
    }
    return render(request, 'portal/home.html', context)


def rescue_map(request):
    """Trang bản đồ điều phối A*."""
    return render(request, 'portal/rescue_map.html')


def admin_dashboard(request):
    """Trang quản lý và điều phối cứu hộ."""
    today = timezone.now().date()
    total_stations = RescueStation.objects.count()
    available_stations = RescueStation.objects.filter(status='available', vehicle_count__gt=0).count()
    busy_stations = RescueStation.objects.filter(status='busy').count()
    total_requests = VictimReport.objects.count()
    pending_requests = VictimReport.objects.filter(status='pending').count()
    active_requests = VictimReport.objects.filter(status__in=['assigned', 'on_the_way']).count()
    completed_today = VictimReport.objects.filter(status='completed', updated_at__date=today).count()

    recent_requests = VictimReport.objects.select_related('assigned_station').order_by('-created_at')[:20]
    recent_logs = RescueLog.objects.select_related('report', 'station').order_by('-assigned_at')[:20]
    stations = RescueStation.objects.all().order_by('station_code')

    average_distance = RescueLog.objects.aggregate(average=Avg('route_distance_km'))['average'] or 0
    average_response_time = RescueLog.objects.aggregate(average=Avg('estimated_time_minutes'))['average'] or 0

    context = {
        'total_stations': total_stations,
        'available_stations': available_stations,
        'busy_stations': busy_stations,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'active_requests': active_requests,
        'completed_today': completed_today,
        'average_distance': round(average_distance, 2),
        'average_response_time': round(average_response_time, 1),
        'recent_requests': recent_requests,
        'recent_logs': recent_logs,
        'stations': stations,
    }
    return render(request, 'portal/admin_dashboard.html', context)


# =====================================================
# API THỐNG KÊ
# =====================================================

@require_http_methods(['GET'])
def api_stats(request):
    today = timezone.now().date()
    total_stations = RescueStation.objects.count()
    available_stations = RescueStation.objects.filter(status='available', vehicle_count__gt=0).count()
    pending_requests = VictimReport.objects.filter(status='pending').count()
    active_requests = VictimReport.objects.filter(status__in=['assigned', 'on_the_way']).count()
    completed_today = VictimReport.objects.filter(status='completed', updated_at__date=today).count()

    average_distance = RescueLog.objects.aggregate(average=Avg('route_distance_km'))['average'] or 0
    average_time = RescueLog.objects.aggregate(average=Avg('estimated_time_minutes'))['average'] or 0

    return JsonResponse({
        'success': True,
        'data': {
            'total_stations': total_stations,
            'available_stations': available_stations,
            'pending_requests': pending_requests,
            'active_requests': active_requests,
            'completed_today': completed_today,
            'average_distance': round(average_distance, 2),
            'average_response_time': round(average_time, 1),
            'last_sync': timezone.now().strftime('%H:%M:%S'),
        }
    })


# =====================================================
# API QUẢN LÝ TRẠM CỨU HỘ
# =====================================================

@require_http_methods(['GET'])
def api_rescue_stations(request):
    stations = RescueStation.objects.all().order_by('station_code')
    data = []
    for station in stations:
        data.append({
            'id': station.id,
            'station_code': station.station_code,
            'name': station.name,
            'phone': station.phone,
            'address': station.address,
            'latitude': float(station.latitude),
            'longitude': float(station.longitude),
            'status': station.status,
            'status_display': station.get_status_display(),
            'vehicle_count': station.vehicle_count,
            'is_available': station.is_available,
        })
    return JsonResponse({'success': True, 'data': data})


@csrf_exempt
@require_http_methods(['POST'])
def api_create_station(request):
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)

    required_fields = ['station_code', 'name', 'latitude', 'longitude']
    missing_fields = [field for field in required_fields if data.get(field) in [None, '']]

    if missing_fields:
        return JsonResponse({'success': False, 'error': 'Thiếu dữ liệu bắt buộc: ' + ', '.join(missing_fields)},
                            status=400)

    if RescueStation.objects.filter(station_code=data['station_code']).exists():
        return JsonResponse({'success': False, 'error': 'Mã trạm cứu hộ đã tồn tại.'}, status=400)

    latitude, longitude, coordinate_error = validate_coordinates(data.get('latitude'), data.get('longitude'))
    if coordinate_error:
        return JsonResponse({'success': False, 'error': coordinate_error}, status=400)

    try:
        vehicle_count = int(data.get('vehicle_count', 1))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Số phương tiện không hợp lệ.'}, status=400)

    if vehicle_count < 0:
        return JsonResponse({'success': False, 'error': 'Số phương tiện không được âm.'}, status=400)

    valid_statuses = [value for value, label in RescueStation.STATUS_CHOICES]
    status = data.get('status', 'available')
    if status not in valid_statuses:
        status = 'available'

    station = RescueStation.objects.create(
        station_code=data['station_code'].strip(),
        name=data['name'].strip(),
        phone=data.get('phone', '').strip(),
        address=data.get('address', '').strip(),
        latitude=latitude,
        longitude=longitude,
        status=status,
        vehicle_count=vehicle_count,
        notes=data.get('notes', '').strip(),
    )

    return JsonResponse({
        'success': True,
        'message': 'Đã tạo trạm cứu hộ.',
        'data': {'id': station.id, 'station_code': station.station_code, 'name': station.name}
    }, status=201)


@csrf_exempt
@require_http_methods(['PUT'])
def api_update_station(request, station_id):
    station = get_object_or_404(RescueStation, id=station_id)
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)

    new_station_code = data.get('station_code', station.station_code).strip()
    if RescueStation.objects.filter(station_code=new_station_code).exclude(id=station.id).exists():
        return JsonResponse({'success': False, 'error': 'Mã trạm cứu hộ đã tồn tại.'}, status=400)

    if 'latitude' in data or 'longitude' in data:
        latitude, longitude, coordinate_error = validate_coordinates(
            data.get('latitude', station.latitude),
            data.get('longitude', station.longitude)
        )
        if coordinate_error:
            return JsonResponse({'success': False, 'error': coordinate_error}, status=400)
        station.latitude = latitude
        station.longitude = longitude

    if 'vehicle_count' in data:
        try:
            vehicle_count = int(data['vehicle_count'])
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Số phương tiện không hợp lệ.'}, status=400)
        if vehicle_count < 0:
            return JsonResponse({'success': False, 'error': 'Số phương tiện không được âm.'}, status=400)
        station.vehicle_count = vehicle_count

    valid_statuses = [value for value, label in RescueStation.STATUS_CHOICES]
    new_status = data.get('status', station.status)
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': 'Trạng thái trạm không hợp lệ.'}, status=400)

    station.station_code = new_station_code
    station.name = data.get('name', station.name).strip()
    station.phone = data.get('phone', station.phone).strip()
    station.address = data.get('address', station.address).strip()
    station.notes = data.get('notes', station.notes).strip()
    station.status = new_status
    station.save()

    return JsonResponse({'success': True, 'message': 'Đã cập nhật trạm cứu hộ.'})


@csrf_exempt
@require_http_methods(['DELETE'])
def api_delete_station(request, station_id):
    station = get_object_or_404(RescueStation, id=station_id)
    try:
        station.delete()
    except Exception:
        return JsonResponse({'success': False, 'error': 'Không thể xóa trạm vì đang có nhật ký cứu hộ liên quan.'},
                            status=400)
    return JsonResponse({'success': True, 'message': 'Đã xóa trạm cứu hộ.'})


# =====================================================
# API GỬI YÊU CẦU CỨU HỘ
# =====================================================

@csrf_exempt
@require_http_methods(['POST'])
def api_request_rescue(request):
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    if latitude in [None, ''] or longitude in [None, '']:
        return JsonResponse(
            {'success': False, 'error': 'Không nhận được vị trí GPS. Vui lòng bật quyền truy cập vị trí.'}, status=400)

    latitude, longitude, coordinate_error = validate_coordinates(latitude, longitude)
    if coordinate_error:
        return JsonResponse({'success': False, 'error': coordinate_error}, status=400)

    valid_emergency_levels = [value for value, label in VictimReport.EMERGENCY_LEVEL_CHOICES]
    emergency_level = data.get('emergency_level', 'medium')
    if emergency_level not in valid_emergency_levels:
        emergency_level = 'medium'

    valid_location_sources = ['gps', 'three_words', 'map']
    location_source = data.get('location_source', 'gps')
    if location_source not in valid_location_sources:
        location_source = 'gps'

    location_accuracy_m = None
    try:
        raw_accuracy = data.get('location_accuracy_m')
        if raw_accuracy is not None:
            location_accuracy_m = float(raw_accuracy)
    except (TypeError, ValueError):
        location_accuracy_m = None

    what3words_address = str(data.get('what3words_address') or '').strip().removeprefix('///')

    report = VictimReport.objects.create(
        reporter=request.user if request.user.is_authenticated else None,
        victim_name=data.get('victim_name', '').strip(),
        phone=data.get('phone', '').strip(),
        description=data.get('description', '').strip(),
        emergency_level=emergency_level,
        latitude=latitude,
        longitude=longitude,
        address=data.get('address', '').strip(),
        location_source=location_source,
        location_accuracy_m=location_accuracy_m,
        what3words_address=what3words_address,
        assigned_station=None,
        status='pending',
    )

    return JsonResponse({
        'success': True,
        'message': 'Đã ghi nhận yêu cầu cứu hộ. Trung tâm điều phối sẽ chọn trạm và tuyến đường phù hợp.',
        'data': {
            'report_id': report.id,
            'status': report.status,
            'status_display': report.get_status_display(),
            'station': None,
        }
    }, status=201)


# =====================================================
# API ĐIỀU PHỐI VÀ TÌM ĐƯỜNG
# =====================================================

@csrf_exempt
@require_http_methods(['POST'])
def api_dispatch_rescue(request, report_id):
    report = get_object_or_404(VictimReport.objects.select_related('assigned_station'), id=report_id)

    if report.status in ['assigned', 'on_the_way'] and report.assigned_station:
        latest_log = report.rescue_logs.select_related('station').order_by('-assigned_at').first()
        if latest_log:
            return JsonResponse({
                'success': True,
                'message': 'Yêu cầu này đã được điều phối.',
                'data': build_dispatch_response(report, latest_log)
            })

    if report.status == 'completed':
        return JsonResponse({'success': False, 'error': 'Yêu cầu này đã hoàn thành.'}, status=400)

    if not RescueStation.objects.filter(status='available', vehicle_count__gt=0).exists():
        return JsonResponse({'success': False, 'error': 'Hiện không có trạm cứu hộ nào sẵn sàng.'}, status=400)

    best_result, route_errors = find_best_station_by_road(report.latitude, report.longitude)
    if best_result is None:
        return JsonResponse({
            'success': False,
            'error': 'Không thể tìm được tuyến đường từ các trạm đến vị trí người gặp nạn.',
            'route_errors': route_errors,
        }, status=502)

    station = best_result['station']

    with transaction.atomic():
        report.assigned_station = station
        report.status = 'assigned'
        report.save()

        from .auto_dispatch import sync_station_status
        sync_station_status(station)

        rescue_log = RescueLog.objects.create(
            report=report,
            station=station,
            route_distance_km=best_result['distance_km'],
            estimated_time_minutes=best_result['duration_minutes'],
            route_data={
                'type': 'Feature',
                'properties': {
                    'report_id': report.id,
                    'station_id': station.id,
                    'station_code': station.station_code,
                    'station_name': station.name,
                },
                'geometry': best_result['geometry'],
            },
            algorithm='OSRM',
            status='assigned',
        )

    return JsonResponse({
        'success': True,
        'message': 'Đã chọn trạm có thời gian di chuyển ngắn nhất.',
        'data': build_dispatch_response(report, rescue_log)
    }, status=201)


# =====================================================
# API DANH SÁCH VÀ CHI TIẾT YÊU CẦU
# =====================================================

@require_http_methods(['GET'])
def api_rescue_requests(request):
    status_filter = request.GET.get('status')
    reports = VictimReport.objects.select_related('assigned_station').all()

    if status_filter:
        reports = reports.filter(status=status_filter)
    reports = reports.order_by('-created_at')

    data = []
    for report in reports:
        station_data = None
        if report.assigned_station:
            station_data = {
                'id': report.assigned_station.id,
                'station_code': report.assigned_station.station_code,
                'name': report.assigned_station.name,
            }
        data.append({
            'id': report.id,
            'victim_name': report.victim_name,
            'phone': report.phone,
            'description': report.description,
            'emergency_level': report.emergency_level,
            'emergency_level_display': report.get_emergency_level_display(),
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
            'address': report.address,
            'location_source': report.location_source,
            'location_accuracy_m': report.location_accuracy_m,
            'what3words_address': report.what3words_address,
            'status': report.status,
            'status_display': report.get_status_display(),
            'assigned_station': station_data,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
        })

    return JsonResponse({'success': True, 'data': data})


@require_http_methods(['GET'])
def api_rescue_request_detail(request, report_id):
    report = get_object_or_404(VictimReport.objects.select_related('assigned_station'), id=report_id)
    logs = report.rescue_logs.select_related('station').order_by('-assigned_at')

    log_data = []
    for log in logs:
        log_data.append({
            'id': log.id,
            'station': {
                'id': log.station.id,
                'station_code': log.station.station_code,
                'name': log.station.name,
            },
            'route_distance_km': log.route_distance_km,
            'estimated_time_minutes': log.estimated_time_minutes,
            'route_data': log.route_data,
            'algorithm': log.algorithm,
            'status': log.status,
            'status_display': log.get_status_display(),
            'assigned_at': log.assigned_at.isoformat(),
            'completed_at': log.completed_at.isoformat() if log.completed_at else None,
        })

    station_data = None
    if report.assigned_station:
        station_data = {
            'id': report.assigned_station.id,
            'station_code': report.assigned_station.station_code,
            'name': report.assigned_station.name,
            'phone': report.assigned_station.phone,
            'address': report.assigned_station.address,
            'latitude': float(report.assigned_station.latitude),
            'longitude': float(report.assigned_station.longitude),
        }

    return JsonResponse({
        'success': True,
        'data': {
            'id': report.id,
            'victim_name': report.victim_name,
            'phone': report.phone,
            'description': report.description,
            'emergency_level': report.emergency_level,
            'emergency_level_display': report.get_emergency_level_display(),
            'latitude': float(report.latitude),
            'longitude': float(report.longitude),
            'address': report.address,
            'location_source': report.location_source,
            'location_accuracy_m': report.location_accuracy_m,
            'what3words_address': report.what3words_address,
            'status': report.status,
            'status_display': report.get_status_display(),
            'assigned_station': station_data,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
            'logs': log_data,
        }
    })


# =====================================================
# API CẬP NHẬT TRẠNG THÁI CỨU HỘ
# =====================================================

@csrf_exempt
@require_http_methods(['PUT'])
def api_update_rescue_status(request, report_id):
    report = get_object_or_404(VictimReport.objects.select_related('assigned_station'), id=report_id)
    data = parse_json_body(request)

    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)

    new_status = data.get('status')
    valid_statuses = [value for value, label in VictimReport.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': 'Trạng thái yêu cầu không hợp lệ.'}, status=400)

    latest_log = report.rescue_logs.order_by('-assigned_at').first()

    with transaction.atomic():
        report.status = new_status
        report.save()

        if latest_log:
            status_mapping = {
                'assigned': 'assigned',
                'on_the_way': 'departed',
                'completed': 'completed',
                'cancelled': 'failed',
            }
            log_status = status_mapping.get(new_status)
            if log_status:
                latest_log.status = log_status
            if new_status == 'completed':
                latest_log.completed_at = timezone.now()
            latest_log.save()

        if report.assigned_station:
            from .auto_dispatch import sync_station_status
            sync_station_status(report.assigned_station)

    return JsonResponse({
        'success': True,
        'message': 'Đã cập nhật trạng thái cứu hộ.',
        'data': {
            'report_id': report.id,
            'status': report.status,
            'status_display': report.get_status_display(),
        }
    })


# =====================================================
# API XÓA YÊU CẦU CỨU HỘ
# =====================================================

@csrf_exempt
@require_http_methods(['DELETE'])
def api_delete_rescue_request(request, report_id):
    report = get_object_or_404(VictimReport.objects.select_related('assigned_station'), id=report_id)
    station = report.assigned_station

    with transaction.atomic():
        report.delete()
        if station:
            from .auto_dispatch import sync_station_status
            sync_station_status(station)

    return JsonResponse({'success': True, 'message': 'Đã xóa yêu cầu cứu hộ.'})


# =====================================================
# API TRỢ LÝ HƯỚNG DẪN SƠ CỨU
# =====================================================

import re

def strip_accents(s):
    s = s.lower()
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    return s

import base64
from django.conf import settings

def call_gemini_api(query_text, image_bytes=None):
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return None

    import json
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    user_parts = []
    user_parts.append({"text": f"Triệu chứng / câu hỏi của người dùng: {query_text}"})

    if image_bytes is not None:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        user_parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": base64_image
            }
        })

    payload = {
        "system_instruction": {
            "parts": [{
                "text": (
                    "Bạn là chuyên gia sơ cứu khẩn cấp. Hãy phân tích triệu chứng hoặc hình ảnh vết thương do người dùng cung cấp. "
                    "Trả về JSON object với các trường:\n"
                    "1. 'title': Tên ngắn gọn của tình trạng chấn thương bằng tiếng Việt.\n"
                    "2. 'steps': Mảng các bước sơ cứu rõ ràng bằng tiếng Việt. Nếu nguy hiểm, thêm bước đầu tiên bắt đầu bằng '🚨 CẢNH BÁO NGUY HIỂM: ' và yêu cầu gọi ngay 115.\n"
                    "3. 'is_severe': boolean (true nếu nguy hiểm, false nếu nhẹ).\n"
                    "4. 'image_suggestion': Chọn MỘT trong các giá trị: 'bleeding' (chảy máu/vết cắt/đứt tay), 'burn' (bỏng lửa/nước sôi/hóa chất), 'fracture' (gãy xương/bong gân/trật khớp), 'head' (chấn thương đầu/sọ não/va đầu), 'food' (ngộ độc thức ăn/nôn mửa/tiêu chảy/đau bụng), 'insect' (ong đốt/côn trùng cắn/dị ứng), 'heat' (say nắng/say nóng/sốt cao/kiệt sức nhiệt), 'cpr' (ngừng thở/ngừng tim/bất tỉnh/hồi sức), 'snake' (rắn cắn/bị cắn bởi động vật có nọc độc), 'choking' (hóc/nghẹn/tắc đường thở), 'drowning' (đuối nước/chết đuối), 'eye' (chấn thương mắt/bụi vào mắt/hóa chất bắn vào mắt), 'none' (tình huống khác).\n\n"
                    "CHỈ trả về JSON thuần túy, không dùng markdown hay code block."
                )
            }]
        },
        "contents": [{
            "role": "user",
            "parts": user_parts
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text_response.strip())
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

@csrf_exempt
def api_first_aid_assistant(request):
    """
    API Trợ lý sơ cứu thông minh.
    Hỗ trợ tiếp nhận cả văn bản (query) hoặc ảnh chụp vết thương (image).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Phương thức không được hỗ trợ.'}, status=405)

    query_text = request.POST.get('query', '').strip().lower()
    uploaded_file = request.FILES.get('image')
    is_severe = False
    red_ratio = 0.0
    raw_image_bytes = None

    # Kiểm tra từ khóa nghiêm trọng trong query
    severe_keywords = ["lớn", "lon", "nặng", "nang", "nguy kịch", "nguy kich", "nhiều máu", "nhieu mau", "sâu", "sau", "cap cuu", "cấp cứu"]
    if any(kw in query_text for kw in severe_keywords):
        is_severe = True

    if uploaded_file:
        try:
            raw_image_bytes = uploaded_file.read()
            file_bytes = np.frombuffer(raw_image_bytes, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if image is not None:
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 50, 50])
                upper_red2 = np.array([180, 255, 255])

                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                red_mask = mask1 + mask2

                total_pixels = image.shape[0] * image.shape[1]
                red_pixels = np.sum(red_mask > 0)
                red_ratio = red_pixels / total_pixels

                if red_ratio > 0.04:
                    if not query_text:
                        query_text = "cam mau"
                
                # Tự động đánh giá vết thương lớn nếu diện tích màu đỏ (máu) > 12% diện tích ảnh
                if red_ratio > 0.12:
                    is_severe = True
            else:
                return JsonResponse({'success': False, 'error': 'Tệp hình ảnh gửi lên không hợp lệ.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Lỗi phân tích hình ảnh OpenCV: {str(e)}'}, status=500)

    if not query_text:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng cung cấp văn bản câu hỏi triệu chứng hoặc tải ảnh lên.'
        }, status=400)

    # 1. Thử gọi Gemini AI Agent trước nếu được cấu hình
    gemini_result = call_gemini_api(query_text, raw_image_bytes)
    if gemini_result and isinstance(gemini_result, dict) and 'title' in gemini_result and 'steps' in gemini_result:
        img_suggestion = gemini_result.get('image_suggestion', 'none')
        image_url = None
        image_map = {
            'bleeding':     'first_aid_images/first_aid_bleeding.png',
            'burn':         'first_aid_images/first_aid_burn.png',
            'fracture':     'first_aid_images/first_aid_fracture.png',
            'head':         'first_aid_images/first_aid_head_trauma.png',
            'food':         'first_aid_images/first_aid_food_poisoning.png',
            'insect':       'first_aid_images/first_aid_bee_sting.png',
            'heat':         'first_aid_images/first_aid_heat_stroke.png',
            'cpr':          'first_aid_images/first_aid_cpr.png',
            'snake':        'first_aid_images/first_aid_snake_bite.png',
            'animal':       'first_aid_images/first_aid_snake_bite.png',
            'choking':      'first_aid_images/first_aid_choking.png',
            'drowning':     'first_aid_images/first_aid_drowning.png',
            'eye':          'first_aid_images/first_aid_eye_injury.png',
            'none':         'first_aid_images/first_aid_general.png',
        }
        # Luôn có ảnh - dùng ảnh chung nếu không khớp loại cụ thể
        chosen = image_map.get(img_suggestion, image_map['none'])
        image_url = settings.MEDIA_URL + chosen

        return JsonResponse({
            'success': True,
            'detected_keyword': query_text,
            'is_severe': gemini_result.get('is_severe', is_severe),
            'red_ratio': round(red_ratio, 4),
            'results': [{
                'id': 999,
                'title': gemini_result.get('title', 'Hướng dẫn sơ cứu AI'),
                'steps': gemini_result.get('steps', []),
                'image_url': image_url,
            }]
        })

    # 2. Dự phòng: Tìm kiếm trong CSDL cục bộ nếu không dùng Gemini API hoặc bị lỗi
    # Chuẩn hóa truy vấn không dấu và phân tách thành các từ để tìm kiếm chính xác
    query_normalized = strip_accents(query_text)
    words = [w.strip() for w in query_normalized.split() if len(w.strip()) > 1]

    q_filter = Q(title__icontains=query_text) | Q(keywords__icontains=query_text)
    if words:
        for word in words:
            q_filter |= Q(keywords__icontains=word) | Q(title__icontains=word)

    guides = FirstAidGuide.objects.filter(q_filter)

    if not guides.exists():
        guides = FirstAidGuide.objects.filter(keywords__icontains="vet thuong")

    result_data = []
    for guide in guides:
        steps_list = [step.strip() for step in guide.steps_instructions.split('\n') if step.strip()]
        
        # Nếu được xác định là nghiêm trọng, chèn khuyến cáo gọi cấp cứu lên đầu danh sách các bước
        if is_severe:
            steps_list.insert(0, "🚨 CẢNH BÁO NGUY HIỂM: Vết thương lớn, mất nhiều máu hoặc có triệu chứng nặng. Hãy gọi ngay Cấp cứu 115 lập tức!")
            
        # image_illustration là CharField lưu đường dẫn tương đối, cần ghép với MEDIA_URL
        img_url = None
        if guide.image_illustration:
            img_url = settings.MEDIA_URL + str(guide.image_illustration)
        result_data.append({
            'id': guide.id,
            'title': guide.title,
            'steps': steps_list,
            'image_url': img_url
        })

    return JsonResponse({
        'success': True,
        'detected_keyword': query_text,
        'is_severe': is_severe,
        'red_ratio': round(red_ratio, 4),
        'results': result_data
    })


# =====================================================
# GIAO DIỆN TRANG TRỢ LÝ SƠ CỨU
# =====================================================

def first_aid_page(request):
    """
    Trang giao diện độc lập cho Trợ lý Sơ cứu Khẩn cấp AI.
    """
    return render(request, 'portal/first_aid.html')