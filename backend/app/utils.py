import os
import uuid
import requests as _req
from flask import current_app

def download_garment_image(image_url: str, shopee_url: str):
    """
    Download hoặc lấy ảnh garment từ local. Thử image_url trước, nếu lỗi thử shopee_url.
    Trả về đường dẫn file local (tuyệt đối), hoặc None nếu hoàn toàn thất bại.
    """
    save_dir = os.path.join(current_app.static_folder, 'uploads', 'tryon')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    os.makedirs(save_dir, exist_ok=True)

    # TRƯỜNG HỢP 1: image_url là đường dẫn nội bộ (bắt đầu bằng /)
    if image_url and image_url.startswith("/"):
        # Chuyển đổi từ /uploads/abc.png thành đường dẫn tuyệt đối trên đĩa
        # Lưu ý: current_app.static_folder trỏ đến thư mục 'frontend'
        local_path = os.path.join(current_app.static_folder, image_url.lstrip("/"))
        if os.path.exists(local_path):
            # Tạo một bản copy vào thư mục tryon để xử lý, tránh ghi đè ảnh gốc
            ext = os.path.splitext(local_path)[1] or ".png"
            new_path = os.path.join(save_dir, f"garment_{uuid.uuid4().hex}{ext}")
            import shutil
            shutil.copy(local_path, new_path)
            return new_path

    # TRƯỜNG HỢP 2: image_url là URL từ Shopee/Lazada hoặc nguồn bên ngoài
    urls_to_try = []
    if image_url and image_url.startswith("http"):
        urls_to_try.append(image_url)
    if shopee_url and shopee_url.startswith("http"):
        urls_to_try.append(shopee_url)

    for url in urls_to_try:
        try:
            resp = _req.get(url, timeout=12, headers=headers, allow_redirects=True)
            ct   = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and len(resp.content) > 1000 and "image" in ct:
                ext = ".jpg"
                if "png" in ct:  ext = ".png"
                if "webp" in ct: ext = ".webp"
                filename = f"garment_{uuid.uuid4().hex}{ext}"
                path = os.path.join(save_dir, filename)
                
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception:
            continue
    return None
