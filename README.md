# AI Virtual Fitting & Style Recommendation Platform

Một nền tảng web Full-Stack đơn giản cho phép người dùng thử các trang phục ảo và nhận gợi ý phong cách dựa trên AI. Hệ thống sử dụng Python Flask cho backend và HTML/CSS/JS thuần cho frontend.

## Cấu trúc dự án

```
project/
├── backend/            # Python Flask App
│   ├── app.py          # Server chính
│   ├── requirements.txt # Các thư viện cần thiết
│   └── server_dev.py   # Server cho môi trường dev (auto-reload)
├── frontend/           # Giao diện người dùng
│   ├── index.html      # Trang chủ (Dashboard)
│   ├── login.html      # Trang đăng nhập
│   ├── register.html   # Trang đăng ký
│   ├── style.css       # Style Pastel Minimalism
│   └── script.js       # Logic xử lý gọi API
├── database/           # Chứa cơ sở dữ liệu SQLite
│   └── database_v2.db  # Tự động tạo khi chạy app
├── package.json        # Quản lý script chạy song song (npm start)
└── README.md           # Hướng dẫn sử dụng
```

## Yêu cầu hệ thống

- **Python 3.7+**: Để chạy Backend.
- **Node.js**: Để sử dụng `npm` quản lý các tiến trình song song.

## Hướng dẫn cài đặt và chạy (Khuyên dùng)

Đây là cách hiện đại và tiện lợi nhất, giúp chạy cả Backend và Frontend chỉ với một lệnh duy nhất, hỗ trợ tự động tải lại (auto-reload) khi sửa code.

### 1. Cài đặt

Mở terminal tại thư mục gốc của dự án và chạy các lệnh sau:

```bash
# 1. Cài đặt thư viện Python (Backend)
pip install -r backend/requirements.txt

# 2. Cài đặt thư viện Node.js (để chạy song song)
npm install
```

### 2. Khởi động dự án

Chỉ cần chạy một lệnh duy nhất:

```bash
npm start
```

Lệnh này sẽ:
1.  Khởi động **Backend** (Python Flask) tại `http://localhost:8080`.
    *   *Chế độ Debug được bật: Server sẽ tự động khởi động lại khi bạn sửa code Python.*
2.  **Frontend** được phục vụ trực tiếp bởi Flask (static folder = `frontend/`) tại cùng domain `http://localhost:8080`.
3.  Tự động mở **2 tab**:
    *   User: `http://127.0.0.1:8080/index.html`
    *   Admin: `http://127.0.0.1:8080/admin_login.html`

---

## Hướng dẫn chạy thủ công (Cách cũ)

Nếu bạn không muốn sử dụng Node.js, bạn có thể chạy thủ công từng thành phần:

1.  **Chạy Backend**:
    *   Mở terminal, chạy: `python backend/server.py`
    *   Server chạy tại: `http://localhost:8080`
2.  **Chạy Frontend**:
    *   Truy cập trực tiếp qua Flask:
        - User: `http://127.0.0.1:8080/index.html`
        - Admin: `http://127.0.0.1:8080/admin_login.html`

---

## Virtual Try-On: dùng đúng ảnh crawl (clean PNG)

Để model Try-On dùng đúng ảnh sản phẩm (đặc biệt khi ảnh crawl là ảnh ghép/multi-item hoặc có người mẫu), hãy tạo ảnh **PNG nền trong suốt** và lưu vào `products.clean_image_path`.

### 1) Tạo file `.env` (khuyến nghị)

Tạo `.env` ở thư mục gốc project (cùng cấp `backend/`):

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

### 2) Batch clean/segment ảnh từ DB

Chạy:

```bash
python data_engine/segment_clean_images.py --limit 200
```

Tuỳ chọn:
- `--overwrite`: xử lý lại kể cả khi đã có `clean_image_path`

Ảnh output nằm ở:
- `frontend/static/clean_images/<item_id>.png`

Sau đó endpoint `/api/virtual-tryon` sẽ **ưu tiên dùng `clean_image_path`** làm input garment cho VTON.

## Chức năng

### User Website:
- **Đăng ký/Đăng nhập**: Tạo tài khoản an toàn.
- **AI Try-On**: Giả lập thử đồ.
- **Gợi ý Outfit**: Xem danh sách các bộ đồ được đề xuất.

### Admin Website:
- **Đăng nhập**: Truy cập với tài khoản có quyền Admin.
- **Dashboard**: Quản lý người dùng, sản phẩm.

## Tài khoản Demo
- **User**: Đăng ký mới bất kỳ.
- **Admin**:
    - Username: `admin`
    - Password: `admin`
