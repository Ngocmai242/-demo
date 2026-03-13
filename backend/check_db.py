import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Product

def check_db():
    app = create_app()
    with app.app_context():
        count = Product.query.count()
        print(f"Total products in DB: {count}")
        if count > 0:
            p = Product.query.first()
            print(f"First product: {p.name} (Shop: {p.shop_name})")

if __name__ == '__main__':
    check_db()
