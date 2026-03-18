"""
normalize_product_images.py
Kiểm tra tất cả image_url trong DB, đánh dấu URL hỏng, thử lấy URL dự phòng.
Chạy: cd backend && python normalize_product_images.py
"""
import sqlite3, os, requests, json
from urllib.parse import urlparse

# === SỬA CHO ĐÚNG VỚI DB THỰC TẾ (Đã kiểm tra cấu trúc dự án) ===
DB_PATH      = "../database/database_v2.db"
TABLE        = "products"
ID_COL       = "id"
NAME_COL     = "name"
IMAGE_COL    = "image_url"
SHOPEE_COL   = "shopee_url"
CATEGORY_COL = "category_label" # DB của bạn dùng category_label cho text
# =====================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://shopee.vn/",
}

def check_image_url(url: str) -> tuple[bool, int]:
    """Kiểm tra URL có trả về ảnh hợp lệ không. Trả (ok, size_bytes)."""
    if not url or not url.strip().startswith("http"):
        return False, 0
    try:
        resp = requests.get(url.strip(), timeout=10, headers=HEADERS, allow_redirects=True)
        ct   = resp.headers.get("Content-Type", "")
        size = len(resp.content)
        ok   = resp.status_code == 200 and ("image" in ct) and size > 5000
        return ok, size
    except Exception:
        return False, 0


def extract_shopee_image_from_url(shopee_url: str) -> str | None:
    """
    Thử trích xuất URL ảnh từ link Shopee.
    Shopee URL dạng: https://shopee.vn/product-name-i.SHOPID.ITEMID
    Ảnh CDN Shopee dạng: https://cf.shopee.vn/file/HASH
    """
    if not shopee_url:
        return None
    # Nếu shopee_url đã là URL ảnh CDN
    if "cf.shopee" in shopee_url or "shopee_vn" in shopee_url:
        return shopee_url
    return None  # Không thể trích xuất tự động


def main():
    db_relative_path = os.path.join(os.path.dirname(__file__), DB_PATH)
    db_path = os.path.abspath(db_relative_path)
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    cur.execute(f"SELECT {ID_COL}, {NAME_COL}, {IMAGE_COL}, {SHOPEE_COL}, {CATEGORY_COL} FROM {TABLE}")
    rows = cur.fetchall()

    print(f"Tổng sản phẩm: {len(rows)}")
    print("=" * 80)

    stats = {"ok": 0, "fixed": 0, "empty": 0, "broken": 0}
    broken_ids = []

    for row in rows:
        pid      = row[ID_COL]
        name     = (row[NAME_COL] or "")[:45]
        img_url  = row[IMAGE_COL] or ""
        shop_url = row[SHOPEE_COL] or ""
        category = row[CATEGORY_COL] or ""

        # Trường hợp 1: image_url rỗng
        if not img_url.strip():
            # Thử lấy từ shopee_url
            alt = extract_shopee_image_from_url(shop_url)
            if alt:
                ok, size = check_image_url(alt)
                if ok:
                    cur.execute(f"UPDATE {TABLE} SET {IMAGE_COL}=? WHERE {ID_COL}=?", (alt, pid))
                    conn.commit()
                    print(f"[FIXED-EMPTY] ID={pid:4d} | {name} | → {alt[:60]}")
                    stats["fixed"] += 1
                    continue
            print(f"[EMPTY      ] ID={pid:4d} | {name} | Không có ảnh")
            stats["empty"] += 1
            broken_ids.append(pid)
            continue

        # Trường hợp 2: image_url có giá trị, kiểm tra
        ok, size = check_image_url(img_url)
        if ok:
            print(f"[OK   {size//1024:4d}KB] ID={pid:4d} | {name} | {img_url[:60]}")
            stats["ok"] += 1
        else:
            # Thử URL dự phòng từ shopee_url
            alt = extract_shopee_image_from_url(shop_url)
            if alt and alt != img_url:
                alt_ok, alt_size = check_image_url(alt)
                if alt_ok:
                    cur.execute(f"UPDATE {TABLE} SET {IMAGE_COL}=? WHERE {ID_COL}=?", (alt, pid))
                    conn.commit()
                    print(f"[FIXED-BROKEN] ID={pid:4d} | {name} | {img_url[:40]} → {alt[:40]}")
                    stats["fixed"] += 1
                    continue

            print(f"[BROKEN     ] ID={pid:4d} | {name} | {img_url[:60]}")
            stats["broken"] += 1
            broken_ids.append(pid)

    conn.close()
    print("\n" + "=" * 80)
    print(f"OK: {stats['ok']} | Fixed: {stats['fixed']} | Empty: {stats['empty']} | Broken: {stats['broken']}")
    if broken_ids:
        print(f"\nSản phẩm cần cập nhật ảnh thủ công (ID): {broken_ids}")
        print("→ Admin vào Outfit & Product và cập nhật image_url cho các ID này")

if __name__ == "__main__":
    main()
