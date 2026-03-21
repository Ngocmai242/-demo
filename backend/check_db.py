import sqlite3
db = sqlite3.connect('database/database_v2.db')
c = db.cursor()

# Gender distribution
c.execute("SELECT gender, COUNT(*) FROM products GROUP BY gender")
print("=== Gender Distribution ===")
for r in c.fetchall():
    print(r)

# Male products sample
c.execute("SELECT name, gender, category_label, clean_image_path FROM products WHERE gender LIKE '%male%' OR gender LIKE '%Male%' LIMIT 5")
print("\n=== Male Products Sample ===")
for r in c.fetchall():
    print(r)

# Products with clean_image_path (normalized)
c.execute("SELECT COUNT(*) FROM products WHERE clean_image_path IS NOT NULL AND clean_image_path != ''")
print("\n=== Products with clean_image_path ===", c.fetchone())

# Male products with clean
c.execute("SELECT COUNT(*) FROM products WHERE (gender='male' OR gender='Male') AND clean_image_path IS NOT NULL")
print("Male with clean_image_path:", c.fetchone())

db.close()
