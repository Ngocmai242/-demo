"""
segment_clean_images.py

Mục tiêu:
- Tải ảnh product từ DB (products.image_url)
- Remove background (rembg) -> RGBA
- Tách các item nếu ảnh có nhiều cụm (connected-components trên alpha mask)
- Lưu PNG nền trong suốt vào: frontend/static/clean_images/
- Update products.clean_image_path = "static/clean_images/<item_id>.png" (ưu tiên cụm lớn nhất)

Chạy:
  python data_engine/segment_clean_images.py --limit 200
  python data_engine/segment_clean_images.py --overwrite --limit 50

Ghi chú:
- Script này KHÔNG cần YOLO/Detectron2. Nó dùng rembg + connected components.
- Với ảnh multi-item, nó sẽ chọn item lớn nhất làm "garment" chính để VTON dùng.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from io import BytesIO

import numpy as np
import requests
from PIL import Image

try:
    from rembg import remove as rembg_remove
except Exception as e:  # pragma: no cover
    rembg_remove = None
    _REMBG_ERR = e


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _db_path() -> str:
    return os.path.join(_project_root(), "database", "database_v2.db")


def _out_dir() -> str:
    return os.path.join(_project_root(), "frontend", "static", "clean_images")


def _download(url: str) -> bytes | None:
    if not url or not url.startswith("http"):
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://shopee.vn/",
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 5000:
            return r.content
    except Exception:
        return None
    return None


def _to_rgba_png_bytes(image_bytes: bytes) -> bytes | None:
    if rembg_remove is None:
        raise RuntimeError(f"rembg not available: {_REMBG_ERR}")
    try:
        # rembg returns bytes; ensure it's RGBA PNG
        out = rembg_remove(image_bytes)
        img = Image.open(BytesIO(out)).convert("RGBA")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def _largest_component_bbox(alpha: np.ndarray, min_area: int = 2500) -> tuple[int, int, int, int] | None:
    """
    alpha: HxW uint8
    Returns bbox (x1, y1, x2, y2) of largest connected component in alpha mask.
    """
    mask = alpha > 10
    if mask.sum() < min_area:
        return None

    # connected components using scipy if available, else fallback to simple bbox of all foreground
    try:
        from scipy import ndimage as ndi

        labeled, n = ndi.label(mask)
        if n <= 0:
            return None
        sizes = ndi.sum(mask, labeled, index=range(1, n + 1))
        sizes = np.asarray(sizes)
        best_idx = int(np.argmax(sizes)) + 1
        if sizes[best_idx - 1] < min_area:
            return None
        ys, xs = np.where(labeled == best_idx)
        y1, y2 = int(ys.min()), int(ys.max())
        x1, x2 = int(xs.min()), int(xs.max())
        return x1, y1, x2 + 1, y2 + 1
    except Exception:
        ys, xs = np.where(mask)
        if ys.size == 0:
            return None
        y1, y2 = int(ys.min()), int(ys.max())
        x1, x2 = int(xs.min()), int(xs.max())
        return x1, y1, x2 + 1, y2 + 1


def _crop_with_padding(img: Image.Image, bbox: tuple[int, int, int, int], pad_ratio: float = 0.06) -> Image.Image:
    x1, y1, x2, y2 = bbox
    w, h = img.size
    pad = int(max((x2 - x1), (y2 - y1)) * pad_ratio)
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return img.crop((x1, y1, x2, y2))


def process_one(image_url: str, out_abs_path: str) -> bool:
    raw = _download(image_url)
    if not raw:
        return False
    rgba_png = _to_rgba_png_bytes(raw)
    if not rgba_png:
        return False

    img = Image.open(BytesIO(rgba_png)).convert("RGBA")
    alpha = np.asarray(img.split()[-1])
    bbox = _largest_component_bbox(alpha)
    if bbox:
        img = _crop_with_padding(img, bbox)

    os.makedirs(os.path.dirname(out_abs_path), exist_ok=True)
    img.save(out_abs_path, "PNG")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=_db_path())
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if rembg_remove is None:
        raise SystemExit(f"[SegmentCleaner] rembg import failed: {_REMBG_ERR}\n→ Run: pip install rembg")

    db_path = args.db
    if not os.path.exists(db_path):
        raise SystemExit(f"[SegmentCleaner] DB not found: {db_path}")

    out_dir = _out_dir()
    os.makedirs(out_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    q = "SELECT id, item_id, image_url, clean_image_path FROM products WHERE image_url IS NOT NULL AND image_url != ''"
    if not args.overwrite:
        q += " AND (clean_image_path IS NULL OR clean_image_path = '')"
    q += " LIMIT ?"

    rows = cur.execute(q, (int(args.limit),)).fetchall()
    if not rows:
        print("[SegmentCleaner] Nothing to do.")
        conn.close()
        return

    ok = 0
    for i, r in enumerate(rows, start=1):
        pid = r["id"]
        item_id = str(r["item_id"] or pid)
        url = (r["image_url"] or "").strip()
        out_abs = os.path.join(out_dir, f"{item_id}.png")
        out_rel = f"static/clean_images/{item_id}.png"

        try:
            success = process_one(url, out_abs)
        except Exception as e:
            print(f"[SegmentCleaner] FAIL {item_id}: {type(e).__name__}: {str(e)[:120]}")
            success = False

        if success:
            cur.execute("UPDATE products SET clean_image_path = ? WHERE id = ?", (out_rel, pid))
            ok += 1
            if ok % 20 == 0:
                conn.commit()
            print(f"[SegmentCleaner] OK {i}/{len(rows)} -> {out_rel}")
        else:
            print(f"[SegmentCleaner] SKIP {i}/{len(rows)} {item_id}")

    conn.commit()
    conn.close()
    print(f"[SegmentCleaner] Done. Updated {ok}/{len(rows)} products.")


if __name__ == "__main__":
    main()

