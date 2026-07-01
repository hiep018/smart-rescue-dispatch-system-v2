# 🚨 Hệ Thống Điều Phối Cứu Hộ Thông Minh

Dự án được xây dựng bằng **Python Django**, hỗ trợ tiếp nhận yêu cầu cứu hộ, xác định vị trí người gặp nạn, lựa chọn trạm cứu hộ phù hợp và cung cấp hướng dẫn sơ cứu ban đầu.

Hệ thống sử dụng các công nghệ:

* GPS.
* Leaflet.
* OpenStreetMap.
* Địa chỉ ô 3 từ.
* Thuật toán A*.
* Dịch vụ OSRM.
* OpenCV.
* Cơ sở dữ liệu hướng dẫn sơ cứu.

Các công nghệ trên được sử dụng để xác định vị trí, tính toán quãng đường, ước tính thời gian di chuyển, lựa chọn trạm cứu hộ và hiển thị tuyến đường trên bản đồ.

---

## ✨ Chức năng chính

| Chức năng            | Mô tả                                                                        |
| -------------------- | ---------------------------------------------------------------------------- |
| Xác định vị trí      | Lấy vị trí bằng GPS, chọn trực tiếp trên bản đồ hoặc nhập địa chỉ ô 3 từ     |
| Gửi yêu cầu cứu hộ   | Lưu tên người gặp nạn, số điện thoại, mức độ khẩn cấp và mô tả sự cố         |
| Quản lý trạm cứu hộ  | Quản lý vị trí, trạng thái và số lượng phương tiện của từng trạm             |
| Điều phối thông minh | Sử dụng thuật toán A* kết hợp OSRM để lựa chọn trạm cứu hộ phù hợp           |
| Hiển thị tuyến đường | Hiển thị vị trí trạm, vị trí người gặp nạn và tuyến đường cứu hộ trên bản đồ |
| Theo dõi trạng thái  | Theo dõi yêu cầu từ lúc chờ tiếp nhận đến khi hoàn thành hoặc hủy            |
| Thống kê hệ thống    | Thống kê số trạm, số yêu cầu đang xử lý và số yêu cầu đã hoàn thành          |
| Trợ lý sơ cứu AI     | Nhận mô tả triệu chứng hoặc ảnh vết thương và trả về hướng dẫn sơ cứu        |
| Phân tích ảnh        | Sử dụng OpenCV để hỗ trợ xử lý ảnh vết thương người dùng tải lên             |

> **Cảnh báo:** Chức năng trợ lý sơ cứu chỉ cung cấp thông tin hỗ trợ ban đầu, không thay thế bác sĩ hoặc nhân viên y tế. Trong tình huống nguy hiểm, cần gọi ngay số cấp cứu `115`.

---

## 🛠️ Yêu cầu phần cứng và phần mềm

| Thành phần       | Yêu cầu                                         |
| ---------------- | ----------------------------------------------- |
| Hệ điều hành     | Windows 10/11                                   |
| CPU              | Intel Core i3 trở lên hoặc tương đương          |
| RAM              | Tối thiểu 4 GB                                  |
| Python           | Python 3.10 – 3.12, khuyến nghị Python 3.12     |
| Editor           | Visual Studio Code                              |
| Trình duyệt      | Google Chrome hoặc Microsoft Edge               |
| Kết nối Internet | Cần thiết để tải bản đồ và sử dụng dịch vụ OSRM |
| Git              | Dùng để tải và cập nhật mã nguồn                |
| OpenCV           | Dùng để hỗ trợ xử lý ảnh trong chức năng sơ cứu |
| Pillow           | Hỗ trợ đọc và lưu ảnh tải lên                   |
| NumPy            | Hỗ trợ xử lý dữ liệu ảnh                        |

> **Lưu ý:** Dự án không bắt buộc phải sử dụng InsightFace, ONNX Runtime, CUDA hoặc GPU NVIDIA. OpenCV có thể chạy bằng CPU.

---

# ⚙️ Hướng dẫn cài đặt môi trường

## Bước 1 — Tải hoặc cập nhật dự án

Nếu máy đã có dự án, mở Terminal trong Visual Studio Code và chạy:

```bash
git pull
```

Nếu máy chưa có dự án, chạy:

```bash
git clone <đường-dẫn-repository>
```

Sau đó mở thư mục dự án vừa tải về.

---

## Bước 2 — Di chuyển đến thư mục chứa `manage.py`

```bash
cd django_app
```

Nếu Terminal đã đứng tại thư mục chứa file `manage.py` thì không cần chạy lệnh này.

---

## Bước 3 — Tạo môi trường ảo

Chỉ cần thực hiện trong lần cài đặt đầu tiên:

```bash
python -m venv venv
```

---

## Bước 4 — Kích hoạt môi trường ảo

### Windows Command Prompt

```cmd
venv\Scripts\activate
```

### Windows PowerShell

Nếu PowerShell chặn quyền chạy script, chạy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Khi môi trường ảo được kích hoạt thành công, Terminal sẽ hiển thị `(venv)` ở đầu dòng lệnh.

---

## Bước 5 — Nâng cấp `pip`

```bash
python -m pip install --upgrade pip
```

---

## Bước 6 — Cài đặt các thư viện cần thiết

Khuyến nghị cài đặt từ file `requirements.txt`:

```bash
pip install -r requirements.txt
```

Nếu chưa có file `requirements.txt`, có thể cài thủ công:

```bash
pip install Django Pillow python-dotenv opencv-python numpy
```

Kiểm tra Django đã được cài đặt thành công:

```bash
python -m django --version
```

---

## Bước 7 — Cập nhật cơ sở dữ liệu

```bash
python manage.py migrate
```

Chỉ khi có chỉnh sửa cấu trúc trong file `models.py`, chạy:

```bash
python manage.py makemigrations
python manage.py migrate
```

> Khi chỉ chạy `git pull` và dự án đã có sẵn các file migration thì không cần chạy `makemigrations`.

---

## Bước 8 — Tạo dữ liệu cứu hộ mẫu

Bước này không bắt buộc. Chỉ thực hiện khi cần dữ liệu để kiểm thử hoặc trình diễn:

```bash
python manage.py create_demo_rescue_data
```

Lệnh trên sẽ tạo:

* Các trạm cứu hộ mẫu.
* Các yêu cầu cứu hộ mẫu.
* Vị trí và trạng thái ban đầu để kiểm thử hệ thống.

---

# 📁 Cấu trúc thư mục

```text
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
│       ├── rescue_map.html
│       └── first_aid.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
```

---

# 🚀 Cách sử dụng

## Bước 1 — Kích hoạt môi trường ảo

```bash
venv\Scripts\activate
```

Nếu sử dụng PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

## Bước 2 — Cập nhật mã nguồn mới nhất

```bash
git pull
```

Có thể bỏ qua bước này nếu không cần cập nhật mã nguồn từ Git.

## Bước 3 — Cập nhật cơ sở dữ liệu

```bash
python manage.py migrate
```

## Bước 4 — Khởi chạy chương trình

```bash
python manage.py runserver
```

Sau khi server chạy thành công, Terminal sẽ hiển thị:

```text
Starting development server at http://127.0.0.1:8000/
```

---

# 🌐 Các địa chỉ truy cập

| Trang                     | URL                                      |
| ------------------------- | ---------------------------------------- |
| Trang gửi yêu cầu cứu hộ  | `http://127.0.0.1:8000/`                 |
| Trung tâm điều phối       | `http://127.0.0.1:8000/admin-dashboard/` |
| Bản đồ điều phối cứu hộ   | `http://127.0.0.1:8000/rescue-map/`      |
| Trợ lý Sơ cứu Khẩn cấp AI | `http://127.0.0.1:8000/first-aid/`       |
| Trang quản trị Django     | `http://127.0.0.1:8000/admin/`           |

---

# 🧭 Quy trình điều phối cứu hộ

```text
1. Người dùng truy cập trang gửi yêu cầu cứu hộ
        |
        v
2. Xác định vị trí bằng GPS, bản đồ hoặc địa chỉ ô 3 từ
        |
        v
3. Nhập thông tin cá nhân và mô tả sự cố
        |
        v
4. Yêu cầu được lưu ở trạng thái pending
        |
        v
5. Điều phối viên truy cập trung tâm điều phối
        |
        v
6. Điều phối viên nhấn nút "Điều phối A*"
        |
        v
7. Hệ thống kiểm tra các trạm còn phương tiện
        |
        v
8. OSRM tính quãng đường và thời gian di chuyển thực tế
        |
        v
9. Hệ thống lựa chọn trạm phù hợp
        |
        v
10. Tuyến đường cứu hộ được hiển thị trên bản đồ
        |
        v
11. Điều phối viên cập nhật trạng thái đến khi hoàn thành
```

---

# 🩹 Quy trình sử dụng Trợ lý Sơ cứu AI

```text
1. Người dùng truy cập trang Trợ lý Sơ cứu Khẩn cấp AI
        |
        v
2. Nhập triệu chứng hoặc mô tả sự cố
        |
        |---- Hoặc tải ảnh chụp vết thương
        |
        v
3. Nhấn nút "Phân tích & Tìm kiếm hướng dẫn"
        |
        v
4. Hệ thống xử lý nội dung văn bản hoặc hình ảnh
        |
        v
5. OpenCV hỗ trợ xử lý ảnh nếu người dùng tải ảnh
        |
        v
6. Hệ thống tìm kiếm dữ liệu hướng dẫn sơ cứu
        |
        v
7. Hiển thị tình huống và các bước sơ cứu phù hợp
```

## Chức năng của Trợ lý Sơ cứu AI

* Nhập triệu chứng hoặc mô tả sự cố bằng văn bản.
* Tải ảnh chụp vết thương từ máy tính.
* Phân tích ảnh bằng OpenCV.
* Tìm kiếm hướng dẫn trong cơ sở dữ liệu sơ cứu.
* Hiển thị từng bước thực hiện.
* Hiển thị ảnh minh họa nếu có.
* Thông báo lỗi khi không tìm thấy hướng dẫn phù hợp.

---

# 📌 Trạng thái yêu cầu cứu hộ

| Trạng thái   | Ý nghĩa                |
| ------------ | ---------------------- |
| `pending`    | Đang chờ tiếp nhận     |
| `assigned`   | Đã phân công trạm      |
| `on_the_way` | Đang trên đường cứu hộ |
| `completed`  | Đã hoàn thành          |
| `cancelled`  | Đã hủy                 |

---

# 🚑 Trạng thái trạm cứu hộ

| Trạng thái  | Ý nghĩa                         |
| ----------- | ------------------------------- |
| `available` | Trạm đang sẵn sàng              |
| `busy`      | Trạm đã sử dụng hết phương tiện |
| `inactive`  | Trạm tạm ngừng hoạt động        |

Số phương tiện còn trống được tính theo công thức:

```text
Số xe còn trống = Tổng số xe - Số yêu cầu đang thực hiện
```

---

# ✅ Kiểm tra hệ thống hoạt động

## Kiểm tra cấu hình Django

```bash
python manage.py check
```

Kết quả mong đợi:

```text
System check identified no issues (0 silenced).
```

## Kiểm tra danh sách trạm cứu hộ

```text
http://127.0.0.1:8000/api/rescue-stations/
```

## Kiểm tra thống kê hệ thống

```text
http://127.0.0.1:8000/api/stats/
```

## Kiểm tra dữ liệu bản đồ

```text
http://127.0.0.1:8000/api/custom-map/data/
```

## Kiểm tra giao diện Trợ lý Sơ cứu AI

```text
http://127.0.0.1:8000/first-aid/
```

---

# 🔁 Các lệnh sử dụng trong những lần chạy sau

```bash
venv\Scripts\activate
git pull
python manage.py migrate
python manage.py runserver
```

Nếu không cần cập nhật mã nguồn từ Git, có thể bỏ qua:

```bash
git pull
```

---

# ⏹️ Dừng chương trình

Tại Terminal đang chạy Django Server, nhấn:

```text
Ctrl + C
```

Thoát môi trường ảo:

```bash
deactivate
```

---

# 📝 Lưu ý khi đưa dự án lên Git

## Không nên push các file và thư mục sau

```text
venv/
__pycache__/
*.pyc
.env
.vscode/
.idea/
db.sqlite3
```

Nên thêm các mục trên vào file `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]

# Virtual environment
venv/
.venv/

# Environment variables
.env

# Database
db.sqlite3

# Editors
.vscode/
.idea/

# Operating system
.DS_Store
Thumbs.db
```

## Cần push các thành phần sau

```text
manage.py
requirements.txt
attendance_system/
portal/
portal/migrations/
portal/management/commands/
templates/
static/
README.md
.gitignore
```

---

# 👥 Hướng dẫn dành cho thành viên trong nhóm

Sau khi clone dự án, thành viên trong nhóm chạy:

```bash
cd django_app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_demo_rescue_data
python manage.py runserver
```

Sau đó truy cập:

```text
http://127.0.0.1:8000/
```

> Lệnh `python manage.py create_demo_rescue_data` chỉ cần chạy khi cơ sở dữ liệu chưa có dữ liệu mẫu.
> ::: 
