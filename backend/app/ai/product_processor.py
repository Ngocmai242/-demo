# backend/app/ai/product_processor.py
import os
import cv2
import numpy as np
import uuid
import shutil
from PIL import Image
from rembg import remove, new_session
from ultralytics import YOLO

# Tải model YOLOv8 pre-trained (sử dụng bản nano để nhanh và nhẹ)
_model = None
# Cache cho các rembg session khác nhau
_rembg_sessions = {}

def get_yolo_model():
    global _model
    if _model is None:
        _model = YOLO('yolov8n.pt')
    return _model

def get_rembg_session(model_name="isnet-general-use"):
    """
    isnet-general-use: SOTA cho tách nền cực chuẩn (không dính rác, text).
    isnet-general-use: Chuẩn hơn u2netp.
    u2net_cloth_seg: chuyên dụng cho quần áo có người mặc.
    """
    global _rembg_sessions
    if model_name not in _rembg_sessions:
        try:
            print(f"[Rembg] Initializing session for {model_name}...")
            _rembg_sessions[model_name] = new_session(model_name)
        except Exception as e:
            print(f"[Rembg] Failed to init session {model_name}: {e}")
            return None
    return _rembg_sessions[model_name]

def detect_products(image_path):
    """Phát hiện các vật thể trong ảnh bằng YOLOv8."""
    try:
        model = get_yolo_model()
        results = model(image_path, verbose=False)
        boxes = []
        for r in results:
            for box in r.boxes:
                # person: 0, tie: 27, handbag: 26 (COCO)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                if conf > 0.4:
                    boxes.append((int(x1), int(y1), int(x2), int(y2), cls))
        return boxes
    except Exception as e:
        print(f"[YOLO] Error: {e}")
        return []

def extract_main_product(input_path, output_path=None, model_name="u2net_cloth_seg"):
    """
    Tách nền và cắt lấy sản phẩm chính. 
    Sử dụng model_name="u2net_cloth_seg" để tách quần áo khỏi người.
    """
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # Determine session
        session = get_rembg_session(model_name)
        
        # Xóa nền
        session = get_rembg_session(model_name)
        
        # Thử với model chỉ định
        try:
            if session:
                img_nobg = remove(img, session=session)
            else:
                img_nobg = remove(img)
        except Exception as e:
            print(f"[Processor] Primary segmentation failed: {e}. Falling back to default.")
            # Fallback sang model mặc định phổ biến isnet-general-use
            default_session = get_rembg_session("isnet-general-use")
            img_nobg = remove(img, session=default_session) if default_session else remove(img)
            
        # --- CẢI TIẾN: Sửa lỗi áo màu Caro/Plaid bị AI phân mảnh ---
        # Chuyển sang numpy để xử lý OpenCV
        img_np = np.array(img_nobg)
        alpha = img_np[:, :, 3]
        
        # Binary alpha để tính toán hình học chính xác
        _, binary_alpha = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        
        # Tạo kernel động nở rộng (Dilation) dựa trên kích thước ảnh (~4% kích thước max)
        # Việc nở rộng (Dilate) sẽ nối tất cả các mảnh vụn của cùng 1 áo bị AI cắt hỏng thành 1 khối duy nhất!
        img_h, img_w = binary_alpha.shape
        k_size = int(max(img_w, img_h) * 0.04)
        if k_size % 2 == 0: k_size += 1
        if k_size < 11: k_size = 11
        
        dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        bloated_mask = cv2.dilate(binary_alpha, dilation_kernel, iterations=1)
        
        # Tìm contours trên khối đã được nở rộng kết dính
        contours, _ = cv2.findContours(bloated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Lấy contour LỚN NHẤT (Khối sản phẩm chính đã kết dính)
            main_contour = max(contours, key=cv2.contourArea)
            
            # --- TÁCH CHUẨN 1 SẢN PHẨM & LOẠI BỎ RÁC ---
            # Vẽ khối sản phẩm chính lên một mask trắng tinh
            clean_bloated = np.zeros_like(binary_alpha)
            cv2.drawContours(clean_bloated, [main_contour], -1, 255, -1)
            
            # Khôi phục nguyên trạng Alpha ban đầu nhưng CHỈ LẤY những vị trí nằm trong khối sản phẩm chính
            # Qua đó, các dải/mảnh vỡ của áo Caro được cứu sống 100%, trong khi Watermark/Sản phẩm thừa ở xa bị xóa sạch!
            alpha_closed = cv2.bitwise_and(alpha, clean_bloated)
            
            # Tìm lại Contour cuối cùng để tính toán Bounding Box chính xác cho việc Crop
            final_contours, _ = cv2.findContours(alpha_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if final_contours:
                final_main_contour = max(final_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(final_main_contour)
            else:
                x, y, w, h = 0, 0, img_w, img_h
            
            # 3. Tính toán padding thông minh (15% thay vì 10% để tránh mất góc)
            max_dim = max(w, h)
            pad = int(max_dim * 0.15)
            
            # Crop vùng chứa sản phẩm với padding
            left = max(0, x - pad)
            top = max(0, y - pad)
            right = min(img_nobg.width, x + w + pad)
            bottom = min(img_nobg.height, y + h + pad)
            
            # Áp dụng mask đã được 'lấp đầy' vào ảnh gốc
            img_np[:, :, 3] = alpha_closed
            img_final = Image.fromarray(img_np)
            
            cropped = img_final.crop((left, top, right, bottom))
            
            # --- THÊM: Đưa về ảnh canvas chuẩn (tỷ lệ 3:4 cho VTON) ---
            # Fashn VTON 1.5 thường yêu cầu ảnh tỷ lệ đứng (portrait)
            target_w, target_h = cropped.size
            # Tạo canvas tỷ lệ 3:4
            final_h = target_h + (pad * 2)
            final_w = int(final_h * 0.75)
            
            if target_w > final_w:
                final_w = target_w + (pad * 2)
                final_h = int(final_w / 0.75)

            # Đảm bảo độ phân giải tối thiểu 1024px chiều cao để giữ nét
            if final_h < 1024:
                scale = 1024 / final_h
                new_w = int(target_w * scale)
                new_h = int(target_h * scale)
                # Dùng LANCZOS để giữ nét tối đa khi phóng to
                cropped = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                final_h = 1024
                final_w = int(final_h * 0.75)
                target_w, target_h = new_w, new_h

            canvas = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
            # Dán vào chính giữa
            offset = ((final_w - target_w) // 2, (final_h - target_h) // 2)
            canvas.paste(cropped, offset)
            cropped = canvas
        else:
            cropped = img_nobg

        if output_path:
            ext = os.path.splitext(output_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                # Dùng nền trắng cho JPEG, chất lượng tối đa 100
                background = Image.new("RGB", cropped.size, (255, 255, 255))
                background.paste(cropped, mask=cropped.split()[3])
                background.save(output_path, "JPEG", quality=100, subsampling=0)
            else:
                # Dùng PNG lossless, tối ưu hóa dung lượng nhưng giữ nguyên chất lượng
                cropped.save(output_path, format='PNG', optimize=True)
            return output_path
        else:
            return cropped
    except Exception as e:
        print(f"[Processor] Error: {e}")
        if output_path:
            if os.path.exists(input_path):
                shutil.copy(input_path, output_path)
            return output_path
        return Image.open(input_path)

def process_garment_for_vton(input_path, output_dir):
    """
    QUAN TRỌNG: Tách quần áo khỏi người để FASHN VTON hoạt động tốt nhất.
    Sử dụng u2net_cloth_seg.
    """
    os.makedirs(output_dir, exist_ok=True)
    res = os.path.join(output_dir, f"vton_garment_{uuid.uuid4().hex}.png")
    
    # Ưu tiên dùng cloth_seg để tách quần áo khỏi người mặc
    try:
        print(f"[Processor] Using specialized clothing segmentation for {input_path}")
        return extract_main_product(input_path, res, model_name="u2net_cloth_seg")
    except Exception as e:
        print(f"[Processor] Specialized seg failed, falling back to simple remove: {e}")
        return extract_main_product(input_path, res, model_name="isnet-general-use")

def split_multi_product_image(image_path, output_dir):
    """Ảnh grid Shopee thường có nhiều item, cần tách ra."""
    os.makedirs(output_dir, exist_ok=True)
    boxes = detect_products(image_path)
    
    if not boxes:
        out_path = os.path.join(output_dir, f"split_0_{uuid.uuid4().hex}.png")
        return [extract_main_product(image_path, out_path)]

    img = Image.open(image_path).convert("RGB")
    processed_paths = []
    for i, (x1, y1, x2, y2, cls) in enumerate(boxes):
        # class 0 là person, chúng ta muốn lấy vật thể (thường YOLOv8 detect quần áo là vật thể khác)
        # Nếu YOLO chỉ detect person, chúng ta crop person đó.
        cropped_region = img.crop((x1, y1, x2, y2))
        
        temp_id = uuid.uuid4().hex
        temp_path = os.path.join(output_dir, f"temp_{temp_id}.png")
        cropped_region.save(temp_path, optimize=True)

        final_filename = f"product_{i}_{temp_id}.png"
        final_path = os.path.join(output_dir, final_filename)
        # Với crop chứa người, dùng cloth_seg
        extract_main_product(temp_path, final_path, model_name="u2net_cloth_seg")

        if os.path.exists(temp_path):
            os.remove(temp_path)
        processed_paths.append(final_path)

    return processed_paths

