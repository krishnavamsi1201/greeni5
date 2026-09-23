import sqlite3

def run_seed():
    conn = sqlite3.connect('greeni5.db')
    cursor = conn.cursor()

    # 1. Update Existing Plants 3 to 9 (Indoor Plants Category: ID 1)
    indoor_updates = [
        (
            3, 1, 'Golden Pothos Money Plant', 'golden-pothos-money-plant', 249.0, 199.0, 35,
            'Golden Pothos is the quintessential low-maintenance indoor trailing vine. Renowned as a NASA-certified air purifier, it thrives in moderate to low light and adds cascading emerald energy to bookshelves and desks.',
            'Low to bright indirect light', 'Water every 5-7 days when top 2 inches feel dry', '18°C - 30°C',
            'Well-draining aerated potting mix', 'Very Easy', 1, 1,
            'https://images.unsplash.com/photo-1545241047-6083a3684587?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            4, 1, 'Monstera Deliciosa (Swiss Cheese Plant)', 'monstera-deliciosa-swiss', 699.0, 549.0, 20,
            'Iconic tropical indoor specimen boasting dramatic fenestrated leaves. Native to Mexican rainforests, it brings an instant urban jungle statement into any modern living space.',
            'Medium to bright indirect light', 'Water once a week thoroughly', '20°C - 32°C',
            'Peat-moss rich organic potting mix', 'Easy', 1, 1,
            'https://images.unsplash.com/photo-1617173944883-6ffbd35d584d?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1598880940080-ff9a29891b85?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            5, 1, 'ZZ Plant (Fortune Plant)', 'zz-plant-fortune', 499.0, 399.0, 28,
            'Virtually indestructible with architectural, high-gloss waxy leaves. Perfect for modern offices, bedrooms, and dark corners where most plants struggle.',
            'Low light to bright filtered light', 'Water every 2-3 weeks; drought tolerant', '16°C - 32°C',
            'Cactus or well-draining potting soil', 'Very Easy', 1, 0,
            'https://images.unsplash.com/photo-1600411833196-7c1f6b1a8b90?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1512428559087-560fa5ceab42?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            6, 1, 'Peace Lily (Spathiphyllum Bloom)', 'peace-lily-bloom', 399.0, 329.0, 25,
            'Elegantly combines lush deep-green foliage with pure white sail-like spathe blooms. Actively filters benzene, formaldehyde, and ammonia from indoor environments.',
            'Medium to low indirect shade', 'Keep soil lightly moist; water when leaves slightly droop', '18°C - 28°C',
            'Rich, moisture-retaining organic soil', 'Easy', 1, 1,
            'https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1545241047-6083a3684587?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            7, 1, 'Areca Palm (Tropical Air Filter)', 'areca-palm-bamboo', 599.0, 489.0, 18,
            'Feathery arching fronds that produce exceptional humidity and act as a natural air humidifier. Transforms any living room or veranda into an oasis.',
            'Bright filtered sunlight', 'Water 2 times weekly; do not let root ball dry out completely', '20°C - 35°C',
            'Loamy aerated mix with perlite', 'Moderate', 1, 0,
            'https://images.unsplash.com/photo-1615865417491-9941019fbc00?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            8, 1, 'Rubber Plant (Ficus Burgundy)', 'rubber-plant-burgundy', 549.0, 449.0, 22,
            'Broad, leathery, dark burgundy-green leaves that reflect light with a glossy sheen. A dramatic centerpiece that purifies stale indoor air.',
            'Bright indirect light', 'Allow top half of soil to dry between waterings (~7-9 days)', '18°C - 30°C',
            'Standard well-draining potting soil', 'Easy', 0, 1,
            'https://images.unsplash.com/photo-1602491453631-e2a5ad90a131?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1545241047-6083a3684587?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            9, 1, 'Crassula Jade Plant (Money Bonsai)', 'crassula-jade-plant', 349.0, 279.0, 40,
            'Beloved symbol of prosperity, resilience, and positive Vastu energy. Features fleshy teardrop leaves and thick wooden stems that grow like miniature trees.',
            'Bright direct or bright indirect sunlight', 'Water sparingly every 10-14 days', '15°C - 35°C',
            'Sandy porous succulent substrate', 'Very Easy', 0, 1,
            'https://images.unsplash.com/photo-1509937528035-ad76254b0356?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=1000&auto=format&fit=crop&q=80']
        )
    ]

    for pid, cat_id, name, slug, price, disc_price, stock, desc, sun, water, temp, soil, diff, feat, best, prim_img, gall_imgs in indoor_updates:
        cursor.execute('''
            UPDATE plants 
            SET category_id=?, name=?, slug=?, price=?, discount_price=?, stock=?, description=?,
                sunlight=?, watering=?, temperature=?, soil=?, difficulty=?, is_featured=?, is_bestseller=?
            WHERE id=?
        ''', (cat_id, name, slug, price, disc_price, stock, desc, sun, water, temp, soil, diff, feat, best, pid))

        cursor.execute('DELETE FROM plant_images WHERE plant_id=?', (pid,))
        cursor.execute('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 1)', (pid, prim_img))
        for g_img in gall_imgs:
            cursor.execute('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 0)', (pid, g_img))

    # 2. Insert Diverse Plants for Categories 2, 3, 4, 5
    new_plants = [
        # Outdoor Plants (Cat 2)
        (
            2, 'Bougainvillea Glabra (Royal Pink)', 'bougainvillea-glabra-pink', 329.0, 269.0, 30,
            'Spectacular sun-loving flowering vine covered in luminous magenta-pink bracts. Highly heat resistant, drought tolerant, and perfect for sunny balconies, arches, and boundary walls.',
            'Full direct sunlight (6+ hours daily)', 'Water when soil is dry to touch; drought resistant', '22°C - 38°C',
            'Coarse sandy loam mix with good drainage', 'Easy', 1, 1,
            'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1512428813834-c702c7702b78?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            2, 'Red Indian Hibiscus (Gudhal)', 'red-indian-hibiscus-gudhal', 289.0, 229.0, 35,
            'Sacred ornamental shrub bearing radiant ruby-red blossom flowers year-round. Traditionally revered in Indian households and Ayurvedic hair and skin rituals.',
            'Direct morning to mid-day sunlight', 'Water thoroughly daily in summer, alter in monsoon', '20°C - 35°C',
            'Nutrient-rich garden soil with vermicompost', 'Easy', 1, 0,
            'https://images.unsplash.com/photo-1550950158-d0d960dff51b?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            2, 'Desert Rose (Adenium Obesum Bonsai)', 'desert-rose-adenium-bonsai', 749.0, 599.0, 15,
            'Living sculptural bonsai specimen featuring a swollen, sculpted caudex stem and vivid trumpet-shaped blossoms. Stores water internally for extreme resilience.',
            'Intense bright sunlight', 'Water only once every 8-10 days; avoid waterlogging', '20°C - 38°C',
            'Gravelly cactus & succulent mix', 'Easy', 0, 1,
            'https://images.unsplash.com/photo-1512428813834-c702c7702b78?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1509937528035-ad76254b0356?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            2, 'Golden Bamboo (Bambusa Vulgaris)', 'golden-bamboo-hedge', 499.0, 399.0, 20,
            'Graceful vertical canes with golden-yellow stripes and delicate airy foliage. Serves as a soothing privacy screen for terraces, patios, and outdoor entrances.',
            'Direct sun or partial shade', 'Keep moist during growth phases; water 2-3 times weekly', '15°C - 35°C',
            'Rich loamy garden soil with compost', 'Moderate', 0, 0,
            'https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1615865417491-9941019fbc00?w=1000&auto=format&fit=crop&q=80']
        ),

        # Flower Plants (Cat 3)
        (
            3, 'Mogra / Arabian Jasmine (Bhat Mogra)', 'arabian-jasmine-mogra', 279.0, 219.0, 45,
            'Enchanting nocturnal flowering shrub renowned for its intensely sweet, intoxicating natural fragrance. Prized for puja offerings and traditional bridal garlands.',
            'Morning sunlight (4-5 hours)', 'Water moderately when surface soil is dry', '20°C - 34°C',
            'Well-drained soil rich in organic manure', 'Easy', 1, 1,
            'https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            3, 'Fragrant Dutch Red Rose', 'fragrant-dutch-red-rose', 349.0, 289.0, 25,
            'Classic deep-velvet crimson rose bush with perpetual budding cycles and romantic aroma. Bred for compact container gardening on sunny apartment balconies.',
            'Direct bright sunlight for at least 5 hours', 'Deep watering every 2-3 days at base level', '15°C - 30°C',
            'Clayey-loam potting mix fortified with bone meal', 'Moderate', 1, 0,
            'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            3, 'Bright Orange Marigold (Genda)', 'bright-orange-marigold-genda', 149.0, 119.0, 50,
            'Cheerful, sun-kissed pom-pom blooms that repel garden pests naturally while infusing vibrant festive color into verandas and planters.',
            'Full open sunlight', 'Water regularly; keep soil evenly moist but not soggy', '18°C - 35°C',
            'Well-drained garden soil', 'Very Easy', 0, 1,
            'https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=1000&auto=format&fit=crop&q=80']
        ),

        # Fruit Plants (Cat 4)
        (
            4, 'Seedless Kagzi Lemon / Lime Plant', 'seedless-kagzi-lemon-plant', 399.0, 319.0, 30,
            'All-season dwarf grafted citrus plant producing juicy, thin-skinned aromatic lemons. Highly prolific fruiter ideal for large terracotta balcony planters.',
            'Direct all-day sunlight', 'Water deeply twice a week; do not allow roots to sit in stagnant water', '20°C - 36°C',
            'Nutrient-rich loamy soil with cow dung manure', 'Easy', 1, 1,
            'https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1553279768-865429fa0078?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            4, 'Dwarf Amrapali Mango Tree (Grafted)', 'dwarf-amrapali-mango-tree', 649.0, 499.0, 20,
            'Premium dwarf hybrid mango bred specifically for container farming and compact kitchen gardens. Yields fiberless, exceptionally sweet golden mangoes.',
            'Full direct sun', 'Water 2 times weekly during flowering and fruiting', '22°C - 38°C',
            'Rich deep potting soil blended with vermicompost', 'Moderate', 1, 0,
            'https://images.unsplash.com/photo-1553279768-865429fa0078?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            4, 'Bhagwa Ruby Pomegranate (Anar)', 'bhagwa-ruby-pomegranate', 449.0, 369.0, 22,
            'Hardy dwarf pomegranate variety bearing thick-skinned, glossy crimson fruits with sweet, soft ruby-red arils. Highly antioxidant-rich homegrown harvest.',
            'Full direct sun', 'Water moderately; drought resistant once established', '20°C - 38°C',
            'Sandy loam with good natural drainage', 'Easy', 0, 1,
            'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=1000&auto=format&fit=crop&q=80']
        ),

        # Medicinal Plants (Cat 5)
        (
            5, 'Krishna Tulsi (Holy Basil)', 'krishna-tulsi-holy-basil', 199.0, 149.0, 50,
            'Sacred purple-green holy basil with crisp clove-like aroma. An indispensable cornerstone of Indian wellness, boosting immunity and soothing respiratory ailments.',
            'Direct morning to mid-day sun', 'Water daily in moderate amount; do not over-saturate', '20°C - 35°C',
            'Fertile garden soil with compost', 'Very Easy', 1, 1,
            'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1509423350716-97f9360b4e09?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            5, 'Organic Aloe Vera Barbadensis', 'organic-aloe-vera-barbadensis', 249.0, 189.0, 40,
            'Plump, fleshy succulent packed with pure healing polysaccharide gel for soothing burns, hydrating skin, and aiding natural digestion.',
            'Bright indirect sun or gentle morning direct light', 'Water once every 2 weeks; highly drought-hardy', '18°C - 35°C',
            'Fast-draining sandy succulent mix', 'Very Easy', 1, 0,
            'https://images.unsplash.com/photo-1509423350716-97f9360b4e09?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            5, 'Indian Borage (Ajwain Leaf Plant)', 'indian-borage-ajwain-leaf', 199.0, 159.0, 35,
            'Thick velvety leaves with a potent herbal thymol aroma. Extensively used in home herbal teas, bajji fritters, and natural cold/cough steam remedies.',
            'Partial to full morning sunlight', 'Water 2-3 times a week when topsoil dries', '18°C - 32°C',
            'Well-aerated porous garden mix', 'Very Easy', 0, 1,
            'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=1000&auto=format&fit=crop&q=80']
        ),
        (
            5, 'Haworthia Zebra Succulent', 'haworthia-zebra-succulent', 299.0, 239.0, 30,
            'Compact architectural succulent adorned with striking white horizontal zebra stripes. Thrives happily on office workstations, coffee tables, and study desks.',
            'Bright indirect light', 'Water sparingly once every 2-3 weeks', '16°C - 30°C',
            'Gritty succulent mix with pumice', 'Very Easy', 0, 0,
            'https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=1000&auto=format&fit=crop&q=80',
            ['https://images.unsplash.com/photo-1509937528035-ad76254b0356?w=1000&auto=format&fit=crop&q=80']
        )
    ]

    for cat_id, name, slug, price, disc_price, stock, desc, sun, water, temp, soil, diff, feat, best, prim_img, gall_imgs in new_plants:
        cursor.execute('''
            INSERT INTO plants (category_id, name, slug, price, discount_price, stock, description,
                                sunlight, watering, temperature, soil, difficulty, is_featured, is_bestseller)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cat_id, name, slug, price, disc_price, stock, desc, sun, water, temp, soil, diff, feat, best))
        new_pid = cursor.lastrowid

        # Insert primary image
        cursor.execute('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 1)', (new_pid, prim_img))
        for g_img in gall_imgs:
            cursor.execute('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 0)', (new_pid, g_img))

        # Insert pot variants for the new plant
        cursor.execute('''
            INSERT INTO plant_variants (plant_id, variant_name, pot_type, pot_size, extra_price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_pid, '4-inch Nursery Recycled Pot', 'Plastic', 'Small (4")', 0.0, stock))
        cursor.execute('''
            INSERT INTO plant_variants (plant_id, variant_name, pot_type, pot_size, extra_price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_pid, '6-inch Glazed Ceramic Planter', 'Ceramic', 'Medium (6")', 149.0, 20))
        cursor.execute('''
            INSERT INTO plant_variants (plant_id, variant_name, pot_type, pot_size, extra_price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_pid, '8-inch Self-Watering Eco Pot', 'Self-Watering', 'Large (8")', 249.0, 15))

    conn.commit()
    print(f'Successfully updated 7 existing plants and inserted {len(new_plants)} new diverse plants!')

    # Query summary
    cursor.execute('SELECT c.name, count(p.id) FROM categories c LEFT JOIN plants p ON c.id = p.category_id GROUP BY c.id')
    print('Category breakdown:')
    for row in cursor.fetchall():
        print(f' - {row[0]}: {row[1]} plants')

    conn.close()

if __name__ == '__main__':
    run_seed()
