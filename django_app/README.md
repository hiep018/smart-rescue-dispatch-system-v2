# Hệ Thống Điều Phối Cứu Hộ Thông Minh

Dự án được xây dựng bằng **Python Django**, hỗ trợ tiếp nhận yêu cầu cứu hộ, xác định vị trí người gặp nạn và lựa chọn trạm cứu hộ phù hợp.

Hệ thống sử dụng **GPS**, **Leaflet**, **OpenStreetMap**, **địa chỉ ô 3 từ**, **thuật toán A\*** và **dịch vụ OSRM** để tính toán quãng đường, thời gian di chuyển và hiển thị tuyến đường cứu hộ trên bản đồ.

---

## Chức năng chính

| Chức năng | Mô tả |
|---|---|
| **Xác định vị trí** | Lấy vị trí bằng GPS, chọn trực tiếp trên bản đồ hoặc nhập địa chỉ ô 3 từ |
| **Gửi yêu cầu cứu hộ** | Lưu tên người gặp nạn, số điện thoại, mức độ khẩn cấp và mô tả sự cố |
| **Quản lý trạm cứu hộ** | Quản lý vị trí, trạng thái và số lượng phương tiện của từng trạm |
| **Điều phối thông minh** | Sử dụng thuật toán A* kết hợp OSRM để lựa chọn trạm cứu hộ phù hợp |
| **Hiển thị tuyến đường** | Hiển thị vị trí trạm, vị trí người gặp nạn và tuyến đường cứu hộ trên bản đồ |
| **Theo dõi trạng thái** | Theo dõi yêu cầu từ lúc chờ tiếp nhận đến khi hoàn thành hoặc hủy |
| **Thống kê hệ thống** | Thống kê số trạm, số yêu cầu đang xử lý và số yêu cầu đã hoàn thành |

---

## Yêu cầu phần cứng và phần mềm

| Thành phần | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11 |
| CPU | Intel Core i3 trở lên hoặc tương đương |
| RAM | Tối thiểu 4 GB |
| Python | 3.10 – 3.12 (khuyến nghị Python 3.12) |
| Editor | Visual Studio Code |
| Trình duyệt | Google Chrome hoặc Microsoft Edge |
| Kết nối Internet | Cần thiết để tải bản đồ và sử dụng dịch vụ OSRM |
| Git | Dùng để tải và cập nhật mã nguồn |

> **Lưu ý:** Hệ thống cứu hộ **không cần** cài OpenCV, InsightFace, ONNX Runtime, CUDA hoặc GPU NVIDIA.

---

## Hướng dẫn cài đặt môi trường

### Bước 1 — Pull dự án về máy

Mở Terminal trong Visual Studio Code và chạy:

```bash
git pull
```

Nếu máy chưa có dự án:

```bash
git clone <đường-dẫn-repository>
```

### Bước 2 — Di chuyển đến thư mục chứa manage.py

```bash
cd django_app
```

> Nếu Terminal đã đứng tại thư mục chứa `manage.py` thì không cần chạy lệnh này.

### Bước 3 — Tạo môi trường ảo

> Chỉ thực hiện trong **lần cài đặt đầu tiên**.

```bash
python -m venv venv
```

### Bước 4 — Kích hoạt môi trường ảo

**Windows (Command Prompt):**

```bash
venv\Scripts\activate
```

**Windows (PowerShell) — nếu bị chặn quyền chạy:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

### Bước 5 — Nâng cấp pip

```bash
python -m pip install --upgrade pip
```

### Bước 6 — Cài đặt các thư viện cần thiết

```bash
pip install Django Pillow python-dotenv
```

Kiểm tra Django đã được cài thành công:

```bash
python -m django --version
```

### Bước 7 — Cập nhật cơ sở dữ liệu

```bash
python manage.py migrate
```

> Chỉ khi có chỉnh sửa cấu trúc trong file `models.py`, chạy thêm:
>
> ```bash
> python manage.py makemigrations
> python manage.py migrate
> ```
>
> Khi chỉ `git pull` và đã có sẵn migration thì **không cần** chạy `makemigrations`.

### Bước 8 — Tạo dữ liệu cứu hộ mẫu

> Bước này **không bắt buộc**. Chỉ chạy khi cần dữ liệu để kiểm thử hoặc trình diễn.

```bash
python manage.py create_demo_rescue_data
```

Lệnh trên sẽ tạo:

- Các trạm cứu hộ mẫu
- Các yêu cầu cứu hộ mẫu
- Vị trí và trạng thái ban đầu để kiểm thử hệ thống

---

## Cấu trúc thư mục

```
django_app/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md
│
├── attendance_system/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── portal/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── auto_dispatch.py
│   ├── custom_map_views.py
│   ├── what3words_views.py
│   │
│   ├── migrations/
│   │   └── ...
│   │
│   └── management/
│       ├── __init__.py
│       └── commands/
│           ├── __init__.py
│           └── create_demo_rescue_data.py
│
├── templates/
│   ├── base.html
│   └── portal/
│       ├── home.html
│       ├── admin_dashboard.html
│       └── rescue_map.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
```

---

## Cách sử dụng

### Bước 1 — Kích hoạt môi trường ảo

```bash
venv\Scripts\activate
```

### Bước 2 — Cập nhật mã nguồn mới nhất

```bash
git pull
```

### Bước 3 — Cập nhật cơ sở dữ liệu

```bash
python manage.py migrate
```

### Bước 4 — Khởi chạy chương trình

```bash
python manage.py runserver
```

Sau khi server chạy thành công, Terminal sẽ hiển thị:

```
Starting development server at http://127.0.0.1:8000/
```

---

## Các địa chỉ truy cập

| Trang | URL |
|---|---|
| Trang gửi yêu cầu cứu hộ | http://127.0.0.1:8000/ |
| Trung tâm điều phối | http://127.0.0.1:8000/admin-dashboard/ |
| Bản đồ điều phối cứu hộ | http://127.0.0.1:8000/rescue-map/ |
| Trang quản trị Django | http://127.0.0.1:8000/admin/ |

---

## Quy trình hoạt động

```
1. Người dùng truy cập trang gửi yêu cầu cứu hộ
        |
        v
2. Xác định vị trí (GPS / Bản đồ / Địa chỉ 3 từ)
        |
        v
3. Nhập thông tin cá nhân và mô tả sự cố
        |
        v
4. Yêu cầu được lưu ở trạng thái: pending
        |
        v
5. Điều phối viên truy cập trung tâm điều phối
        |
        v
6. Nhấn nút "Điều phối A*"
        |
        v
7. Hệ thống kiểm tra các trạm còn phương tiện
        |
        v
8. OSRM tính quãng đường và thời gian di chuyển thực tế
        |
        v
9. Hệ thống lựa chọn trạm phù hợp nhất
        |
        v
10. Tuyến đường cứu hộ hiển thị trên bản đồ
        |
        v
11. Điều phối viên cập nhật trạng thái -> completed
```

---

## Trạng thái yêu cầu cứu hộ

| Trạng thái | Ý nghĩa |
|---|---|
| `pending` | Đang chờ tiếp nhận |
| `assigned` | Đã phân công trạm |
| `on_the_way` | Đang trên đường cứu hộ |
| `completed` | Đã hoàn thành |
| `cancelled` | Đã hủy |

---

## Trạng thái trạm cứu hộ

| Trạng thái | Ý nghĩa |
|---|---|
| `available` | Trạm đang sẵn sàng |
| `busy` | Trạm đã sử dụng hết phương tiện |
| `inactive` | Trạm tạm ngừng hoạt động |

> **Công thức tính xe còn trống:**
>
> ```
> Số xe còn trống = Tổng số xe - Số yêu cầu đang thực hiện
> ```

---

## Kiểm tra hệ thống hoạt động

**Kiểm tra cấu hình Django:**

```bash
python manage.py check
```

Kết quả mong đợi:

```
System check identified no issues (0 silenced).
```

**Kiểm tra danh sách trạm cứu hộ:**

```
http://127.0.0.1:8000/api/rescue-stations/
```

**Kiểm tra thống kê hệ thống:**

```
http://127.0.0.1:8000/api/stats/
```

**Kiểm tra dữ liệu bản đồ:**

```
http://127.0.0.1:8000/api/custom-map/data/
```

---

## Các lệnh sử dụng trong những lần chạy sau

```bash
venv\Scripts\activate
git pull
python manage.py migrate
python manage.py runserver
```

> Nếu không cần cập nhật mã nguồn từ Git, có thể bỏ qua `git pull`.

---

## Dừng chương trình

Tại Terminal đang chạy Django Server, nhấn:

```
Ctrl + C
```

Thoát môi trường ảo:

```bash
deactivate
```

---

## Lưu ý khi đưa dự án lên Git

**Không nên push các file và thư mục sau:**

```
venv/
__pycache__/
*.pyc
.env
.vscode/
.idea/
db.sqlite3
```

**Cần push các thành phần sau:**

```
manage.py
requirements.txt
attendance_system/
portal/
portal/migrations/
portal/management/commands/
templates/
static/
README.md
```

**Sau khi thành viên trong nhóm clone dự án, chỉ cần chạy:**

```bash
python manage.py migrate
python manage.py create_demo_rescue_data
python manage.py runserver
```
