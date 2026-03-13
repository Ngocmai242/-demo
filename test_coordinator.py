import sys
import os
sys.path.append(os.getcwd())

from backend.app import create_app, db
from backend.app.models import Product, ItemType, Category, Style, Color
from backend.app.ai.coordinator import OutfitCoordinator

app = create_app()
with app.app_context():
    print("Testing get_outfit_for_person...")
    try:
        res = OutfitCoordinator.get_outfit_for_person(body_shape='Hourglass', occasion='Play', gender='Female')
        print("Result:", res)
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
