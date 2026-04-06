from PIL import Image, ImageDraw, ImageFont
import os, uuid
import traceback

person_path = "dummy_avatar.png"
err_msg = "test error"

try:
    img = Image.open(person_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    text = f"RAPID API ERROR:\n{err_msg}\nvui long Subscribe tren RapidAPI!"
    draw.rectangle(((50, 50), (450, 150)), fill="red")
    draw.text((60, 60), text, fill="white")
    
    ext = os.path.splitext(person_path)[1] or ".png"
    out_name = f"error_texel_{uuid.uuid4().hex}{ext}"
    out_path = os.path.join(os.path.dirname(person_path), out_name)
    img.save(out_path)
    print("PIL SUCCESS", out_path)
except Exception as e:
    print("PIL ERROR:", e)
    traceback.print_exc()
