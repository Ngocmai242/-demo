import sys
import os

# Ensure project root (so data_engine, frontend, etc. can be imported)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from app import create_app

app = create_app()

if __name__ == '__main__':
    print(">>> STARTING DEV SERVER (FLASK DEBUG)...")
    print(">>> URL: http://localhost:8080")
    print(">>> Auto-reload is ENABLED.")
    # Run in debug mode, monitoring all files in proper folders
    app.run(host='0.0.0.0', port=8080, debug=True)
