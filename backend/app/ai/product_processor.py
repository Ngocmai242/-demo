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
_rembg_session = None

def get_yolo_model():
    global _model
    if _model is None:
        _model = YOLO('yolov8n.pt')
    return _model

def get_rembg_session(model_name="u2netp"):
    """
    u2netp: nhanh, nhẹ (default)
    u2net_cloth_seg: chuyên dụng cho quần áo (FASHN VTON recommend)
    """
    global _rembg_session
    try:
        # Nếu model_name là cloth_seg, chúng ta khởi tạo session riêng
        return new_session(model_name)
    except Exception:
        return None

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

def extract_main_product(input_path, output_path=None, model_name="u2netp"):
    """
    Tách nền và cắt lấy sản phẩm chính. 
    Sử dụng model_name="u2net_cloth_seg" để tách quần áo khỏi người.
    """
    try:
        img = Image.open(input_path).convert("RGB")
        
        # Determine session
        session = get_rembg_session(model_name)
        
        # Xóa nền
        if session:
            img_nobg = remove(img, session=session)
        else:
            img_nobg = remove(img)
            
        # Tạo mask từ kênh alpha
        alpha = np.array(img_nobg)[:, :, 3]
        
        # Tìm contours để crop sát
        contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(main_contour)
            # Thêm padding nhẹ
            pad = 20
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(img_nobg.width - x, w + 2 * pad)
            h = min(img_nobg.height - y, h + 2 * pad)
            cropped = img_nobg.crop((x, y, x+w, y+h))
        else:
            cropped = img_nobg

        if output_path:
            ext = os.path.splitext(output_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                background = Image.new("RGB", cropped.size, (255, 255, 255))
                background.paste(cropped, mask=cropped.split()[3])
                background.save(output_path, "JPEG", quality=95)
            else:
                cropped.save(output_path, format='PNG')
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
        return extract_main_product(input_path, res, model_name="u2netp")

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
        cropped_region.save(temp_path)

        final_filename = f"product_{i}_{temp_id}.png"
        final_path = os.path.join(output_dir, final_filename)
        # Với crop chứa người, dùng cloth_seg
        extract_main_product(temp_path, final_path, model_name="u2net_cloth_seg")

        if os.path.exists(temp_path):
            os.remove(temp_path)
        processed_paths.append(final_path)

    return processed_paths

