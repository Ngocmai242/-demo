import requests
import base64
import json
import os
from dotenv import load_dotenv

# Load env to get key
load_dotenv()

API_KEY = os.getenv("RAPIDAPI_KEY", "32093762d1msh9ca635f1ef2bc5fp101cabjsn0418c3adbe9d")
HOST = "try-on-diffusion.p.rapidapi.com"
ENDPOINT = "https://try-on-diffusion.p.rapidapi.com/try-on-file"

def test_try_on():
    print(f"--- Testing Texel Moda API ---")
    print(f"Key: {API_KEY[:10]}...")
    
    # Path to sample images if any, otherwise use placeholder logic
    # We'll try to find any image in uploads/tryon
    sample_person = None
    sample_garment = None
    
    upload_dir = "frontend/static/uploads/tryon"
    if not os.path.exists(upload_dir):
        upload_dir = "backend/static/uploads/tryon"

    sample_person = r"C:\Mai\4\frontend\assets\slide1.png"
    sample_garment = r"C:\Mai\4\frontend\assets\slide2.png"

    if not sample_person or not sample_garment:
        print("❌ Error: No sample images found in uploads/tryon to test.")
        return

    print(f"Using Person: {sample_person}")
    print(f"Using Garment: {sample_garment}")

    with open(sample_person, "rb") as f:
        p_b64 = base64.b64encode(f.read()).decode()
    with open(sample_garment, "rb") as f:
        g_b64 = base64.b64encode(f.read()).decode()

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }
    
    files = {
        'avatar_image': ('avatar.png', open(sample_person, "rb"), 'image/png'),
        'clothing_image': ('garment.png', open(sample_garment, "rb"), 'image/png'),
    }
    
    payload = {
        "avatar_sex": "female"
    }

    try:
        print("Calling API (Multipart)...")
        response = requests.post(ENDPOINT, files=files, data=payload, headers={"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST}, timeout=120)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API returned an image!")
            with open("test_result.png", "wb") as f:
                f.write(response.content)
            print("Saved result to test_result.png")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_try_on()
