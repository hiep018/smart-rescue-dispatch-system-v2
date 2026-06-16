
from django.db import models
from django.contrib.auth.models import User


class RescueStation(models.Model):
    """Lưu thông tin trạm cứu hộ."""

    STATUS_CHOICES = [
        ('available', 'Sẵn sàng'),
        ('busy', 'Đang thực hiện cứu hộ'),
        ('inactive', 'Tạm ngừng hoạt động'),
    ]

    station_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Mã trạm cứu hộ'
    )

    name = models.CharField(
        max_length=100,
        verbose_name='Tên trạm cứu hộ'
    )

    manager = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_rescue_station',
        verbose_name='Người quản lý'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Số điện thoại'
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Địa chỉ'
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='Vĩ độ'
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='Kinh độ'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Trạng thái'
    )

    vehicle_count = models.PositiveIntegerField(
        default=1,
        verbose_name='Số phương tiện cứu hộ'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Lần cập nhật cuối'
    )

    class Meta:
        verbose_name = 'Trạm cứu hộ'
        verbose_name_plural = 'Danh sách trạm cứu hộ'
        ordering = ['station_code']

    def __str__(self):
        return f'{self.station_code} - {self.name}'

    @property
    def is_available(self):
        return self.status == 'available' and self.vehicle_count > 0


class VictimReport(models.Model):
    """Lưu yêu cầu cứu hộ của người gặp nạn."""

    EMERGENCY_LEVEL_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('critical', 'Khẩn cấp'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Đang chờ tiếp nhận'),
        ('assigned', 'Đã phân công trạm'),
        ('on_the_way', 'Đang trên đường cứu hộ'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='victim_reports',
        verbose_name='Tài khoản gửi yêu cầu'
    )

    victim_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tên người gặp nạn'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Số điện thoại'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Mô tả tình trạng'
    )

    emergency_level = models.CharField(
        max_length=20,
        choices=EMERGENCY_LEVEL_CHOICES,
        default='medium',
        verbose_name='Mức độ khẩn cấp'
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='Vĩ độ người gặp nạn'
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name='Kinh độ người gặp nạn'
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Địa chỉ gần đúng'
    )

    location_source = models.CharField(
        max_length=20,
        choices=[
            ('gps', 'GPS'),
            ('three_words', 'Địa chỉ ba từ'),
            ('map', 'Chọn trên bản đồ'),
        ],
        default='gps',
        verbose_name='Nguồn vị trí',
    )

    location_accuracy_m = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Độ chính xác GPS (m)',
    )

    what3words_address = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Địa chỉ ba từ',
    )

    assigned_station = models.ForeignKey(
        RescueStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports',
        verbose_name='Trạm được phân công'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Trạng thái'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian gửi yêu cầu'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Lần cập nhật cuối'
    )

    class Meta:
        verbose_name = 'Yêu cầu cứu hộ'
        verbose_name_plural = 'Danh sách yêu cầu cứu hộ'
        ordering = ['-created_at']

    def __str__(self):
        victim_name = self.victim_name or 'Chưa xác định'

        return (
            f'Yêu cầu #{self.pk} - '
            f'{victim_name} - '
            f'{self.get_status_display()}'
        )


class RescueLog(models.Model):
    """Lưu lịch sử điều phối và quá trình cứu hộ."""

    STATUS_CHOICES = [
        ('assigned', 'Đã phân công'),
        ('departed', 'Đã xuất phát'),
        ('arrived', 'Đã đến hiện trường'),
        ('completed', 'Đã hoàn thành'),
        ('failed', 'Không thể thực hiện'),
    ]

    report = models.ForeignKey(
        VictimReport,
        on_delete=models.CASCADE,
        related_name='rescue_logs',
        verbose_name='Yêu cầu cứu hộ'
    )

    station = models.ForeignKey(
        RescueStation,
        on_delete=models.PROTECT,
        related_name='rescue_logs',
        verbose_name='Trạm cứu hộ'
    )

    route_distance_km = models.FloatField(
        default=0.0,
        verbose_name='Quãng đường đề xuất (km)'
    )

    estimated_time_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name='Thời gian dự kiến (phút)'
    )

    route_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dữ liệu tuyến đường',
        help_text=(
            'Lưu danh sách tọa độ hoặc dữ liệu tuyến đường '
            'do thuật toán hoặc API bản đồ trả về.'
        )
    )

    algorithm = models.CharField(
        max_length=50,
        default='A*',
        verbose_name='Thuật toán định tuyến'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned',
        verbose_name='Trạng thái xử lý'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú'
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian phân công'
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian hoàn thành'
    )

    class Meta:
        verbose_name = 'Nhật ký cứu hộ'
        verbose_name_plural = 'Lịch sử cứu hộ'
        ordering = ['-assigned_at']

    def __str__(self):
        return (
            f'Nhật ký #{self.pk} - '
            f'{self.station.name} - '
            f'Yêu cầu #{self.report_id}'
        )


class SystemStats(models.Model):
    """Lưu thống kê hoạt động cứu hộ theo ngày."""

    date = models.DateField(
        unique=True,
        verbose_name='Ngày'
    )

    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='Tổng yêu cầu cứu hộ'
    )

    completed_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='Số yêu cầu đã hoàn thành'
    )

    cancelled_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='Số yêu cầu đã hủy'
    )

    average_response_time = models.FloatField(
        default=0.0,
        verbose_name='Thời gian phản hồi trung bình (phút)'
    )

    average_distance = models.FloatField(
        default=0.0,
        verbose_name='Quãng đường trung bình (km)'
    )

    class Meta:
        verbose_name = 'Thống kê hệ thống'
        verbose_name_plural = 'Thống kê hệ thống'
        ordering = ['-date']

    def __str__(self):
        return f'Thống kê cứu hộ - {self.date}'

    average_response_time = models.FloatField(
        default=0.0,
        verbose_name='Thời gian phản hồi trung bình (phút)'
    )

    average_distance = models.FloatField(
        default=0.0,
        verbose_name='Quãng đường trung bình (km)'
    )

    class Meta:
        verbose_name = 'Thống kê hệ thống'
        verbose_name_plural = 'Thống kê hệ thống'
        ordering = ['-date']

    def __str__(self):
        return f'Thống kê cứu hộ - {self.date}'


# =====================================================
# LƯU Ý: CLASS NÀY PHẢI NẰM SÁT LỀ TRÁI (KHÔNG THỤT LỀ)
# =====================================================
class FirstAidGuide(models.Model):
    """Model lưu trữ các bài viết hướng dẫn sơ cứu chấn thương khẩn cấp"""

    title = models.CharField(max_length=200, verbose_name="Tên chấn thương / Vết thương")
    keywords = models.CharField(
        max_length=255,
        help_text="Các từ khóa tìm kiếm không dấu cách nhau bằng dấu phẩy, vd: cam mau, chan thuong, vet thuong ho",
        verbose_name="Từ khóa hệ thống"
    )
    steps_instructions = models.TextField(
        help_text="Nhập các bước sơ cứu, mỗi bước cách nhau bằng một dấu xuống dòng (Enter)",
        verbose_name="Các bước hướng dẫn sơ cứu"
    )
    image_illustration = models.ImageField(
        upload_to='first_aid_images/',
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa thao tác"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bài hướng dẫn sơ cứu"
        verbose_name_plural = "Danh sách bài hướng dẫn sơ cứu"

    def __str__(self):
        return self.title