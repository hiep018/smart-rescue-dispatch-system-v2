from django.urls import path

from . import custom_map_views
from . import views
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
        views.admin_dashboard,
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
        views.api_stats,
        name="api_stats",
    ),

    # =================================================
    # API TRẠM CỨU HỘ
    # =================================================
    path(
        "api/rescue-stations/",
        views.api_rescue_stations,
        name="api_rescue_stations",
    ),
    path(
        "api/rescue-stations/create/",
        views.api_create_station,
        name="api_create_station",
    ),
    path(
        "api/rescue-stations/<int:station_id>/update/",
        views.api_update_station,
        name="api_update_station",
    ),
    path(
        "api/rescue-stations/<int:station_id>/delete/",
        views.api_delete_station,
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
        views.api_rescue_requests,
        name="api_rescue_requests",
    ),
    path(
        "api/rescue/requests/<int:report_id>/",
        views.api_rescue_request_detail,
        name="api_rescue_request_detail",
    ),
    path(
        "api/rescue/requests/<int:report_id>/status/",
        views.api_update_rescue_status,
        name="api_update_rescue_status",
    ),
    path(
        "api/rescue/requests/<int:report_id>/delete/",
        views.api_delete_rescue_request,
        name="api_delete_rescue_request",
    ),

    # =================================================
    # BẢN ĐỒ TỰ XÂY DỰNG
    # =================================================
    path(
        "api/custom-map/data/",
        custom_map_views.api_custom_map_data,
        name="api_custom_map_data",
    ),
    path(
        "api/rescue/requests/<int:report_id>/dispatch/",
        custom_map_views.api_custom_dispatch,
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
]