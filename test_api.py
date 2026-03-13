from backend.app import create_app
import json

app = create_app()
client = app.test_client()

print("Testing API /api/ai/outfit-for-person...")
response = client.get('/api/ai/outfit-for-person?body_shape=Hourglass&occasion=Tet&gender=Female')
print("Status Code:", response.status_code)
print("Data:", response.data.decode())
