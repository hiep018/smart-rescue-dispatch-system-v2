import json
import heapq
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from firebase_admin import firestore
from portal.views import parse_json_body, validate_coordinates
from portal.custom_map_views import haversine_km, get_road_distance_km

def get_db():
    return firestore.client()

def admin_dashboard(request):
    db = get_db()
    stations_ref = db.collection('stations').stream()
    incidents_ref = db.collection('rescue_requests').stream()
    
    # Pre-fetch stations to map assignedStationId to name
    station_map = {}
    stations = []
    available_stations = 0
    for s in stations_ref:
        d = s.to_dict()
        station_code = d.get('code', s.id)
        name = d.get('name', 'Trạm ' + station_code)
        active = d.get('active', False)
        
        station_map[station_code] = name
        
        stations.append({
            'id': s.id,
            'station_code': station_code,
            'name': name,
            'phone': d.get('phone', '—'),
            'address': d.get('address', '—'),
            'latitude': d.get('lat', 0.0),
            'longitude': d.get('lng', 0.0),
            'vehicle_count': d.get('maxIncidents', d.get('vehicle_count', 1)),
            'notes': d.get('notes', ''),
            'status': 'available' if active else 'inactive',
            'get_status_display': 'Sẵn sàng' if active else 'Tạm ngừng'
        })
        if active:
            available_stations += 1
            
    from portal.what3words_views import coords_to_3wa, cell_id_to_words
    
    users_ref = db.collection('users').stream()
    user_map = {}
    for u in users_ref:
        user_map[u.id] = u.to_dict()

    incidents = []
    completed_today = 0
    pending_requests = 0
    active_requests = 0
    
    for i in incidents_ref:
        d = i.to_dict()
        status = d.get('status', 'pending')
        
        status_display_map = {
            'pending': 'Đang chờ',
            'assigned': 'Đã phân công',
            'on_the_way': 'Đang đến',
            'completed': 'Hoàn thành',
            'cancelled': 'Đã hủy'
        }
        
        if status == 'completed':
            completed_today += 1
        elif status == 'pending':
            pending_requests += 1
        elif status in ['assigned', 'on_the_way']:
            active_requests += 1

        created_at = d.get('created_at')
        if not isinstance(created_at, datetime):
            created_at = datetime.now()
            
        emergency_level = d.get('emergency_level', 'low')
            
        station_id = d.get('assignedStationId')
        assigned_station = {'name': station_map.get(station_id, station_id)} if station_id else None

        # Resolve location to 3 words
        lat = d.get('latitude', 0.0)
        lng = d.get('longitude', 0.0)
        what3words_address = d.get('three_words', '')
        if not what3words_address and lat and lng:
            cell_id = coords_to_3wa(lat, lng)
            if cell_id is not None:
                what3words_address = cell_id_to_words(cell_id)

        victim_name = d.get('victim_name', '')
        phone = d.get('phone', '')
                
        if not victim_name:
            victim_name = 'Chưa xác định'
        if not phone:
            phone = '—'

        assigned_at_val = d.get('assigned_at')
        if assigned_at_val and isinstance(assigned_at_val, str):
            try:
                assigned_at_val = datetime.fromisoformat(assigned_at_val)
            except:
                pass

        route_geo = d.get('route_geojson')
        if isinstance(route_geo, str):
            try:
                route_geo = json.loads(route_geo)
            except:
                pass

        incidents.append({
            'id': i.id,
            'victim_name': victim_name,
            'description': d.get('description', ''),
            'phone': phone,
            'what3words_address': what3words_address,
            'emergency_level': emergency_level,
            'status': status,
            'get_status_display': status_display_map.get(status, status),
            'created_at': created_at,
            'timestamp_val': created_at.timestamp(),
            'assigned_station': assigned_station,
            'route_distance_km': d.get('route_distance_km', 0),
            'estimated_time_minutes': d.get('estimated_time_minutes', 0),
            'route_geojson': route_geo,
            'assigned_at': assigned_at_val,
            'algorithm': 'A*' if 'route_distance_km' in d else '',
            'report': {'id': i.id, 'victim_name': victim_name},
            'station': assigned_station if assigned_station else {'name': ''},
        })

    # Sort
    priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    recent_requests = sorted(incidents, key=lambda x: (priority.get(x.get('emergency_level', 'medium'), 0), x['timestamp_val']), reverse=True)[:20]
    
    logs = [i for i in incidents if i.get('assigned_at') and isinstance(i['assigned_at'], datetime)]
    recent_logs = sorted(logs, key=lambda x: x['assigned_at'], reverse=True)[:10]

    # Calculate average distance and response time
    avg_dist = 0
    avg_time = 0
    if logs:
        avg_dist = round(sum(l.get('route_distance_km', 0) for l in logs) / len(logs), 2)
        avg_time = round(sum(l.get('estimated_time_minutes', 0) for l in logs) / len(logs))

    context = {
        'total_stations': len(stations),
        'available_stations': available_stations,
        'busy_stations': len(stations) - available_stations,
        'total_requests': len(incidents),
        'pending_requests': pending_requests,
        'active_requests': active_requests,
        'completed_today': completed_today,
        'average_distance': avg_dist,
        'average_response_time': avg_time,
        'recent_requests': recent_requests,
        'recent_logs': recent_logs,
        'stations': stations,
    }
    return render(request, 'portal/admin_dashboard.html', context)

@require_http_methods(['GET'])
def api_stats(request):
    db = get_db()
    stations_ref = db.collection('stations').stream()
    incidents_ref = db.collection('rescue_requests').stream()
    
    total_stations = 0
    available_stations = 0
    for s in stations_ref:
        total_stations += 1
        if s.to_dict().get('active'):
            available_stations += 1
            
    pending_requests = 0
    active_requests = 0
    completed_today = 0
    
    for i in incidents_ref:
        status = i.to_dict().get('status', 'pending')
        if status == 'completed':
            completed_today += 1
        elif status == 'pending':
            pending_requests += 1
        elif status in ['assigned', 'on_the_way']:
            active_requests += 1

    return JsonResponse({
        'success': True,
        'data': {
            'total_stations': total_stations,
            'available_stations': available_stations,
            'pending_requests': pending_requests,
            'active_requests': active_requests,
            'completed_today': completed_today,
            'average_distance': 0,
            'average_response_time': 0,
            'last_sync': datetime.now().strftime('%H:%M:%S'),
        }
    })

@require_http_methods(['GET'])
def api_rescue_stations(request):
    db = get_db()
    
    incidents_ref = db.collection('rescue_requests').stream()
    busy_counts = {}
    for i in incidents_ref:
        d = i.to_dict()
        if d.get('status') in ['assigned', 'on_the_way']:
            sid = d.get('assignedStationId')
            if sid:
                busy_counts[sid] = busy_counts.get(sid, 0) + 1
                
    stations_ref = db.collection('stations').stream()
    data = []
    for s in stations_ref:
        d = s.to_dict()
        station_code = d.get('code', s.id)
        bc = busy_counts.get(station_code, 0) + busy_counts.get(s.id, 0)
        try:
            vc = int(d.get('maxIncidents', d.get('vehicle_count', 1)))
        except:
            vc = 1
            
        is_active = d.get('active', False)
        is_available = is_active and (bc < vc)
        
        data.append({
            'id': s.id,
            'station_code': station_code,
            'name': d.get('name', ''),
            'phone': d.get('phone', ''),
            'address': d.get('address', ''),
            'latitude': d.get('lat', 0),
            'longitude': d.get('lng', 0),
            'status': 'available' if is_available else 'busy',
            'status_display': 'Sẵn sàng' if is_available else 'Bận',
            'vehicle_count': vc,
            'busy_count': bc,
            'is_available': is_available,
        })
    return JsonResponse({'success': True, 'data': data})

@csrf_exempt
@require_http_methods(['POST'])
def api_create_station(request):
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)
        
    db = get_db()
    new_station_ref = db.collection('stations').document()
    try:
        vehicle_count = int(data.get('vehicle_count', 1))
    except:
        vehicle_count = 1
        
    new_station_ref.set({
        'code': data.get('station_code', '').strip(),
        'name': data.get('name', '').strip(),
        'phone': data.get('phone', '').strip(),
        'address': data.get('address', '').strip(),
        'lat': float(data.get('latitude', 0)),
        'lng': float(data.get('longitude', 0)),
        'active': data.get('status') == 'available',
        'vehicle_count': vehicle_count,
        'maxIncidents': vehicle_count,
        'notes': data.get('notes', '').strip(),
    })
    
    return JsonResponse({'success': True, 'message': 'Đã tạo trạm cứu hộ.', 'data': {'id': new_station_ref.id}})

@csrf_exempt
@require_http_methods(['PUT'])
def api_update_station(request, station_id):
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)
        
    db = get_db()
    station_ref = db.collection('stations').document(str(station_id))
    
    if not station_ref.get().exists:
        return JsonResponse({'success': False, 'error': 'Trạm không tồn tại'}, status=404)
        
    try:
        vehicle_count = int(data.get('vehicle_count', 1))
    except:
        vehicle_count = 1
        
    station_ref.update({
        'code': data.get('station_code', '').strip(),
        'name': data.get('name', '').strip(),
        'phone': data.get('phone', '').strip(),
        'address': data.get('address', '').strip(),
        'lat': float(data.get('latitude', 0)),
        'lng': float(data.get('longitude', 0)),
        'active': data.get('status') == 'available',
        'vehicle_count': vehicle_count,
        'maxIncidents': vehicle_count,
        'notes': data.get('notes', '').strip(),
    })
    
    return JsonResponse({'success': True, 'message': 'Đã cập nhật trạm cứu hộ.'})

@csrf_exempt
@require_http_methods(['DELETE'])
def api_delete_station(request, station_id):
    db = get_db()
    db.collection('stations').document(str(station_id)).delete()
    return JsonResponse({'success': True, 'message': 'Đã xóa trạm cứu hộ.'})


@require_http_methods(['GET'])
def api_rescue_requests(request):
    status_filter = request.GET.get('status')
    db = get_db()
    incidents_ref = db.collection('rescue_requests').stream()
    data = []
    
    for i in incidents_ref:
        d = i.to_dict()
        status = d.get('status', 'pending')
        if status_filter and status != status_filter:
            continue
            
        created_at = d.get('created_at')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        else:
            created_at = datetime.now().isoformat()
            
        emergency_level = d.get('emergency_level', 'medium')
        emergency_level_display_map = {
            'low': 'Thấp',
            'medium': 'Trung bình',
            'high': 'Cao',
            'critical': 'Khẩn cấp'
        }
            
        data.append({
            'id': i.id,
            'victim_name': d.get('victim_name', 'Chưa xác định'),
            'phone': d.get('phone', ''),
            'description': d.get('description', ''),
            'emergency_level': emergency_level,
            'emergency_level_display': emergency_level_display_map.get(emergency_level, emergency_level),
            'latitude': d.get('latitude', 0),
            'longitude': d.get('longitude', 0),
            'address': d.get('three_words', ''),
            'status': status,
            'status_display': status,
            'assigned_station': {'id': d.get('assignedStationId')} if d.get('assignedStationId') else None,
            'created_at': created_at,
            'updated_at': created_at,
        })
    
    priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    data.sort(key=lambda x: (priority.get(x.get('emergency_level', 'medium'), 0), x['created_at']), reverse=True)
    return JsonResponse({'success': True, 'data': data})

@require_http_methods(['GET'])
def api_rescue_request_detail(request, report_id):
    db = get_db()
    doc = db.collection('rescue_requests').document(str(report_id)).get()
    if not doc.exists:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
        
    d = doc.to_dict()
    status = d.get('status', 'pending')
    created_at = d.get('created_at')
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    else:
        created_at = datetime.now().isoformat()
        
    station_data = None
    if d.get('assignedStationId'):
        station_data = {'id': d.get('assignedStationId'), 'station_code': d.get('assignedStationId'), 'name': d.get('assignedStationId')}
        
    emergency_level = d.get('emergency_level', 'high')
    emergency_level_display_map = {
        'low': 'Thấp',
        'medium': 'Trung bình',
        'high': 'Cao',
        'critical': 'Khẩn cấp'
    }
        
    logs = []
    route_geo = d.get('route_geojson')
    if route_geo:
        if isinstance(route_geo, str):
            try:
                route_geo = json.loads(route_geo)
            except:
                pass
        logs.append({
            'route_distance_km': d.get('route_distance_km'),
            'estimated_time_minutes': d.get('estimated_time_minutes'),
            'route_data': route_geo,
            'algorithm': 'A*',
            'assigned_at': d.get('assigned_at')
        })

    return JsonResponse({
        'success': True,
        'data': {
            'id': doc.id,
            'victim_name': d.get('victim_name', 'Chưa xác định'),
            'description': d.get('description', ''),
            'emergency_level': emergency_level,
            'emergency_level_display': emergency_level_display_map.get(emergency_level, emergency_level),
            'latitude': d.get('latitude', 0),
            'longitude': d.get('longitude', 0),
            'status': status,
            'status_display': status,
            'assigned_station': station_data,
            'created_at': created_at,
            'updated_at': created_at,
            'logs': logs,
        }
    })

@csrf_exempt
@require_http_methods(['PUT'])
def api_update_rescue_status(request, report_id):
    data = parse_json_body(request)
    if not data or 'status' not in data:
        return JsonResponse({'success': False, 'error': 'Invalid body'}, status=400)
        
    db = get_db()
    db.collection('rescue_requests').document(str(report_id)).update({'status': data['status']})
    return JsonResponse({
        'success': True,
        'message': 'Đã cập nhật',
        'data': {'report_id': report_id, 'status': data['status'], 'status_display': data['status']}
    })

@csrf_exempt
@require_http_methods(['DELETE'])
def api_delete_rescue_request(request, report_id):
    db = get_db()
    db.collection('rescue_requests').document(str(report_id)).delete()
    return JsonResponse({'success': True, 'message': 'Đã xóa'})

@csrf_exempt
@require_http_methods(['POST'])
def api_firebase_dispatch(request, report_id):
    db = get_db()
    doc_ref = db.collection('rescue_requests').document(str(report_id))
    doc = doc_ref.get()
    
    if not doc.exists:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
        
    report = doc.to_dict()
    if report.get('status') in ['completed', 'cancelled']:
        return JsonResponse({'success': False, 'error': 'Yêu cầu đã kết thúc'}, status=400)
        
    victim_lat = float(report.get('latitude', 0.0))
    victim_lon = float(report.get('longitude', 0.0))
    
    stations_ref = db.collection('stations').where('active', '==', True).stream()
    incidents_ref = db.collection('rescue_requests').stream()
    
    busy_counts = {}
    for i in incidents_ref:
        doc_dict = i.to_dict()
        if doc_dict.get('status') in ['assigned', 'on_the_way']:
            sid = doc_dict.get('assignedStationId')
            if sid:
                busy_counts[sid] = busy_counts.get(sid, 0) + 1
                
    stations = []
    for s in stations_ref:
        d = s.to_dict()
        d['id'] = s.id
        station_code = d.get('code', s.id)
        bc = busy_counts.get(station_code, 0) + busy_counts.get(s.id, 0)
        try:
            vc = int(d.get('maxIncidents', d.get('vehicle_count', 1)))
        except:
            vc = 1
            
        if bc < vc:
            stations.append(d)
        
    if not stations:
        return JsonResponse({'success': False, 'error': 'Không có trạm cứu hộ nào sẵn sàng'}, status=503)
        
    open_heap = []
    for s in stations:
        s_lat = float(s.get('lat', 0.0))
        s_lon = float(s.get('lng', 0.0))
        h = haversine_km(s_lat, s_lon, victim_lat, victim_lon)
        heapq.heappush(open_heap, (h, s['id'], s, s_lat, s_lon))
        
    class FirebaseAStarNode:
        def __init__(self, dist, dur, geo):
            self.distance_km = dist
            self.duration_min = dur
            self.geometry = geo

    best_node = None
    best_station = None
    visited = set()
    errors = []
    
    while open_heap:
        h_est, s_id, s_data, s_lat, s_lon = heapq.heappop(open_heap)
        if s_id in visited: continue
        visited.add(s_id)
        
        try:
            dist_km, dur_min, geometry = get_road_distance_km(s_lat, s_lon, victim_lat, victim_lon)
        except Exception as e:
            errors.append({'station_id': s_id, 'error': str(e)})
            continue
            
        node = FirebaseAStarNode(dist_km, dur_min, geometry)
        if best_node is None:
            best_node = node
            best_station = s_data
        else:
            if dur_min < best_node.duration_min:
                best_node = node
                best_station = s_data
            elif dur_min == best_node.duration_min and dist_km < best_node.distance_km:
                best_node = node
                best_station = s_data
                
        if open_heap:
            if open_heap[0][0] >= best_node.distance_km:
                break
                
    if not best_node:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy đường đi', 'errors': errors}, status=503)
        
    # Update Firebase doc
    doc_ref.update({
        'status': 'assigned',
        'assignedStationId': best_station.get('code', best_station['id']),
        'route_distance_km': best_node.distance_km,
        'estimated_time_minutes': best_node.duration_min,
        'route_geojson': json.dumps(best_node.geometry),
        'assigned_at': datetime.now().isoformat()
    })
    
    # Return data for Leaflet
    return JsonResponse({
        'success': True,
        'message': f"Đã phân công trạm {best_station.get('name', '')}",
        'data': {
            'report_id': report_id,
            'station': {
                'id': best_station['id'],
                'station_code': best_station.get('code', best_station['id']),
                'name': best_station.get('name', ''),
                'phone': best_station.get('phone', ''),
                'address': best_station.get('address', ''),
                'latitude': float(best_station.get('lat', 0.0)),
                'longitude': float(best_station.get('lng', 0.0)),
            },
            'victim': {
                'name': report.get('victim_name', 'Chưa xác định'),
                'phone': report.get('phone', ''),
                'address': report.get('three_words', ''),
                'latitude': victim_lat,
                'longitude': victim_lon,
            },
            'distance_km': best_node.distance_km,
            'estimated_time_minutes': best_node.duration_min,
            'route_geojson': best_node.geometry,
            'errors': errors
        }
    })


@require_http_methods(['GET'])
def api_firebase_map_data(request):
    db = get_db()
    incidents_ref = db.collection('rescue_requests').stream()
    incidents_list = list(incidents_ref)
    
    busy_counts = {}
    for i in incidents_list:
        doc_dict = i.to_dict()
        if doc_dict.get('status') in ['assigned', 'on_the_way']:
            sid = doc_dict.get('assignedStationId')
            if sid:
                busy_counts[sid] = busy_counts.get(sid, 0) + 1
                
    stations_ref = db.collection('stations').stream()
    station_data = []
    
    for s in stations_ref:
        d = s.to_dict()
        station_code = d.get('code', s.id)
        bc = busy_counts.get(station_code, 0) + busy_counts.get(s.id, 0)
        try:
            vc = int(d.get('maxIncidents', d.get('vehicle_count', 1)))
        except:
            vc = 1
            
        is_active = d.get('active', False)
        is_available = is_active and (bc < vc)
        status = 'available' if is_available else 'busy'
        st = {
            'id': s.id,
            'station_code': station_code,
            'name': d.get('name', ''),
            'phone': d.get('phone', ''),
            'address': d.get('address', ''),
            'latitude': float(d.get('lat', 0)),
            'longitude': float(d.get('lng', 0)),
            'status': status,
            'status_display': 'Sẵn sàng' if is_available else 'Bận',
            'vehicle_count': vc,
            'busy_count': bc,
            'is_available': is_available,
        }
        station_data.append(st)
        
    report_data = []
    
    for i in incidents_list:
        d = i.to_dict()
        status = d.get('status', 'pending')
        if status not in ['pending', 'assigned', 'on_the_way']:
            continue
            
        created_at = d.get('created_at')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        elif not created_at:
            created_at = datetime.now().isoformat()
            
        emergency_level = d.get('emergency_level', 'medium')
        emergency_level_display_map = {
            'low': 'Thấp',
            'medium': 'Trung bình',
            'high': 'Cao',
            'critical': 'Khẩn cấp'
        }
        
        status_display_map = {
            'pending': 'Đang chờ',
            'assigned': 'Đã phân công',
            'on_the_way': 'Đang di chuyển'
        }
        
        assigned = None
        assigned_station_id = d.get('assignedStationId')
        if assigned_station_id:
            for st in station_data:
                if st['station_code'] == assigned_station_id or st['id'] == assigned_station_id:
                    assigned = {
                        'id': st['id'],
                        'name': st['name'],
                        'station_code': st['station_code'],
                    }
                    break
        
        route_geo = d.get('route_geojson')
        if route_geo:
            if isinstance(route_geo, str):
                try:
                    route_geo = json.loads(route_geo)
                except:
                    pass
                    
        report_data.append({
            'id': i.id,
            'victim_name': d.get('victim_name', 'Chưa xác định'),
            'phone': d.get('phone', ''),
            'address': d.get('three_words', ''),
            'latitude': float(d.get('latitude', 0)),
            'longitude': float(d.get('longitude', 0)),
            'emergency_level': emergency_level,
            'emergency_level_display': emergency_level_display_map.get(emergency_level, emergency_level),
            'status': status,
            'status_display': status_display_map.get(status, status),
            'assigned_station': assigned,
            'route_geojson': route_geo,
            'algorithm': 'A*' if route_geo else None,
            'created_at': str(created_at),
        })
        
    priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    report_data.sort(key=lambda x: (priority.get(x.get('emergency_level', 'medium'), 0), x['created_at']), reverse=True)
        
    return JsonResponse({
        'success': True,
        'data': {
            'stations': station_data,
            'active_reports': report_data,
        }
    })

