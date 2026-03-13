import os
import sys
import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app import create_app, db
from app.models import Product
from app.routes import is_single_item_image

def validate_all_product_images():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        total = len(products)
        print(f'Found {total} products to validate.')

        for i, product in enumerate(products):
            print(f'Processing product {i+1}/{total} (ID: {product.id})...')
            if not product.image_url:
                product.is_valid = False
                print(f'  -> Invalid: No image URL.')
                continue

            try:
                image_bytes = requests.get(product.image_url).content
                is_valid = is_single_item_image(image_bytes)
                product.is_valid = is_valid
                if not is_valid:
                    print(f'  -> Invalid: Multiple items detected.')
                else:
                    print(f'  -> Valid.')
            except Exception as e:
                product.is_valid = False
                print(f'  -> Invalid: Error fetching or processing image: {e}')

        print('Committing changes to the database...')
        db.session.commit()
        print('Validation complete!')

if __name__ == '__main__':
    validate_all_product_images()
