import os
import sqlite3
import requests
import shutil
import uuid
from PIL import Image
from io import BytesIO

# Import the new smart processor
try:
    from .app.ai.product_processor import extract_main_product, split_multi_product_image
except ImportError:
    # Handle if run directly or as a script
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.app.ai.product_processor import extract_main_product, split_multi_product_image

def clean_product_image(image_url, item_id, output_dir):
    """
    Downloads image from image_url and uses the AI Processor to clean and crop it.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"{item_id}.png"
    file_path = os.path.join(output_dir, file_name)
    
    # Temp path for the raw download
    raw_path = os.path.join(output_dir, f"raw_{item_id}.jpg")
    
    try:
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://shopee.vn/'
        }
        response = requests.get(image_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[Cleaner] Failed to download {image_url}: {response.status_code}")
            return None
            
        with open(raw_path, "wb") as f:
            f.write(response.content)

        # Use the Smart Processor with u2net_cloth_seg to detach clothing from people
        print(f"[Cleaner] AI cleaning image for {item_id} (using cloth_seg)...")
        res_path = extract_main_product(raw_path, file_path, model_name="u2net_cloth_seg")
        
        # Cleanup raw
        if os.path.exists(raw_path):
            os.remove(raw_path)
            
        if res_path and os.path.exists(res_path):
            # Return path relative to static root for frontend
            return f"static/clean_images/{file_name}"
        return None
        
    except Exception as e:
        print(f"[Cleaner] Error cleaning {item_id}: {e}")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        return None

def batch_clean_from_db(db_path, limit=100, overwrite=False):
    """
    Quét DB, tải và làm sạch ảnh cho các sản phẩm chưa có clean_image_path.
    """
    if not os.path.exists(db_path):
        print(f"[Cleaner] DB not found: {db_path}")
        return 0
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Query các item cần xử lý
    query = "SELECT id, item_id, image_url FROM products"
    conditions = []
    if not overwrite:
        conditions.append("(clean_image_path IS NULL OR clean_image_path = '')")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += f" LIMIT {limit}"
    
    rows = cur.execute(query).fetchall()
    if not rows:
        conn.close()
        return 0
        
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SAVE_DIR = os.path.join(BASE_DIR, "frontend", "static", "clean_images")
    output_dir = SAVE_DIR
    
    print(f"[Cleaner] Processing {len(rows)} images with YOLO+Rembg...")
    success_count = 0
    
    for i, row in enumerate(rows):
        cid = row['id']
        item_id = row['item_id']
        url = row['image_url']
        
        if not url: continue
        
        clean_path = clean_product_image(url, item_id, output_dir)
        if clean_path:
            cur.execute("UPDATE products SET clean_image_path = ? WHERE id = ?", (clean_path, cid))
            success_count += 1
            
        if (i + 1) % 10 == 0: # Commit more frequently as YOLO/rembg are heavy
            conn.commit()
            print(f"[Cleaner] Handled {i+1}/{len(rows)}...")
            
    conn.commit()
    conn.close()
    print(f"[Cleaner] Finished. Cleaned {success_count} images.")
    return success_count

if __name__ == "__main__":
    # Test script
    import sys
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "database_v2.db"))
    batch_clean_from_db(db_file, limit=5)
