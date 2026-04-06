import requests
import time

api_key = "41bc05ce03msh67626f796ce6555p1c4872jsn5c4fa2d8cedd"

try:
    files = {
        'avatar_image': ('avatar.png', open('dummy_avatar.png', 'rb'), 'image/png'),
        'clothing_image': ('garment.png', open('dummy_garment.png', 'rb'), 'image/png'),
    }
    
    payload = {
        'avatar_sex': 'female'
    }
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "try-on-diffusion.p.rapidapi.com"
    }
    
    url = "https://try-on-diffusion.p.rapidapi.com/try-on-file"
    print(f"Testing {url}...")
    start_time = time.time()
    response = requests.post(url, data=payload, files=files, headers=headers, timeout=120)
    duration = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Duration: {duration:.2f}s")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
