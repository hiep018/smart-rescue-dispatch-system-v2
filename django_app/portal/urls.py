from django.urls import path

from . import custom_map_views
from . import views
from . import firebase_views
from . import what3words_views

app_name = "portal"

urlpatterns = [
    # =================================================
    # GIAO DIỆN TRANG CHỦ & QUẢN TRỊ
    # =================================================
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "admin-dashboard/",
        firebase_views.admin_dashboard,
        name="admin_dashboard",
    ),
    path(
        "rescue-map/",
        views.rescue_map,
        name="rescue_map",
    ),

    # MỚI THÊM: Giao diện Trang Trợ lý Sơ cứu AI
    path(
        "first-aid/",
        views.first_aid_page,
        name="first_aid_page"
    ),

    # =================================================
    # API THỐNG KÊ
    # =================================================
    path(
        "api/stats/",
        firebase_views.api_stats,
        name="api_stats",
    ),

    # =================================================
    # API TRẠM CỨU HỘ
    # =================================================
    path(
        "api/rescue-stations/",
        firebase_views.api_rescue_stations,
        name="api_rescue_stations",
    ),
    path(
        "api/rescue-stations/create/",
        firebase_views.api_create_station,
        name="api_create_station",
    ),
    path(
        "api/rescue-stations/<str:station_id>/update/",
        firebase_views.api_update_station,
        name="api_update_station",
    ),
    path(
        "api/rescue-stations/<str:station_id>/delete/",
        firebase_views.api_delete_station,
        name="api_delete_station",
    ),

    # =================================================
    # API YÊU CẦU CỨU HỘ
    # =================================================
    path(
        "api/rescue/request/",
        views.api_request_rescue,
        name="api_request_rescue",
    ),
    path(
        "api/rescue/requests/",
        firebase_views.api_rescue_requests,
        name="api_rescue_requests",
    ),
    path(
        "api/rescue/requests/<str:report_id>/",
        firebase_views.api_rescue_request_detail,
        name="api_rescue_request_detail",
    ),
    path(
        "api/rescue/requests/<str:report_id>/status/",
        firebase_views.api_update_rescue_status,
        name="api_update_rescue_status",
    ),
    path(
        "api/rescue/requests/<str:report_id>/delete/",
        firebase_views.api_delete_rescue_request,
        name="api_delete_rescue_request",
    ),

    # =================================================
    # BẢN ĐỒ TỰ XÂY DỰNG
    # =================================================
    path(
        "api/custom-map/data/",
        firebase_views.api_firebase_map_data,
        name="api_custom_map_data",
    ),
    path(
        "api/rescue/requests/<str:report_id>/dispatch/",
        firebase_views.api_firebase_dispatch,
        name="api_dispatch_rescue",
    ),

    # =================================================
    # API ĐỊNH VỊ (WHAT3WORDS)
    # =================================================
    path(
        'api/location/coordinates-to-3wa/',
        what3words_views.api_coordinates_to_3wa,
        name='api_coordinates_to_3wa',
    ),
    path(
        'api/location/3wa-to-coordinates/',
        what3words_views.api_3wa_to_coordinates,
        name='api_3wa_to_coordinates',
    ),
    path(
        'api/location/grid-section/',
        what3words_views.api_grid_section,
        name='api_grid_section',
    ),

    # =================================================
    # MỚI THÊM: API TRỢ LÝ SƠ CỨU AI
    # =================================================
    path(
        'api/first-aid-assistant/',
        views.api_first_aid_assistant,
        name='api_first_aid_assistant'
    ),

    # =================================================
    # NHIỆM VỤ HỆ THỐNG & AUTO-FIX
    # =================================================
    path(
        'system-tasks/',
        firebase_views.system_tasks_page,
        name='system_tasks'
    ),
    path(
        'api/system-tasks/',
        firebase_views.api_get_system_tasks,
        name='api_system_tasks'
    ),
    path(
        'api/system-tasks/<str:task_id>/autofix/',
        firebase_views.api_autofix_task,
        name='api_autofix_task'
    ),
    path(
        'api/system-tasks/mock/',
        firebase_views.api_mock_error,
        name='api_mock_error'
    ),

    # =================================================
    # MODULE CẢNH BÁO BÃO & HƯỚNG DẪN AN TOÀN
    # =================================================
    path(
        'storm-warning/',
        views.storm_warning_page,
        name='storm_warning',
    ),
    path(
        'api/storm/alerts/',
        views.api_storm_alerts,
        name='api_storm_alerts',
    ),
    path(
        'api/weather/current/',
        views.api_weather_current,
        name='api_weather_current',
    ),
]