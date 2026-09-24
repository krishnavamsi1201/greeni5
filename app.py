import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import re
import json
import uuid
import datetime
import urllib.parse
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import get_db, close_db, query_db, execute_db

app = Flask(__name__)
app.secret_key = 'greeni5-secret-key-production-ready-plants-2026'
app.teardown_appcontext(close_db)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'claims'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'reviews'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('currency')
def currency_filter(amount):
    try:
        val = float(amount)
        return f"₹{val:,.2f}".rstrip('0').rstrip('.') if val % 1 == 0 else f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{amount}"

@app.template_filter('status_badge')
def status_badge_filter(status):
    mapping = {
        'Pending': 'badge-pending',
        'Accepted': 'badge-accepted',
        'Packed': 'badge-packed',
        'Shipped': 'badge-shipped',
        'Delivered': 'badge-delivered',
        'Rejected': 'badge-rejected'
    }
    return mapping.get(status, 'badge-secondary')

@app.context_processor
def inject_global_data():
    categories = query_db('SELECT * FROM categories ORDER BY name ASC')
    cart = session.get('cart', {})
    cart_count = sum(item.get('quantity', 1) for item in cart.values())
    
    current_user = None
    if 'user_id' in session:
        current_user = query_db('SELECT id, name, email, role, phone FROM users WHERE id = ?', (session['user_id'],), one=True)
        if not current_user:
            session.clear()

    active_flash_sale = None
    try:
        active_flash_sale = query_db('SELECT * FROM flash_sales WHERE is_active = 1 AND datetime(ends_at) > datetime("now") ORDER BY id DESC LIMIT 1', one=True)
    except Exception:
        pass
            
    return dict(
        nav_categories=categories,
        cart_count=cart_count,
        current_user=current_user,
        active_flash_sale=active_flash_sale,
        now_year=datetime.datetime.now().year
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('login', next=request.url))
        user = query_db('SELECT role FROM users WHERE id = ?', (session['user_id'],), one=True)
        if not user or user['role'] != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def get_cart_details():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0.0

    if cart:
        for item_key, item_info in list(cart.items()):
            qty = item_info.get('quantity', 1) if isinstance(item_info, dict) else 1

            # Check if this is an add-on item
            if (isinstance(item_info, dict) and item_info.get('is_addon')) or str(item_key).startswith('addon_'):
                addon_id = item_info.get('addon_id') if isinstance(item_info, dict) else None
                if not addon_id and str(item_key).startswith('addon_'):
                    try:
                        addon_id = int(str(item_key).split('_')[1])
                    except (IndexError, ValueError):
                        addon_id = None

                addon = query_db('SELECT * FROM addons WHERE id = ?', (addon_id,), one=True) if addon_id else None
                if addon:
                    effective_price = addon['price']
                    item_subtotal = effective_price * qty
                    subtotal += item_subtotal
                    cart_items.append({
                        'cart_key': str(item_key),
                        'plant_id': None,
                        'addon_id': addon['id'],
                        'name': addon['name'],
                        'slug': '',
                        'variant_name': addon['category'],
                        'price': effective_price,
                        'original_price': addon['price'],
                        'discount_price': None,
                        'quantity': qty,
                        'stock': 99,
                        'subtotal': item_subtotal,
                        'image_url': addon['image_url'],
                        'category_name': 'Plant Care Combo',
                        'is_addon': True
                    })
                else:
                    cart.pop(item_key, None)
            else:
                # Regular plant item (potentially with a variant)
                plant_id = item_info.get('plant_id') if isinstance(item_info, dict) else None
                if not plant_id:
                    try:
                        parts = str(item_key).split('_')
                        plant_id = int(parts[0])
                    except (ValueError, IndexError):
                        plant_id = None

                plant = query_db('''
                    SELECT p.*, c.name as category_name,
                           COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                                    (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1),
                                    'https://images.unsplash.com/photo-1545241047-6083a3684587?w=600') as image_url
                    FROM plants p
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.id = ?
                ''', (plant_id,), one=True) if plant_id else None

                if plant:
                    base_price = plant['discount_price'] if plant['discount_price'] and plant['discount_price'] > 0 else plant['price']
                    variant_id = item_info.get('variant_id') if isinstance(item_info, dict) else None
                    if not variant_id and '_' in str(item_key):
                        try:
                            parts = str(item_key).split('_')
                            if len(parts) > 1:
                                variant_id = int(parts[1])
                        except (ValueError, IndexError):
                            variant_id = None

                    variant = None
                    if variant_id:
                        variant = query_db('SELECT * FROM plant_variants WHERE id = ?', (variant_id,), one=True)

                    variant_name = variant['variant_name'] if variant else 'Standard Nursery Pot'
                    extra_price = variant['extra_price'] if variant else 0.0
                    effective_price = base_price + extra_price
                    item_subtotal = effective_price * qty
                    subtotal += item_subtotal

                    cart_items.append({
                        'cart_key': str(item_key),
                        'plant_id': plant['id'],
                        'variant_id': variant_id,
                        'variant_name': variant_name,
                        'name': plant['name'],
                        'slug': plant['slug'],
                        'price': effective_price,
                        'original_price': plant['price'] + extra_price,
                        'discount_price': (plant['discount_price'] + extra_price) if plant['discount_price'] else None,
                        'quantity': qty,
                        'stock': variant['stock'] if variant else plant['stock'],
                        'subtotal': item_subtotal,
                        'image_url': plant['image_url'],
                        'category_name': plant['category_name'],
                        'is_addon': False
                    })
                else:
                    cart.pop(item_key, None)
        session['cart'] = cart

    # Flash sale discount calculation
    flash_discount = 0.0
    active_flash_sale = None
    try:
        active_flash_sale = query_db('SELECT * FROM flash_sales WHERE is_active = 1 AND datetime(ends_at) > datetime("now") ORDER BY id DESC LIMIT 1', one=True)
        if active_flash_sale and subtotal > 0:
            flash_discount = round(subtotal * (float(active_flash_sale['discount_pct']) / 100.0), 2)
    except Exception:
        pass

    subtotal_after_discount = max(0.0, subtotal - flash_discount)
    shipping = 0.0 if subtotal_after_discount >= 999 or subtotal_after_discount == 0 else 99.0
    tax = round(subtotal_after_discount * 0.05, 2)
    total = round(subtotal_after_discount + shipping + tax, 2)

    return {
        'items': cart_items, 'cart_items': cart_items,
        'subtotal': subtotal,
        'flash_discount': flash_discount,
        'active_flash_sale': active_flash_sale,
        'subtotal_after_discount': subtotal_after_discount,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'free_shipping_threshold': 999.0,
        'amount_for_free_shipping': max(0.0, 999.0 - subtotal_after_discount)
    }

def track_abandoned_cart():
    cart = session.get('cart', {})
    if not cart:
        return
    user_id = session.get('user_id')
    cart_details = get_cart_details()
    if not cart_details['items']:
        return

    items_summary = ", ".join(f"{it['name']} ({it['quantity']}x)" for it in cart_details['items'][:4])
    total_amount = cart_details['total']

    cust_name = ""
    email = ""
    phone = ""

    if user_id:
        user = query_db('SELECT name, email, phone FROM users WHERE id = ?', (user_id,), one=True)
        if user:
            cust_name = user['name']
            email = user['email']
            phone = user['phone'] or ""

    existing = None
    if user_id:
        existing = query_db('SELECT id FROM abandoned_carts WHERE user_id = ? AND recovered = 0', (user_id,), one=True)
    elif email:
        existing = query_db('SELECT id FROM abandoned_carts WHERE email = ? AND recovered = 0', (email,), one=True)

    if existing:
        execute_db('''
            UPDATE abandoned_carts
            SET cart_items_json = ?, total_amount = ?, updated_at = CURRENT_TIMESTAMP,
                customer_name = COALESCE(NULLIF(?, ''), customer_name),
                phone = COALESCE(NULLIF(?, ''), phone)
            WHERE id = ?
        ''', (items_summary, total_amount, cust_name, phone, existing['id']))
    else:
        execute_db('''
            INSERT INTO abandoned_carts (user_id, customer_name, email, phone, cart_items_json, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, cust_name, email, phone, items_summary, total_amount))

# ==========================================
# PUBLIC / CUSTOMER ROUTES
# ==========================================

@app.route('/')
def index():
    categories = query_db('SELECT * FROM categories ORDER BY id ASC')
    
    # Base plant query with category name, primary image, ratings
    plant_select_base = '''
        SELECT p.*, c.name as category_name,
               COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                        (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1),
                        'https://images.unsplash.com/photo-1545241047-6083a3684587?w=800') as image_url,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE plant_id = p.id) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE plant_id = p.id) as review_count
        FROM plants p
        JOIN categories c ON p.category_id = c.id
    '''

    featured_plants = query_db(plant_select_base + ' WHERE p.is_featured = 1 ORDER BY p.id DESC LIMIT 8')
    # If no plant specifically marked featured, show all recent plants
    if not featured_plants:
        featured_plants = query_db(plant_select_base + ' ORDER BY p.id DESC LIMIT 8')

    bestseller_plants = query_db(plant_select_base + ' WHERE p.is_bestseller = 1 ORDER BY p.id DESC LIMIT 8')
    if not bestseller_plants and len(featured_plants) > 4:
        bestseller_plants = featured_plants[4:8]

    # Total plant count to help UI display empty states or catalog counters
    total_plants_count = query_db('SELECT count(*) as cnt FROM plants', one=True)['cnt']

    customer_reviews = query_db('''
        SELECT r.*, p.name as plant_name, p.slug as plant_slug
        FROM reviews r
        JOIN plants p ON r.plant_id = p.id
        ORDER BY r.id DESC LIMIT 4
    ''')

    return render_template(
        'index.html',
        categories=categories,
        featured_plants=featured_plants,
        bestseller_plants=bestseller_plants,
        customer_reviews=customer_reviews,
        total_plants_count=total_plants_count
    )

@app.route('/catalog')
def catalog():
    category_slug = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'popular').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    difficulty = request.args.get('difficulty', '').strip()

    sql = '''
        SELECT p.*, c.name as category_name, c.slug as category_slug,
               COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                        (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1)) as image_url,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE plant_id = p.id) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE plant_id = p.id) as review_count
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []

    selected_category = None
    if category_slug and category_slug != 'all':
        sql += ' AND c.slug = ?'
        params.append(category_slug)
        selected_category = query_db('SELECT * FROM categories WHERE slug = ?', (category_slug,), one=True)

    if search_query:
        sql += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if min_price is not None:
        sql += ' AND COALESCE(p.discount_price, p.price) >= ?'
        params.append(min_price)

    if max_price is not None:
        sql += ' AND COALESCE(p.discount_price, p.price) <= ?'
        params.append(max_price)

    if difficulty:
        sql += ' AND p.difficulty = ?'
        params.append(difficulty)

    if sort == 'price_asc':
        sql += ' ORDER BY COALESCE(p.discount_price, p.price) ASC'
    elif sort == 'price_desc':
        sql += ' ORDER BY COALESCE(p.discount_price, p.price) DESC'
    elif sort == 'newest':
        sql += ' ORDER BY p.id DESC'
    elif sort == 'name_asc':
        sql += ' ORDER BY p.name ASC'
    else:
        sql += ' ORDER BY p.is_bestseller DESC, p.is_featured DESC, p.id ASC'

    plants = query_db(sql, params)
    categories = query_db('SELECT * FROM categories ORDER BY name ASC')

    return render_template(
        'catalog.html',
        plants=plants,
        categories=categories,
        selected_category=selected_category,
        current_category=category_slug,
        search_query=search_query,
        current_sort=sort,
        min_price=min_price,
        max_price=max_price,
        current_difficulty=difficulty,
        total_count=len(plants)
    )

def get_watering_schedule_for_items(items):
    schedule = []
    seen = set()
    for raw_itm in items:
        try:
            itm = dict(raw_itm)
        except Exception:
            itm = raw_itm

        plant_name = itm.get('plant_name', '') if isinstance(itm, dict) else ''
        if not plant_name or plant_name in seen:
            continue
        seen.add(plant_name)

        plant_id = itm.get('plant_id') if isinstance(itm, dict) else None
        plant = query_db('SELECT * FROM plants WHERE id = ?', (plant_id,), one=True) if plant_id else None
        if not plant:
            plant = query_db('SELECT * FROM plants WHERE name LIKE ? LIMIT 1', (f"%{plant_name}%",), one=True)

        watering = plant['watering'] if plant and plant['watering'] else 'Twice a week'
        sunlight = plant['sunlight'] if plant and plant['sunlight'] else 'Bright indirect light'
        img_url = (itm.get('image_url') if isinstance(itm, dict) else '') or (plant['image_url'] if plant and 'image_url' in plant else 'https://images.unsplash.com/photo-1545241047-6083a3684587?w=400')
        var_name = itm.get('variant_name') if isinstance(itm, dict) else ''

        w_lower = watering.lower()
        if 'once' in w_lower:
            days = ['Sun']
            freq_label = 'Once a week (Every Sunday)'
        elif 'daily' in w_lower or 'alternate' in w_lower:
            days = ['Mon', 'Wed', 'Fri', 'Sun']
            freq_label = 'Alternate days'
        elif '10' in w_lower or 'dry' in w_lower:
            days = ['Sun']
            freq_label = 'Every 7-10 days'
        else:
            days = ['Wed', 'Sun']
            freq_label = 'Twice a week (Wed & Sun)'

        schedule.append({
            'plant_name': plant_name,
            'image_url': img_url,
            'variant_name': var_name,
            'watering': watering,
            'sunlight': sunlight,
            'frequency_label': freq_label,
            'days': days,
            'water_amount': '150ml - 200ml'
        })
    return schedule

def generate_whatsapp_care_url(schedule, customer_name="Plant Parent"):
    if not schedule:
        return ""
    lines = [
        "🌿 *Greeni5 Living Plant Watering & Care Schedule*",
        f"Hello {customer_name}! Here is your customized weekly watering schedule:\n"
    ]
    for s in schedule:
        lines.append(f"🌱 *{s['plant_name']}*")
        lines.append(f"   • Watering: {s['frequency_label']} (~{s['water_amount']})")
        lines.append(f"   • Sunlight: {s['sunlight']}")
        lines.append(f"   • Care: Check topsoil before watering.")
        lines.append("")
    lines.append("💧 *Greeni5 Plant Doctor Helpline:* +91 98765 43210")
    lines.append("Happy Gardening with Greeni5! 🪴✨")
    msg = "\n".join(lines)
    return f"https://wa.me/?text={urllib.parse.quote(msg)}"

@app.route('/plant-quiz')
def plant_quiz():
    location = request.args.get('location', 'indoor')
    sunlight = request.args.get('sunlight', 'indirect')
    experience = request.args.get('experience', 'beginner')

    sql = '''
        SELECT p.*, c.name as category_name, c.slug as category_slug,
               COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                        (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1),
                        'https://images.unsplash.com/photo-1545241047-6083a3684587?w=600') as image_url,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE plant_id = p.id AND is_approved = 1) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE plant_id = p.id AND is_approved = 1) as review_count
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE p.stock > 0
        ORDER BY p.is_bestseller DESC, p.is_featured DESC, p.id ASC
    '''
    plants = query_db(sql)
    if not plants:
        fallback_sql = sql.replace('WHERE p.stock > 0', 'WHERE 1=1')
        plants = query_db(fallback_sql)

    return render_template(
        'quiz.html',
        recommended_plants=plants,
        location=location,
        sunlight=sunlight,
        experience=experience
    )

@app.route('/plant/<slug>')
def plant_details(slug):
    plant = query_db('''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE p.slug = ?
    ''', (slug,), one=True)

    if not plant:
        abort(404)

    images = query_db('SELECT * FROM plant_images WHERE plant_id = ? ORDER BY is_primary DESC, id ASC', (plant['id'],))
    variants = query_db('SELECT * FROM plant_variants WHERE plant_id = ? ORDER BY extra_price ASC', (plant['id'],))
    addons = query_db('SELECT * FROM addons WHERE is_active = 1 LIMIT 4')
    reviews = query_db('SELECT * FROM reviews WHERE plant_id = ? AND is_approved = 1 ORDER BY created_at DESC', (plant['id'],))
    avg_rating = query_db('SELECT ROUND(AVG(rating), 1) as avg, COUNT(*) as cnt FROM reviews WHERE plant_id = ? AND is_approved = 1', (plant['id'],), one=True)

    related_plants = query_db('''
        SELECT p.*, c.name as category_name,
               COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                        (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1)) as image_url,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE plant_id = p.id AND is_approved = 1) as avg_rating
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ?
        ORDER BY RANDOM() LIMIT 4
    ''', (plant['category_id'], plant['id']))

    return render_template(
        'plant_details.html',
        plant=plant,
        images=images,
        variants=variants,
        addons=addons,
        reviews=reviews,
        avg_rating=avg_rating['avg'] or 5.0,
        review_count=avg_rating['cnt'] or 0,
        related_plants=related_plants
    )

@app.route('/cart')
def cart():
    cart_data = get_cart_details()
    return render_template('cart.html', cart=cart_data)

@app.route('/cart/add/<int:plant_id>', methods=['POST', 'GET'])
def add_to_cart(plant_id):
    plant = query_db('SELECT * FROM plants WHERE id = ?', (plant_id,), one=True)
    if not plant:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Plant not found'}), 404
        flash('Plant not found.', 'danger')
        return redirect(url_for('catalog'))

    qty = int(request.form.get('quantity', request.args.get('quantity', 1)))
    qty = max(1, qty)

    variant_id_raw = request.form.get('variant_id', request.args.get('variant_id'))
    variant_id = int(variant_id_raw) if variant_id_raw and str(variant_id_raw).isdigit() else None

    cart = session.get('cart', {})
    cart_key = f"{plant_id}_{variant_id}" if variant_id else str(plant_id)

    current_qty = cart.get(cart_key, {}).get('quantity', 0) if isinstance(cart.get(cart_key), dict) else 0
    new_qty = min(current_qty + qty, plant['stock'])

    cart[cart_key] = {
        'plant_id': plant_id,
        'variant_id': variant_id,
        'quantity': new_qty,
        'is_addon': False
    }
    session['cart'] = cart
    session.modified = True
    track_abandoned_cart()

    total_cart_count = sum(item.get('quantity', 1) if isinstance(item, dict) else 1 for item in cart.values())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            'success': True,
            'message': f"Added {plant['name']} to cart!",
            'plant_name': plant['name'],
            'cart_count': total_cart_count
        })

    flash(f"Added {plant['name']} to cart!", 'success')
    referrer = request.referrer
    if referrer and ('catalog' in referrer or 'plant' in referrer):
        anchor = f"#plant-{plant_id}"
        if '#' not in referrer:
            return redirect(referrer + anchor)
    return redirect(referrer or url_for('cart'))

@app.route('/cart/add-addon/<int:addon_id>', methods=['GET', 'POST'])
def add_addon_to_cart(addon_id):
    addon = query_db('SELECT * FROM addons WHERE id = ?', (addon_id,), one=True)
    if not addon:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Add-on combo not found'}), 404
        flash('Add-on combo not found.', 'warning')
        return redirect(url_for('cart'))

    cart = session.get('cart', {})
    cart_key = f"addon_{addon_id}"
    current_qty = cart.get(cart_key, {}).get('quantity', 0) if isinstance(cart.get(cart_key), dict) else 0

    cart[cart_key] = {
        'addon_id': addon_id,
        'quantity': current_qty + 1,
        'is_addon': True
    }
    session['cart'] = cart
    session.modified = True
    track_abandoned_cart()

    total_cart_count = sum(item.get('quantity', 1) if isinstance(item, dict) else 1 for item in cart.values())
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            'success': True,
            'message': f"Added {addon['name']} combo to your cart!",
            'cart_count': total_cart_count
        })

    flash(f"Added {addon['name']} combo to your cart!", 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    cart_key = request.form.get('cart_key') or request.form.get('plant_id')
    quantity = int(request.form.get('quantity', 1))

    cart = session.get('cart', {})
    key_str = str(cart_key)

    if key_str in cart:
        if quantity <= 0:
            cart.pop(key_str, None)
        else:
            if isinstance(cart[key_str], dict):
                cart[key_str]['quantity'] = quantity
            else:
                cart[key_str] = {'quantity': quantity}
        session['cart'] = cart
        session.modified = True
        track_abandoned_cart()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        cart_data = get_cart_details()
        return jsonify({
            'success': True,
            'cart_count': sum(item.get('quantity', 1) if isinstance(item, dict) else 1 for item in cart.values()),
            'cart_data': cart_data
        })

    return redirect(url_for('cart'))

@app.route('/cart/remove/<path:cart_key>', methods=['POST', 'GET'])
def remove_from_cart(cart_key):
    cart = session.get('cart', {})
    key_str = str(cart_key)
    if key_str in cart:
        cart.pop(key_str, None)
        session['cart'] = cart
        session.modified = True
        track_abandoned_cart()
        flash('Item removed from cart.', 'info')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        cart_data = get_cart_details()
        return jsonify({
            'success': True,
            'cart_count': sum(item.get('quantity', 1) if isinstance(item, dict) else 1 for item in cart.values()),
            'cart_data': cart_data
        })

    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    session.modified = True
    flash('Cart has been cleared.', 'info')
    return redirect(url_for('cart'))

# ==========================================
# REVIEWS & GUARANTEE CLAIMS
# ==========================================

@app.route('/reviews/add/<int:plant_id>', methods=['POST'])
def add_review(plant_id):
    plant = query_db('SELECT * FROM plants WHERE id = ?', (plant_id,), one=True)
    if not plant:
        abort(404)

    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()
    user_name = request.form.get('user_name', '').strip()
    user_id = session.get('user_id')

    if user_id:
        user = query_db('SELECT name FROM users WHERE id = ?', (user_id,), one=True)
        if user:
            user_name = user['name']

    if not user_name:
        user_name = "Greeni5 Gardener"

    photo_url = ''
    if 'review_photo' in request.files:
        file = request.files['review_photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"rev_{plant_id}_{int(datetime.datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'reviews', filename))
            photo_url = url_for('static', filename=f'uploads/reviews/{filename}')

    if comment:
        execute_db('''
            INSERT INTO reviews (plant_id, user_id, user_name, rating, comment, photo_url, is_approved)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (plant_id, user_id, user_name, rating, comment, photo_url))
        flash('Thank you! Your plant review and photo have been published.', 'success')
    else:
        flash('Please provide a comment for your review.', 'warning')

    return redirect(url_for('plant_details', slug=plant['slug']))

@app.route('/order/claim-replacement', methods=['GET'])
@app.route('/orders/claim-replacement', methods=['GET'])
def general_claim_replacement():
    user_id = session.get('user_id')
    if user_id:
        latest_order = query_db('SELECT id FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,), one=True)
        if latest_order:
            return redirect(url_for('customer_claim_replacement', order_id=latest_order['id']))
        flash('You have no active orders to claim replacement for.', 'info')
        return redirect(url_for('dashboard'))
    flash('Please enter your order number below to claim replacement for your shipment.', 'info')
    return redirect(url_for('track_lookup'))

@app.route('/orders/<int:order_id>/claim-replacement', methods=['GET', 'POST'])
def customer_claim_replacement(order_id):
    order = query_db('SELECT * FROM orders WHERE id = ?', (order_id,), one=True)
    if not order:
        abort(404)

    items = query_db('SELECT * FROM order_items WHERE order_id = ?', (order_id,))

    if request.method == 'POST':
        plant_name = request.form.get('plant_name', '').strip()
        reason = request.form.get('reason', '').strip()
        photo_url = ''

        if 'damage_photo' in request.files:
            file = request.files['damage_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"claim_{order_id}_{int(datetime.datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'claims', filename))
                photo_url = url_for('static', filename=f'uploads/claims/{filename}')

        user_id = session.get('user_id')
        execute_db('''
            INSERT INTO replacement_claims (order_id, user_id, plant_name, reason, photo_url, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
        ''', (order_id, user_id, plant_name, reason, photo_url))

        flash('Your 7-Day Guarantee Replacement Claim has been submitted! Our greenhouse team will inspect and dispatch a healthy new plant shortly.', 'success')
        return redirect(url_for('order_tracking', order_number=order['order_number']))

    return render_template('claim_replacement.html', order=order, items=items)

@app.route('/order/<order_number>/invoice')
def customer_invoice(order_number):
    order = query_db('SELECT * FROM orders WHERE order_number = ?', (order_number,), one=True)
    if not order:
        abort(404)
    items = query_db('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
    return render_template('admin/invoice.html', order=order, items=items)

# ==========================================
# CHECKOUT & ORDER ROUTES
# ==========================================

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_data = get_cart_details()
    if not cart_data['items']:
        flash('Your cart is empty. Add plants before checking out.', 'warning')
        return redirect(url_for('catalog'))

    track_abandoned_cart()

    saved_addresses = []
    if 'user_id' in session:
        saved_addresses = query_db('SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC', (session['user_id'],))

    if request.method == 'POST':
        full_name = request.form.get('customer_name', '').strip()
        email = request.form.get('customer_email', '').strip()
        phone = request.form.get('customer_phone', '').strip()
        address = request.form.get('shipping_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        payment_method = request.form.get('payment_method', 'COD').strip()
        notes = request.form.get('notes', '').strip()
        save_address = request.form.get('save_address') == '1'

        is_gift = 1 if request.form.get('is_gift') in ['1', 'on', 'true'] else 0
        gift_recipient_name = request.form.get('gift_recipient_name', '').strip() if is_gift else ''
        gift_message = request.form.get('gift_message', '').strip() if is_gift else ''
        gift_wrap_fee = 49.0 if is_gift else 0.0
        final_total = round(cart_data['total'] + gift_wrap_fee, 2)

        if not all([full_name, email, phone, address, city, state, pincode]):
            flash('Please complete all shipping address fields.', 'danger')
            return render_template('checkout.html', cart=cart_data, saved_addresses=saved_addresses)

        order_num = f"GRN-{datetime.datetime.now().year}-{str(uuid.uuid4().int)[:6]}"
        user_id = session.get('user_id')
        payment_status = 'Paid' if payment_method in ['Online / Card', 'UPI'] else 'Pending'
        invoice_num = f"INV-{order_num}"

        order_id = execute_db('''
            INSERT INTO orders 
            (order_number, invoice_number, user_id, customer_name, customer_email, customer_phone, shipping_address, city, state, pincode, payment_method, payment_status, order_status, total_amount, notes, is_gift, gift_recipient_name, gift_message, gift_wrap_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, ?, ?)
        ''', (order_num, invoice_num, user_id, full_name, email, phone, address, city, state, pincode, payment_method, payment_status, final_total, notes, is_gift, gift_recipient_name, gift_message, gift_wrap_fee))

        for item in cart_data['items']:
            execute_db('''
                INSERT INTO order_items (order_id, plant_id, plant_name, variant_name, price, quantity, subtotal, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, item.get('plant_id'), item['name'], item.get('variant_name', ''), item['price'], item['quantity'], item['subtotal'], item['image_url']))

            if item.get('plant_id'):
                execute_db('UPDATE plants SET stock = MAX(0, stock - ?) WHERE id = ?', (item['quantity'], item['plant_id']))

        if user_id and save_address:
            execute_db('''
                INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (user_id, full_name, phone, address, city, state, pincode))

        # Mark abandoned cart as recovered
        execute_db('''
            UPDATE abandoned_carts SET recovered = 1
            WHERE (user_id = ? OR email = ? OR phone = ?) AND recovered = 0
        ''', (user_id, email, phone))

        session['cart'] = {}
        session.modified = True

        flash(f'Order #{order_num} has been placed successfully!', 'success')
        return redirect(url_for('order_success', order_number=order_num))

    return render_template('checkout.html', cart=cart_data, saved_addresses=saved_addresses)

@app.route('/order/success/<order_number>')
def order_success(order_number):
    order = query_db('SELECT * FROM orders WHERE order_number = ?', (order_number,), one=True)
    if not order:
        abort(404)
    items = query_db('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
    return render_template('order_success.html', order=order, items=items)

@app.route('/order/track/<order_number>')
def order_tracking(order_number):
    order = query_db('SELECT * FROM orders WHERE order_number = ?', (order_number,), one=True)
    if not order:
        flash(f'Order {order_number} not found. Please check the order number.', 'warning')
        return redirect(url_for('track_lookup'))

    items = query_db('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
    watering_schedule = get_watering_schedule_for_items(items)
    whatsapp_care_url = generate_whatsapp_care_url(watering_schedule, order['customer_name'])
    stages = ['Pending', 'Accepted', 'Packed', 'Shipped', 'Delivered']
    current_status = order['order_status']
    current_stage_idx = stages.index(current_status) if current_status in stages else -1
    is_rejected = current_status == 'Rejected'

    return render_template(
        'order_tracking.html',
        order=order,
        items=items,
        stages=stages,
        current_status=current_status,
        current_stage_idx=current_stage_idx,
        is_rejected=is_rejected,
        watering_schedule=watering_schedule,
        whatsapp_care_url=whatsapp_care_url
    )

@app.route('/track', methods=['GET', 'POST'])
def track_lookup():
    if request.method == 'POST':
        order_num = request.form.get('order_number', '').strip()
        if order_num:
            return redirect(url_for('order_tracking', order_number=order_num))
        flash('Please enter a valid order number.', 'danger')
    return render_template('order_tracking.html', order=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email address or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([name, email, password]):
            flash('Please provide name, email, and password.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        existing = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        user_id = execute_db('''
            INSERT INTO users (name, email, password_hash, role, phone)
            VALUES (?, ?, ?, 'customer', ?)
        ''', (name, email, generate_password_hash(password), phone))

        session['user_id'] = user_id
        session['user_role'] = 'customer'
        session['user_name'] = name
        flash('Account registered successfully! Welcome to Greeni5.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if user:
            flash('A secure password reset link has been dispatched to your email.', 'success')
        else:
            flash('If an account exists with this email, a reset link has been dispatched.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    orders = query_db('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    addresses = query_db('SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC', (session['user_id'],))

    orders_with_items = []
    all_purchased_items = []
    for ord in orders:
        items = query_db('SELECT * FROM order_items WHERE order_id = ?', (ord['id'],))
        orders_with_items.append({'order': ord, 'order_items': items})
        all_purchased_items.extend(items)

    watering_schedule = get_watering_schedule_for_items(all_purchased_items)
    whatsapp_care_url = generate_whatsapp_care_url(watering_schedule, user['name'])

    return render_template(
        'dashboard.html',
        user=user,
        orders_with_items=orders_with_items,
        addresses=addresses,
        watering_schedule=watering_schedule,
        whatsapp_care_url=whatsapp_care_url
    )

@app.route('/dashboard/profile/update', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if name:
        execute_db('UPDATE users SET name = ?, phone = ? WHERE id = ?', (name, phone, session['user_id']))
        session['user_name'] = name
        flash('Profile updated successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/address/add', methods=['POST'])
@login_required
def add_address():
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address_line = request.form.get('address_line', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    pincode = request.form.get('pincode', '').strip()
    is_default = 1 if request.form.get('is_default') else 0

    if is_default:
        execute_db('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (session['user_id'],))

    execute_db('''
        INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], full_name, phone, address_line, city, state, pincode, is_default))

    flash('Shipping address added successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/address/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    execute_db('DELETE FROM addresses WHERE id = ? AND user_id = ?', (address_id, session['user_id']))
    flash('Address removed.', 'info')
    return redirect(url_for('dashboard'))

# ==========================================
# INFORMATIONAL PAGES
# ==========================================

@app.route('/care-tips')
def care_tips():
    return render_template('care_tips.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if all([name, email, subject, message]):
            execute_db('''
                INSERT INTO contact_messages (name, email, subject, message)
                VALUES (?, ?, ?, ?)
            ''', (name, email, subject, message))
            flash('Thank you for reaching out! Our horticulture team will respond shortly.', 'success')
            return redirect(url_for('contact'))
        flash('Please fill in all contact form fields.', 'warning')
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==========================================
# ADMIN DASHBOARD & MANAGEMENT ROUTES
# ==========================================

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_plants = query_db('SELECT COUNT(*) as cnt FROM plants', one=True)['cnt']
    total_customers = query_db('SELECT COUNT(*) as cnt FROM users WHERE role = "customer"', one=True)['cnt']
    total_orders = query_db('SELECT COUNT(*) as cnt FROM orders', one=True)['cnt']
    pending_orders = query_db('SELECT COUNT(*) as cnt FROM orders WHERE order_status = "Pending"', one=True)['cnt']
    revenue_res = query_db('SELECT SUM(total_amount) as rev FROM orders WHERE order_status != "Rejected"', one=True)
    total_revenue = revenue_res['rev'] or 0.0

    recent_orders = query_db('''
        SELECT * FROM orders ORDER BY created_at DESC LIMIT 6
    ''')

    low_stock_plants = query_db('''
        SELECT p.*, c.name as category_name
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE p.stock <= 10
        ORDER BY p.stock ASC LIMIT 5
    ''')

    category_counts = query_db('''
        SELECT c.name, COUNT(p.id) as plant_count
        FROM categories c
        LEFT JOIN plants p ON c.id = p.category_id
        GROUP BY c.id
    ''')

    return render_template(
        'admin/dashboard.html',
        total_plants=total_plants,
        total_customers=total_customers,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        recent_orders=recent_orders,
        low_stock_plants=low_stock_plants,
        category_counts=category_counts
    )

@app.route('/admin/plants')
@admin_required
def admin_plants():
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()

    sql = '''
        SELECT p.*, c.name as category_name,
               COALESCE((SELECT image_url FROM plant_images WHERE plant_id = p.id AND is_primary = 1 LIMIT 1),
                        (SELECT image_url FROM plant_images WHERE plant_id = p.id LIMIT 1)) as image_url
        FROM plants p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []

    if category_id:
        sql += ' AND p.category_id = ?'
        params.append(category_id)

    if search:
        sql += ' AND p.name LIKE ?'
        params.append(f'%{search}%')

    sql += ' ORDER BY p.id DESC'
    plants = query_db(sql, params)
    categories = query_db('SELECT * FROM categories ORDER BY name ASC')

    return render_template('admin/plants.html', plants=plants, categories=categories, current_category=category_id, search=search)

@app.route('/admin/plants/add', methods=['GET', 'POST'])
@admin_required
def admin_plant_add():
    categories = query_db('SELECT * FROM categories ORDER BY name ASC')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        price = float(request.form.get('price', 0))
        discount_price = request.form.get('discount_price')
        discount_price = float(discount_price) if discount_price else None
        stock = int(request.form.get('stock', 10))
        description = request.form.get('description', '').strip()
        sunlight = request.form.get('sunlight', '').strip()
        watering = request.form.get('watering', '').strip()
        temperature = request.form.get('temperature', '').strip()
        soil = request.form.get('soil', '').strip()
        difficulty = request.form.get('difficulty', 'Easy').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_bestseller = 1 if request.form.get('is_bestseller') else 0

        slug = slugify(name)
        existing = query_db('SELECT id FROM plants WHERE slug = ?', (slug,), one=True)
        if existing:
            slug = f"{slug}-{str(uuid.uuid4())[:4]}"

        plant_id = execute_db('''
            INSERT INTO plants 
            (category_id, name, slug, price, discount_price, stock, description, sunlight, watering, temperature, soil, difficulty, is_featured, is_bestseller)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category_id, name, slug, price, discount_price, stock, description, sunlight, watering, temperature, soil, difficulty, is_featured, is_bestseller))

        save_plant_variants(plant_id, request.form)

        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            for idx, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{plant_id}_{int(datetime.datetime.now().timestamp())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    img_url = url_for('static', filename=f'uploads/{filename}')
                    execute_db('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, ?)', (plant_id, img_url, 1 if idx == 0 else 0))

        image_urls_raw = request.form.get('image_urls', '').strip()
        if image_urls_raw:
            urls = [u.strip() for u in re.split(r'[\r\n,]+', image_urls_raw) if u.strip()]
            existing_imgs = query_db('SELECT count(*) as cnt FROM plant_images WHERE plant_id = ?', (plant_id,), one=True)['cnt']
            for idx, url in enumerate(urls):
                is_prim = 1 if existing_imgs == 0 and idx == 0 else 0
                execute_db('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, ?)', (plant_id, url, is_prim))

        has_imgs = query_db('SELECT count(*) as cnt FROM plant_images WHERE plant_id = ?', (plant_id,), one=True)['cnt']
        if has_imgs == 0:
            execute_db('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 1)', (plant_id, 'https://images.unsplash.com/photo-1545241047-6083a3684587?w=800'))

        flash(f'Plant "{name}" has been added to catalog.', 'success')
        return redirect(url_for('admin_plants'))

    return render_template('admin/plant_form.html', categories=categories, plant=None, images=[], variants=[])

def save_plant_variants(plant_id, form):
    variant_names = form.getlist('variant_name[]')
    pot_types = form.getlist('pot_type[]')
    variant_extra_prices = form.getlist('variant_extra_price[]')
    variant_stocks = form.getlist('variant_stock[]')

    if variant_names:
        execute_db('DELETE FROM plant_variants WHERE plant_id = ?', (plant_id,))
        for idx, vname in enumerate(variant_names):
            vname = vname.strip()
            if vname:
                ptype = pot_types[idx].strip() if idx < len(pot_types) else 'Nursery'
                try:
                    ex_price = float(variant_extra_prices[idx]) if idx < len(variant_extra_prices) else 0.0
                except (ValueError, TypeError):
                    ex_price = 0.0
                try:
                    vstock = int(variant_stocks[idx]) if idx < len(variant_stocks) else 10
                except (ValueError, TypeError):
                    vstock = 10
                execute_db('''
                    INSERT INTO plant_variants (plant_id, variant_name, pot_type, pot_size, extra_price, stock)
                    VALUES (?, ?, ?, 'Standard', ?, ?)
                ''', (plant_id, vname, ptype, ex_price, vstock))

@app.route('/admin/plants/edit/<int:plant_id>', methods=['GET', 'POST'])
@admin_required
def admin_plant_edit(plant_id):
    plant = query_db('SELECT * FROM plants WHERE id = ?', (plant_id,), one=True)
    if not plant:
        abort(404)

    categories = query_db('SELECT * FROM categories ORDER BY name ASC')
    images = query_db('SELECT * FROM plant_images WHERE plant_id = ? ORDER BY is_primary DESC, id ASC', (plant_id,))
    variants = query_db('SELECT * FROM plant_variants WHERE plant_id = ? ORDER BY extra_price ASC', (plant_id,))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        price = float(request.form.get('price', 0))
        discount_price = request.form.get('discount_price')
        discount_price = float(discount_price) if discount_price else None
        stock = int(request.form.get('stock', 10))
        description = request.form.get('description', '').strip()
        sunlight = request.form.get('sunlight', '').strip()
        watering = request.form.get('watering', '').strip()
        temperature = request.form.get('temperature', '').strip()
        soil = request.form.get('soil', '').strip()
        difficulty = request.form.get('difficulty', 'Easy').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_bestseller = 1 if request.form.get('is_bestseller') else 0

        execute_db('''
            UPDATE plants 
            SET category_id = ?, name = ?, price = ?, discount_price = ?, stock = ?,
                description = ?, sunlight = ?, watering = ?, temperature = ?, soil = ?,
                difficulty = ?, is_featured = ?, is_bestseller = ?
            WHERE id = ?
        ''', (category_id, name, price, discount_price, stock, description, sunlight, watering, temperature, soil, difficulty, is_featured, is_bestseller, plant_id))

        save_plant_variants(plant_id, request.form)

        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{plant_id}_{int(datetime.datetime.now().timestamp())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    img_url = url_for('static', filename=f'uploads/{filename}')
                    execute_db('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 0)', (plant_id, img_url))

        image_urls_raw = request.form.get('image_urls', '').strip()
        if image_urls_raw:
            urls = [u.strip() for u in re.split(r'[\r\n,]+', image_urls_raw) if u.strip()]
            for url in urls:
                execute_db('INSERT INTO plant_images (plant_id, image_url, is_primary) VALUES (?, ?, 0)', (plant_id, url))

        primary_img_id = request.form.get('primary_image_id', type=int)
        if primary_img_id:
            execute_db('UPDATE plant_images SET is_primary = 0 WHERE plant_id = ?', (plant_id,))
            execute_db('UPDATE plant_images SET is_primary = 1 WHERE id = ? AND plant_id = ?', (primary_img_id, plant_id))

        flash(f'Plant "{name}" updated successfully.', 'success')
        return redirect(url_for('admin_plants'))

    return render_template('admin/plant_form.html', categories=categories, plant=plant, images=images, variants=variants)

@app.route('/admin/plants/delete/<int:plant_id>', methods=['POST'])
@admin_required
def admin_plant_delete(plant_id):
    plant = query_db('SELECT name FROM plants WHERE id = ?', (plant_id,), one=True)
    if plant:
        execute_db('DELETE FROM plants WHERE id = ?', (plant_id,))
        flash(f'Plant "{plant["name"]}" deleted.', 'info')
    return redirect(url_for('admin_plants'))

@app.route('/admin/plants/image/delete/<int:image_id>', methods=['POST'])
@admin_required
def admin_image_delete(image_id):
    img = query_db('SELECT plant_id, is_primary FROM plant_images WHERE id = ?', (image_id,), one=True)
    if img:
        execute_db('DELETE FROM plant_images WHERE id = ?', (image_id,))
        if img['is_primary']:
            execute_db('UPDATE plant_images SET is_primary = 1 WHERE plant_id = ? LIMIT 1', (img['plant_id'],))
        flash('Image removed.', 'info')
        return redirect(url_for('admin_plant_edit', plant_id=img['plant_id']))
    return redirect(url_for('admin_plants'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    sql = 'SELECT * FROM orders WHERE 1=1'
    params = []

    if status_filter and status_filter != 'All':
        sql += ' AND order_status = ?'
        params.append(status_filter)

    if search:
        sql += ' AND (order_number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    sql += ' ORDER BY created_at DESC'
    orders = query_db(sql, params)

    orders_data = []
    for ord in orders:
        items = query_db('SELECT * FROM order_items WHERE order_id = ?', (ord['id'],))
        orders_data.append({'order': ord, 'order_items': items})

    return render_template('admin/orders.html', orders=orders_data, current_status=status_filter, search=search)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status_update(order_id):
    new_status = request.form.get('order_status')
    valid_statuses = ['Pending', 'Accepted', 'Packed', 'Shipped', 'Delivered', 'Rejected']

    if new_status in valid_statuses:
        execute_db('UPDATE orders SET order_status = ? WHERE id = ?', (new_status, order_id))
        flash(f'Order status updated to {new_status}.', 'success')
    else:
        flash('Invalid order status.', 'danger')

    return redirect(request.referrer or url_for('admin_orders'))

@app.route('/admin/orders/<int:order_id>/tracking', methods=['POST'])
@admin_required
def admin_order_tracking_update(order_id):
    courier_name = request.form.get('courier_name', '').strip()
    tracking_number = request.form.get('tracking_number', '').strip()
    tracking_url = f"https://www.delhivery.com/track/package/{tracking_number}" if tracking_number else ""

    execute_db('''
        UPDATE orders 
        SET courier_name = ?, tracking_number = ?, tracking_url = ?
        WHERE id = ?
    ''', (courier_name, tracking_number, tracking_url, order_id))

    flash('Courier & Tracking AWB updated.', 'success')
    return redirect(request.referrer or url_for('admin_orders'))

@app.route('/admin/orders/<int:order_id>/invoice')
@admin_required
def admin_order_invoice(order_id):
    order = query_db('SELECT * FROM orders WHERE id = ?', (order_id,), one=True)
    if not order:
        abort(404)
    items = query_db('SELECT * FROM order_items WHERE order_id = ?', (order_id,))
    return render_template('admin/invoice.html', order=order, items=items)

# ==========================================
# ADMIN ADD-ONS & COMBOS (Feature 2)
# ==========================================

@app.route('/admin/addons', methods=['GET', 'POST'])
@admin_required
def admin_addons():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price', 0))
        category = request.form.get('category', 'Fertilizers').strip()
        image_url = request.form.get('image_url', '').strip()
        description = request.form.get('description', '').strip()

        if name and price > 0:
            execute_db('''
                INSERT INTO addons (name, price, image_url, description, category, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (name, price, image_url, description, category))
            flash(f'Add-on combo "{name}" added successfully.', 'success')
            return redirect(url_for('admin_addons'))

    addons = query_db('SELECT * FROM addons ORDER BY id DESC')
    return render_template('admin/addons.html', addons=addons)

@app.route('/admin/addons/<int:addon_id>/toggle', methods=['POST'])
@admin_required
def admin_addon_toggle(addon_id):
    addon = query_db('SELECT is_active FROM addons WHERE id = ?', (addon_id,), one=True)
    if addon:
        new_state = 0 if addon['is_active'] else 1
        execute_db('UPDATE addons SET is_active = ? WHERE id = ?', (new_state, addon_id))
        flash('Add-on visibility updated.', 'info')
    return redirect(url_for('admin_addons'))

@app.route('/admin/addons/<int:addon_id>/delete', methods=['POST'])
@admin_required
def admin_addon_delete(addon_id):
    execute_db('DELETE FROM addons WHERE id = ?', (addon_id,))
    flash('Add-on deleted.', 'info')
    return redirect(url_for('admin_addons'))

# ==========================================
# ADMIN REPLACEMENT CLAIMS (Feature 3)
# ==========================================

@app.route('/admin/replacements')
@admin_required
def admin_replacements():
    claims = query_db('''
        SELECT rc.*, o.order_number, o.customer_name, o.customer_phone
        FROM replacement_claims rc
        JOIN orders o ON rc.order_id = o.id
        ORDER BY rc.id DESC
    ''')
    return render_template('admin/replacements.html', claims=claims)

@app.route('/admin/replacements/<int:claim_id>/status', methods=['POST'])
@admin_required
def admin_claim_status_update(claim_id):
    status = request.form.get('status', 'Pending')
    admin_notes = request.form.get('admin_notes', '').strip()

    execute_db('''
        UPDATE replacement_claims 
        SET status = ?, admin_notes = ?, resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, admin_notes, claim_id))

    flash(f'Claim #CLM-{claim_id} updated to {status}.', 'success')
    return redirect(url_for('admin_replacements'))

# ==========================================
# ADMIN ABANDONED CARTS (Feature 4)
# ==========================================

@app.route('/admin/abandoned-carts')
@admin_required
def admin_abandoned_carts():
    carts_raw = query_db('SELECT * FROM abandoned_carts ORDER BY updated_at DESC')
    carts = []
    for c in carts_raw:
        item_list = []
        try:
            items = json.loads(c['cart_items_json'])
            if isinstance(items, list):
                item_list = [f"{it.get('name', 'Plant')} ({it.get('qty', 1)}x)" for it in items]
            else:
                item_list = [str(c['cart_items_json'])]
        except Exception:
            item_list = [str(c['cart_items_json'])]

        carts.append({
            'id': c['id'],
            'user_id': c['user_id'],
            'customer_name': c['customer_name'],
            'email': c['email'],
            'phone': c['phone'],
            'items_summary': ", ".join(item_list),
            'total_amount': c['total_amount'],
            'recovered': c['recovered'],
            'updated_at': c['updated_at']
        })

    return render_template('admin/abandoned_carts.html', carts=carts)

@app.route('/admin/abandoned-carts/<int:cart_id>/delete', methods=['POST'])
@admin_required
def admin_abandoned_cart_delete(cart_id):
    execute_db('DELETE FROM abandoned_carts WHERE id = ?', (cart_id,))
    flash('Cart record removed.', 'info')
    return redirect(url_for('admin_abandoned_carts'))

# ==========================================
# ADMIN PHOTO REVIEWS MODERATION (Feature 5)
# ==========================================

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reviews = query_db('''
        SELECT r.*, p.name as plant_name
        FROM reviews r
        JOIN plants p ON r.plant_id = p.id
        ORDER BY r.id DESC
    ''')
    return render_template('admin/reviews_moderation.html', reviews=reviews)

@app.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def admin_review_approve(review_id):
    execute_db('UPDATE reviews SET is_approved = 1 WHERE id = ?', (review_id,))
    flash('Review approved and live with Verified badge.', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/reject', methods=['POST'])
@admin_required
def admin_review_reject(review_id):
    execute_db('UPDATE reviews SET is_approved = 0 WHERE id = ?', (review_id,))
    flash('Review hidden from storefront.', 'info')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def admin_review_delete(review_id):
    execute_db('DELETE FROM reviews WHERE id = ?', (review_id,))
    flash('Review deleted.', 'info')
    return redirect(url_for('admin_reviews'))

# ==========================================
# ADMIN FLASH SALES & PROMOTIONS (Feature 6)
# ==========================================

@app.route('/admin/promotions', methods=['GET', 'POST'])
@admin_required
def admin_promotions():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        discount_pct = float(request.form.get('discount_pct', 10))
        ends_at = request.form.get('ends_at', '').strip()
        banner_text = request.form.get('banner_text', '').strip()
        is_active = 1 if request.form.get('is_active') else 0

        if is_active:
            execute_db('UPDATE flash_sales SET is_active = 0')

        if title and ends_at:
            execute_db('''
                INSERT INTO flash_sales (title, discount_pct, ends_at, banner_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, discount_pct, ends_at, banner_text, is_active))
            flash(f'Flash sale "{title}" created and scheduled!', 'success')
            return redirect(url_for('admin_promotions'))

    sales = query_db('SELECT * FROM flash_sales ORDER BY id DESC')
    return render_template('admin/promotions.html', sales=sales)

@app.route('/admin/promotions/<int:sale_id>/toggle', methods=['POST'])
@admin_required
def admin_promotion_toggle(sale_id):
    sale = query_db('SELECT is_active FROM flash_sales WHERE id = ?', (sale_id,), one=True)
    if sale:
        new_state = 0 if sale['is_active'] else 1
        if new_state == 1:
            execute_db('UPDATE flash_sales SET is_active = 0')
        execute_db('UPDATE flash_sales SET is_active = ? WHERE id = ?', (new_state, sale_id))
        flash('Promotion status updated.', 'info')
    return redirect(url_for('admin_promotions'))

@app.route('/admin/promotions/<int:sale_id>/delete', methods=['POST'])
@admin_required
def admin_promotion_delete(sale_id):
    execute_db('DELETE FROM flash_sales WHERE id = ?', (sale_id,))
    flash('Promotion campaign deleted.', 'info')
    return redirect(url_for('admin_promotions'))

@app.route('/admin/customers')
@admin_required
def admin_customers():
    customers = query_db('''
        SELECT u.*,
               COUNT(o.id) as total_orders,
               COALESCE(SUM(o.total_amount), 0.0) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id AND o.order_status != "Rejected"
        WHERE u.role = "customer"
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = query_db('SELECT * FROM contact_messages ORDER BY created_at DESC')
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/messages/<int:msg_id>/read', methods=['POST'])
@admin_required
def admin_message_mark_read(msg_id):
    execute_db('UPDATE contact_messages SET is_read = 1 WHERE id = ?', (msg_id,))
    flash('Message marked as read.', 'info')
    return redirect(url_for('admin_messages'))

if __name__ == '__main__':
    import webbrowser
    import threading
    import time

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open_new("http://127.0.0.1:5000")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 60)
    print("[GREENI5] Greeni5 Plant Nursery Web Server is LIVE!")
    print("-> Storefront: http://127.0.0.1:5000")
    print("-> Admin Portal: http://127.0.0.1:5000/admin")
    print("-> Press Ctrl+C in this window to stop the server")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
