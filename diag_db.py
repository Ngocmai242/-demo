from backend.app import create_app, db
from backend.app.models import Product, ItemType

app = create_app()
with app.app_context():
    print(f"Total Products: {Product.query.count()}")
    print("Genders in DB:", db.session.query(Product.gender).distinct().all())
    print("ItemTypes in DB:", db.session.query(ItemType.name).all())
    # Check for specific Lunar New Year / Tet items
    tet_items = Product.query.filter(Product.name.ilike('%tet%')).count()
    print(f"Items with 'Tet' in name: {tet_items}")
