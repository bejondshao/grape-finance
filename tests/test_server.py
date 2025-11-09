# test_backend.py
import requests

try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"✅ Backend is running: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Backend is not running on port 8000")
except Exception as e:
    print(f"❌ Error: {e}")