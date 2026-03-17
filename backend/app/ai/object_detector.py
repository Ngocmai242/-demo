# backend/app/ai/object_detector.py
from ultralytics import YOLO
from PIL import Image
import os
import uuid
from .product_processor import extract_main_product

# Load a lightweight segmentation model
# Note: In a real environment, you'd want to download this once and reuse
try:
    model = YOLO('yolov8n-seg.pt') 
except Exception:
    # Fallback if model can't be loaded
    model = None

def detect_and_crop_products(image_path, output_dir):
    """
    Phát hiện các sản phẩm trong ảnh, cắt và xóa nền từng cái.
    Trả về danh sách đường dẫn ảnh đã xử lý.
    """
    if not model:
        print("[Detector] YOLO model not loaded.")
        return []

    os.makedirs(output_dir, exist_ok=True)
    
    try:
        results = model.predict(image_path, conf=0.4)  # detect objects
        boxes = results[0].boxes.xyxy.cpu().numpy()  # tọa độ bounding boxes
        
        cropped_paths = []
        img = Image.open(image_path)
        
        for i, box in enumerate(boxes):
            # Kiểm tra label nếu cần (ví dụ chỉ lấy quần áo)
            # label = results[0].names[int(results[0].boxes.cls[i])]
            
            x1, y1, x2, y2 = map(int, box)
            # Thêm padding cho crop
            pad = 20
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(img.width, x2 + pad)
            y2 = min(img.height, y2 + pad)
            
            cropped = img.crop((x1, y1, x2, y2))
            
            # Lưu tạm để xử lý tách nền
            temp_name = f"temp_crop_{uuid.uuid4().hex}_{i}.png"
            temp_path = os.path.join(output_dir, temp_name)
            cropped.save(temp_path)
            
            # Xóa nền và cắt lấy sản phẩm chính
            final_name = f"final_product_{uuid.uuid4().hex}_{i}.png"
            final_path = os.path.join(output_dir, final_name)
            
            extract_main_product(temp_path, final_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            cropped_paths.append(final_path)
        
        return cropped_paths
    except Exception as e:
        print(f"[Detector] Error detecting objects: {e}")
        return []
