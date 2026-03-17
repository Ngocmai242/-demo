# backend/app/ai/product_processor.py
from rembg import remove
from PIL import Image
import numpy as np
import cv2
import os
import uuid

def extract_main_product(input_path, output_path=None):
    """
    Tách nền và cắt lấy sản phẩm chính từ ảnh.
    Nếu output_path=None, trả về PIL Image; nếu có, lưu vào đường dẫn đó.
    """
    try:
        # Đọc ảnh và xóa nền
        img = Image.open(input_path)
        img_nobg = remove(img)  # Kết quả có kênh alpha

        # Tìm contour lớn nhất (sản phẩm chính)
        # Chuyển ảnh sang OpenCV format (BGR) để tìm contour
        # Chúng ta dùng kênh alpha để tạo mask chính xác
        alpha = np.array(img_nobg)[:, :, 3]
        
        # Tìm contours từ mask alpha
        contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Lấy contour lớn nhất (giả định là sản phẩm chính)
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(main_contour)
            
            # Thêm một chút padding để không bị sát quá
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img_nobg.width - x, w + 2 * padding)
            h = min(img_nobg.height - y, h + 2 * padding)
            
            cropped = img_nobg.crop((x, y, x + w, y + h))
        else:
            cropped = img_nobg  # fallback: giữ nguyên ảnh đã xóa nền

        # Lưu hoặc trả về
        if output_path:
            cropped.save(output_path, format='PNG')
            return output_path
        else:
            return cropped
    except Exception as e:
        print(f"[Processor] Error processing image {input_path}: {e}")
        # Fallback: Trả về ảnh gốc nếu lỗi
        if output_path:
            Image.open(input_path).save(output_path)
            return output_path
        return Image.open(input_path)

def process_garment_for_vton(input_path, output_dir):
    """
    Xử lý ảnh garment trước khi đưa vào VTON: tách nền, crop sản phẩm chính.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"processed_{uuid.uuid4().hex}.png"
    output_path = os.path.join(output_dir, filename)
    return extract_main_product(input_path, output_path)
