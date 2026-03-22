"""
test_fashn.py — test FASHN VTON 1.5
Chạy: cd backend && python test_fashn.py
"""
import os, sys, tempfile, urllib.request
from dotenv import load_dotenv
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")
print(f"HF_TOKEN: {'set ✓' if HF_TOKEN else 'CHƯA SET ✗ — cần tạo .env'}")

print("\n[1] Import gradio_client...")
try:
    from gradio_client import Client, handle_file
    import gradio_client
    print(f"    OK — version {gradio_client.__version__}")
except ImportError as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

print("\n[2] Download ảnh test...")
tmp = tempfile.mkdtemp()
person_path  = os.path.join(tmp, "person.jpg")
garment_path = os.path.join(tmp, "garment.jpg")
try:
    # Ảnh người mẫu (Unsplash)
    urllib.request.urlretrieve(
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=576&h=864&fit=crop",
        person_path
    )
    # Ảnh sản phẩm áo (Unsplash)
    urllib.request.urlretrieve(
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=576&h=864&fit=crop",
        garment_path
    )
    print(f"    OK — lưu tại {tmp}")
    print(f"    Person:  {os.path.getsize(person_path)//1024}KB")
    print(f"    Garment: {os.path.getsize(garment_path)//1024}KB")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

print("\n[3] Gọi FASHN VTON 1.5...")
try:
    client = Client("fashn-ai/fashn-vton-1.5", hf_token=HF_TOKEN)
    print("    Kết nối: OK")
    result = client.predict(
        person_image=handle_file(person_path),
        garment_image=handle_file(garment_path),
        category="tops",
        garment_photo_type="model",
        num_timesteps=50,
        guidance_scale=2.0,
        seed=42,
        segmentation_free=True,
        api_name="/try_on"
    )
    out_path = result[0] if isinstance(result, (list, tuple)) else result
    if isinstance(out_path, dict):
        out_path = out_path.get("path") or out_path.get("url")
    print(f"    Kết quả: {out_path}")
    print(f"    Size: {os.path.getsize(str(out_path))//1024}KB")
    print("\n✅ FASHN VTON 1.5 hoạt động!")
except Exception as e:
    print(f"    FAIL: {type(e).__name__}: {str(e)[:300]}")
    print("\n❌ Lỗi — kiểm tra HF_TOKEN và kết nối mạng")
