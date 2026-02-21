
import asyncio
import re
import logging
import json
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from data_engine.feature_engine import FeatureExtractor

# Setup logging
logger = logging.getLogger("shopee_ultimate_v26")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(ch)

async def _crawl_main(url: str, limit: int = 50) -> List[Dict]:
    """Phiên bản v26 (Ultimate AI Stabilized): Googlebot Stealth + DOM Scraper + AI Normalization"""
    if "shopee.vn/" in url:
        username = url.split("shopee.vn/")[-1].split("?")[0].split("/")[0]
    else:
        username = url
    
    target_url = f"https://shopee.vn/{username}?page_type=shop"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # CHIẾN THUẬT: Giả danh Googlebot để Shopee không yêu cầu Đăng nhập (Anti-crawl 2026 Fix)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            viewport={'width': 1280, 'height': 3000}
        )
        
        page = await context.new_page()
        logger.info(f"🕵️ Khởi động Crawler v26 (Ultimate). Mục tiêu: {username}")
        
        try:
            # 1. Truy cập trang shop
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # Xóa các thành phần HTML cản trở
            await page.evaluate("""() => {
                const selectors = ['.shopee-popup', '.shopee-modal', '.language-selection-popup', '.st-popup'];
                selectors.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
            }""")

            # 2. Cuộn trang để kích hoạt Lazy Load (Cần thiết để lấy đủ sản phẩm)
            logger.info("📜 Đang cuộn trang để tải thêm sản phẩm...")
            for _ in range(2):
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)
            
            # 3. TRÍCH XUẤT DỮ LIỆU TỪ DOM (Bypass all API Blocks 903/403)
            # Selector a[href*='-i.'] là cực kỳ ổn định để lấy ItemID và ShopID
            logger.info("🔍 Đang trích xuất dữ liệu sản phẩm từ giao diện...")
            product_elements = await page.query_selector_all("a[href*='-i.']")
            
            if not product_elements:
                logger.error("🛑 Không tìm thấy sản phẩm. Có thể ShopId hoặc Username không đúng.")
                return []

            logger.info(f"📊 Tìm thấy {len(product_elements)} sản phẩm. Đang chuẩn hóa cho AI...")

            for el in product_elements[:limit]:
                try:
                    # Lấy text thô chứa Tên và Giá
                    text_content = await el.inner_text()
                    href = await el.get_attribute("href")
                    
                    if not text_content or not href: continue
                    
                    # Split text to find name and price
                    lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                    if len(lines) < 2: continue
                    
                    name = lines[0] # Tên sản phẩm thường là dòng đầu tiên
                    
                    # Tìm dòng chứa giá (có ký hiệu ₫ hoặc số có dấu chấm)
                    price_val = 0
                    for line in lines[1:]:
                        if "₫" in line or (re.search(r'[\d\.]+', line) and len(line) > 3):
                            p_clean = re.sub(r'[^\d]', '', line)
                            if p_clean:
                                price_val = float(p_clean)
                                break
                    
                    if price_val == 0: continue
                    
                    # Ảnh (Lấy từ thẻ img bên trong)
                    img_el = await el.query_selector("img")
                    img_url = await img_el.get_attribute("src") if img_el else ""
                    
                    # IIDs (Bóc tách từ link: /Product-Name-i.SHOPID.ITEMID)
                    id_match = re.search(r'i\.(\d+)\.(\d+)', href)
                    sid = id_match.group(1) if id_match else "0"
                    iid = id_match.group(2) if id_match else "0"

                    # --- CHUẨN HÓA DỮ LIỆU AI THEO YÊU CẦU ---
                    # Theo quy trình: Thu thập -> Xử lý (Giá / 100k) -> AI Mapping
                    
                    # price_min_real là giá trị thực tế (VD: 154000)
                    price_min_real = price_val
                    
                    # AI Mapping (Xử lý "Other" và gán nhãn phối đồ)
                    # FeatureExtractor sẽ tự động quét keywords trong tên để gán category
                    ai_data = FeatureExtractor.extract(name, "")
                    
                    results.append({
                        "itemid": iid,
                        "shopid": sid,
                        "name": name,
                        "image": img_url,
                        "url": f"https://shopee.vn{href}" if href.startswith('/') else href,
                        "price_min": price_min_real * 100000, # Giả lập Shopee Raw cho công thức User
                        "price_max": price_min_real * 100000,
                        "price_min_real": price_min_real,
                        "price_max_real": price_min_real,
                        "ai_category": ai_data.get("category"),
                        "item_type": ai_data.get("item_type"),
                        "gender": ai_data.get("gender"),
                        "material": ai_data.get("material"),
                        "style": ai_data.get("style"),
                        "details": f"{price_min_real:,.0f}đ | {ai_data.get('category')}"
                    })
                except Exception as e:
                    continue

            logger.info(f"✅ Hoàn tất! Lấy thành công {len(results)} sản phẩm cho shop {username}.")

        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình crawl: {e}")
        finally:
            await browser.close()
            
    return results

def crawl_shop_url(url: str, limit: int = 50) -> List[Dict]:
    """Hàm wrapper đồng bộ để gọi từ các module khác."""
    try:
        return asyncio.run(_crawl_main(url, limit))
    except Exception as e:
        logger.error(f"Lỗi khởi chạy Crawler: {e}")
        return []

if __name__ == "__main__":
    import sys
    # Reconfigure stdout for UTF-8 to display Vietnamese correctly in terminal
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    
    # Chạy thử với link yêu cầu
    test_url = "https://shopee.vn/vierlin"
    res = crawl_shop_url(test_url, 20)
    
    print("\n--- KẾT QUẢ CRAWL (Sẵn sàng cho AI Training) ---")
    for p in res:
        print(f"[{p['ai_category']}] {p['name']} - Giá: {p['price_min_real']:,.0f}đ")