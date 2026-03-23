from app import create_app
import sys

print("DEBUG: run.py is starting...")
print(f"DEBUG: __name__ is {__name__}")
print(f"DEBUG: sys.path is {sys.path}")

app = create_app()

if __name__ == '__main__':
    try:
        print(">>> Starting AuraFit Server on Port 8080...")
        # Bind to 0.0.0.0 to allow access via 127.0.0.1, localhost, or local IP
        app.run(debug=True, port=8080, host='0.0.0.0')
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to start server: {e}")
        input("Press Enter to exit...")
