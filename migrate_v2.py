import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'greeni5.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[MIGRATION] Creating tables and altering schema...")

    # 1. Plant Pot Variants
    cur.execute('''
    CREATE TABLE IF NOT EXISTS plant_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id INTEGER NOT NULL,
        variant_name TEXT NOT NULL,
        pot_type TEXT NOT NULL,
        pot_size TEXT,
        extra_price REAL DEFAULT 0.0,
        stock INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
    )
    ''')

    # 2. Add-ons & Frequently Bought Together Items
    cur.execute('''
    CREATE TABLE IF NOT EXISTS addons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'Fertilizers',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. Plant Replacement & Transit Damage Claims
    cur.execute('''
    CREATE TABLE IF NOT EXISTS replacement_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        user_id INTEGER,
        plant_name TEXT NOT NULL,
        reason TEXT NOT NULL,
        photo_url TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')

    # 4. Abandoned Carts for WhatsApp Recovery
    cur.execute('''
    CREATE TABLE IF NOT EXISTS abandoned_carts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        customer_name TEXT,
        email TEXT,
        phone TEXT,
        cart_items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        recovered INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')

    # 5. Flash Sales & Promotional Countdown Banners
    cur.execute('''
    CREATE TABLE IF NOT EXISTS flash_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        discount_pct REAL NOT NULL,
        starts_at TIMESTAMP,
        ends_at TIMESTAMP NOT NULL,
        banner_text TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Check and alter orders table for courier and tracking
    cur.execute("PRAGMA table_info(orders)")
    order_cols = [row[1] for row in cur.fetchall()]

    if 'courier_name' not in order_cols:
        cur.execute("ALTER TABLE orders ADD COLUMN courier_name TEXT DEFAULT ''")
    if 'tracking_number' not in order_cols:
        cur.execute("ALTER TABLE orders ADD COLUMN tracking_number TEXT DEFAULT ''")
    if 'tracking_url' not in order_cols:
        cur.execute("ALTER TABLE orders ADD COLUMN tracking_url TEXT DEFAULT ''")
    if 'invoice_number' not in order_cols:
        cur.execute("ALTER TABLE orders ADD COLUMN invoice_number TEXT DEFAULT ''")

    # Check and alter order_items table for variant
    cur.execute("PRAGMA table_info(order_items)")
    order_item_cols = [row[1] for row in cur.fetchall()]
    if 'variant_name' not in order_item_cols:
        cur.execute("ALTER TABLE order_items ADD COLUMN variant_name TEXT DEFAULT ''")

    # Check and alter reviews table for photo and approval
    cur.execute("PRAGMA table_info(reviews)")
    review_cols = [row[1] for row in cur.fetchall()]
    if 'photo_url' not in review_cols:
        cur.execute("ALTER TABLE reviews ADD COLUMN photo_url TEXT DEFAULT ''")
    if 'is_approved' not in review_cols:
        cur.execute("ALTER TABLE reviews ADD COLUMN is_approved INTEGER DEFAULT 1")

    # Seed starter nursery add-ons
    cur.execute("SELECT COUNT(*) FROM addons")
    if cur.fetchone()[0] == 0:
        addons_seed = [
            ("Organic Vermicompost (1 KG)", 99.0, "https://images.unsplash.com/photo-1585336261026-c56784d85834?w=400", "100% pure organic earthworm castings rich in bio-nutrients for root vigor.", "Fertilizers"),
            ("Brass Mist Sprayer Bottle (500ml)", 149.0, "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=400", "Fine-mist ergonomic spray bottle for houseplant humidity and daily leaf dusting.", "Tools"),
            ("Neem Oil Anti-Pest Foliar Spray (250ml)", 129.0, "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400", "Cold-pressed pure neem extract preventing mealybugs, aphids, and leaf spot.", "Plant Care"),
            ("Organic Seaweed Liquid Tonic (200ml)", 119.0, "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?w=400", "Essential micronutrient booster promotes lush foliage and vibrant flowering.", "Fertilizers")
        ]
        cur.executemany('''
            INSERT INTO addons (name, price, image_url, description, category, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', addons_seed)
        print("[MIGRATION] Seeded 4 nursery add-on combos.")

    conn.commit()
    conn.close()
    print("[MIGRATION] Successfully executed migration v2!")

if __name__ == '__main__':
    migrate()
