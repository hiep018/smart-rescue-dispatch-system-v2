from django.core.management.base import BaseCommand

from portal.models import RescueStation, VictimReport


class Command(BaseCommand):
    help = "Tạo dữ liệu demo cho bản đồ cứu hộ tự xây dựng."

    def handle(self, *args, **options):
        station_data = [
            {
                "station_code": "CH-01",
                "name": "Trạm cứu hộ Trung tâm",
                "phone": "0901000001",
                "address": "Khu trung tâm bản đồ mô phỏng",
                "latitude": 10.8290,
                "longitude": 106.7240,
                "status": "available",
                "vehicle_count": 3,
            },
            {
                "station_code": "CH-02",
                "name": "Trạm cứu hộ Đông Bắc",
                "phone": "0901000002",
                "address": "Khu Đông Bắc bản đồ mô phỏng",
                "latitude": 10.8370,
                "longitude": 106.7330,
                "status": "available",
                "vehicle_count": 2,
            },
            {
                "station_code": "CH-03",
                "name": "Trạm cứu hộ Tây Nam",
                "phone": "0901000003",
                "address": "Khu Tây Nam bản đồ mô phỏng",
                "latitude": 10.8210,
                "longitude": 106.7150,
                "status": "available",
                "vehicle_count": 2,
            },
        ]

        for item in station_data:
            station_code = item.pop("station_code")

            RescueStation.objects.update_or_create(
                station_code=station_code,
                defaults=item,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Đã tạo/cập nhật trạm {station_code}"
                )
            )

        if not VictimReport.objects.exists():
            VictimReport.objects.create(
                victim_name="Nguyễn Văn A",
                phone="0909000001",
                description="Cần hỗ trợ khẩn cấp.",
                emergency_level="high",
                latitude=10.825503,
                longitude=106.725434,
                address="Vị trí mẫu gần trung tâm",
                status="pending",
            )

            VictimReport.objects.create(
                victim_name="Trần Thị B",
                phone="0909000002",
                description="Phương tiện gặp sự cố.",
                emergency_level="medium",
                latitude=10.8165,
                longitude=106.7370,
                address="Vị trí mẫu khu Đông Nam",
                status="pending",
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Đã tạo hai yêu cầu cứu hộ mẫu."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Đã có yêu cầu cứu hộ nên không tạo thêm."
                )
            )
