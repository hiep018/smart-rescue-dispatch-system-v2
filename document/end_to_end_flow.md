# Sơ đồ End-to-End: Hệ Thống Điều Phối Cứu Hộ Thông Minh

Dưới đây là sơ đồ luồng hoạt động (End-to-End Flow) của hệ thống điều phối cứu hộ. Sơ đồ được biểu diễn dưới hai dạng: Flowchart (Sơ đồ khối) và Sequence Diagram (Sơ đồ tuần tự).

## 1. Flowchart (Sơ đồ khối)
Sơ đồ này thể hiện các bước nối tiếp nhau trong hệ thống theo từng giai đoạn.

```mermaid
graph TD
    %% Định nghĩa các Actor
    subgraph Người Dùng
        A[Truy cập trang yêu cầu cứu hộ]
        B[Xác định vị trí <br> GPS / Bản đồ / Địa chỉ 3 từ]
        C[Nhập thông tin cá nhân & mô tả sự cố]
    end

    subgraph Hệ Thống
        D[Lưu yêu cầu <br> Trạng thái: Pending]
        G[Lọc các trạm cứu hộ <br> còn phương tiện]
        H[OSRM API: Tính toán quãng đường <br> & thời gian thực tế]
        I[Thuật toán A*: Lựa chọn <br> trạm phù hợp nhất]
        J[Hiển thị tuyến đường <br> trên bản đồ]
    end

    subgraph Điều Phối Viên
        E[Truy cập trung tâm điều phối]
        F[Nhấn nút 'Điều phối A*']
        K[Cập nhật trạng thái <br> -> Completed]
    end

    %% Flow
    A --> B
    B --> C
    C --> D
    
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K

    %% Đổi màu sắc cho dễ nhìn
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;
    classDef system fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000;
    classDef admin fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    
    class A,B,C user;
    class D,G,H,I,J system;
    class E,F,K admin;
```

## 2. Sequence Diagram (Sơ đồ tuần tự)
Sơ đồ này thể hiện sự tương tác giữa các tác nhân (Người Dùng, Hệ Thống, Điều Phối Viên, và OSRM API) theo trình tự thời gian.

```mermaid
sequenceDiagram
    autonumber
    actor U as Người Dùng
    participant S as Hệ Thống
    actor D as Điều Phối Viên
    participant O as OSRM API

    U->>S: Truy cập trang yêu cầu cứu hộ
    U->>S: Cung cấp vị trí (GPS/Bản đồ/What3Words)
    U->>S: Gửi thông tin cá nhân & sự cố
    S-->>S: Lưu yêu cầu (Trạng thái: pending)
    
    Note over D, S: Giai đoạn Điều phối
    
    D->>S: Truy cập trung tâm điều phối
    D->>S: Chọn yêu cầu & Nhấn nút "Điều phối A*"
    
    S->>S: Lọc danh sách trạm còn phương tiện
    S->>O: Gửi tọa độ người gặp nạn & các trạm
    O-->>S: Trả về khoảng cách & thời gian đi đường
    S->>S: Áp dụng thuật toán A* chọn trạm tối ưu nhất
    
    S-->>D: Hiển thị trạm được chọn & tuyến đường trên bản đồ
    
    Note over D, S: Giai đoạn Hoàn thành
    D->>S: Cập nhật trạng thái yêu cầu (completed)
```
