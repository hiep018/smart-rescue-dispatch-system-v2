
from django.contrib import admin

from .models import (
    RescueStation,
    VictimReport,
    RescueLog,
    SystemStats,
)


# =====================================================
# QUẢN LÝ TRẠM CỨU HỘ
# =====================================================

@admin.register(RescueStation)
class RescueStationAdmin(admin.ModelAdmin):
    list_display = [
        'station_code',
        'name',
        'phone',
        'address',
        'status',
        'vehicle_count',
        'created_at',
    ]

    list_filter = [
        'status',
        'created_at',
    ]

    search_fields = [
        'station_code',
        'name',
        'phone',
        'address',
    ]

    ordering = [
        'station_code',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (
            'Thông tin trạm cứu hộ',
            {
                'fields': (
                    'station_code',
                    'name',
                    'manager',
                    'phone',
                    'address',
                )
            }
        ),
        (
            'Vị trí trạm',
            {
                'fields': (
                    'latitude',
                    'longitude',
                )
            }
        ),
        (
            'Trạng thái hoạt động',
            {
                'fields': (
                    'status',
                    'vehicle_count',
                    'notes',
                )
            }
        ),
        (
            'Thông tin hệ thống',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                )
            }
        ),
    )


# =====================================================
# QUẢN LÝ YÊU CẦU CỨU HỘ
# =====================================================

@admin.register(VictimReport)
class VictimReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'victim_name',
        'phone',
        'emergency_level',
        'status',
        'assigned_station',
        'created_at',
    ]

    list_filter = [
        'emergency_level',
        'status',
        'assigned_station',
        'created_at',
    ]

    search_fields = [
        'victim_name',
        'phone',
        'address',
        'description',
    ]

    ordering = [
        '-created_at',
    ]

    date_hierarchy = 'created_at'

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (
            'Thông tin người gặp nạn',
            {
                'fields': (
                    'reporter',
                    'victim_name',
                    'phone',
                    'description',
                    'emergency_level',
                )
            }
        ),
        (
            'Vị trí người gặp nạn',
            {
                'fields': (
                    'latitude',
                    'longitude',
                    'address',
                )
            }
        ),
        (
            'Điều phối cứu hộ',
            {
                'fields': (
                    'assigned_station',
                    'status',
                )
            }
        ),
        (
            'Thông tin hệ thống',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                )
            }
        ),
    )


# =====================================================
# QUẢN LÝ NHẬT KÝ CỨU HỘ
# =====================================================

@admin.register(RescueLog)
class RescueLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'report',
        'station',
        'route_distance_km',
        'estimated_time_minutes',
        'algorithm',
        'status',
        'assigned_at',
    ]

    list_filter = [
        'status',
        'algorithm',
        'station',
        'assigned_at',
    ]

    search_fields = [
        'report__victim_name',
        'report__phone',
        'station__station_code',
        'station__name',
        'notes',
    ]

    ordering = [
        '-assigned_at',
    ]

    date_hierarchy = 'assigned_at'

    readonly_fields = [
        'assigned_at',
    ]

    fieldsets = (
        (
            'Thông tin điều phối',
            {
                'fields': (
                    'report',
                    'station',
                    'status',
                )
            }
        ),
        (
            'Thông tin tuyến đường',
            {
                'fields': (
                    'route_distance_km',
                    'estimated_time_minutes',
                    'algorithm',
                    'route_data',
                )
            }
        ),
        (
            'Thông tin xử lý',
            {
                'fields': (
                    'notes',
                    'assigned_at',
                    'completed_at',
                )
            }
        ),
    )


# =====================================================
# QUẢN LÝ THỐNG KÊ HỆ THỐNG
# =====================================================

@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'total_requests',
        'completed_requests',
        'cancelled_requests',
        'average_response_time',
        'average_distance',
    ]

    list_filter = [
        'date',
    ]

    ordering = [
        '-date',
    ]

    date_hierarchy = 'date'

