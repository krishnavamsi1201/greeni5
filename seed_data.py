import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'greeni5.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

def seed():
    print("Checking database schema & master categories...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON;')
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    cursor = conn.cursor()

    # Master Users
    users = [
        ('Admin User', 'admin@greeni5.com', generate_password_hash('Admin@123'), 'admin', '+91 98765 43210'),
        ('Customer User', 'customer@greeni5.com', generate_password_hash('Customer@123'), 'customer', '+91 91234 56789')
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO users (name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)',
        users
    )
    conn.commit()

    # Master Botanical Categories
    categories = [
        ('Indoor Plants', 'indoor-plants', 'Air-purifying and aesthetic foliage suited for homes and offices with indirect light.', 'home', 'https://images.unsplash.com/photo-1545241047-6083a3684587?w=600&auto=format&fit=crop&q=80'),
        ('Outdoor Plants', 'outdoor-plants', 'Hardy, sun-loving trees and shrubs ideal for balconies, terraces, and garden landscapes.', 'sun', 'https://images.unsplash.com/photo-1512428813834-c702c7702b78?w=600&auto=format&fit=crop&q=80'),
        ('Flower Plants', 'flower-plants', 'Vibrant flowering ornamentals to infuse fragrance and natural color into your space.', 'flower-2', 'https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=600&auto=format&fit=crop&q=80'),
        ('Fruit Plants', 'fruit-plants', 'Grafted and dwarf fruit-bearing trees tailored for container gardening and home orchards.', 'apple', 'https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=600&auto=format&fit=crop&q=80'),
        ('Medicinal Plants', 'medicinal-plants', 'Traditional therapeutic and aromatic herbs providing pure homegrown wellness remedies.', 'heart-pulse', 'https://images.unsplash.com/photo-1509423350716-97f9360b4e09?w=600&auto=format&fit=crop&q=80')
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO categories (name, slug, description, icon, image_url) VALUES (?, ?, ?, ?, ?)',
        categories
    )
    conn.commit()
    conn.close()
    print("Database ready! Real plants can now be added from the Admin Panel.")

if __name__ == '__main__':
    seed()
