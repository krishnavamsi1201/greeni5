import requests
import json
import unittest

BASE_URL = "http://127.0.0.1:5000"

import sqlite3

def get_db():
    conn = sqlite3.connect('greeni5.db')
    conn.row_factory = sqlite3.Row
    return conn

class TestGreeni5V2Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s_admin = requests.Session()
        login_resp = cls.s_admin.post(f"{BASE_URL}/login", data={
            'email': 'admin@greeni5.com',
            'password': 'Admin@123'
        }, allow_redirects=True)
        assert login_resp.status_code == 200, "Admin login failed"

        cls.s_user = requests.Session()

    def test_01_admin_addons_management(self):
        """Test Feature 2: Admin Add-ons Combos CRUD"""
        r = self.s_admin.get(f"{BASE_URL}/admin/addons")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Add New Plant Care Add-on Combo", r.text)

        # Add an add-on
        r_add = self.s_admin.post(f"{BASE_URL}/admin/addons", data={
            'name': 'Organic Neem Cake Pellets (500g)',
            'price': '89.00',
            'category': 'Fertilizers',
            'image_url': 'https://images.unsplash.com/photo-1585336261026-c56784d85834?w=400',
            'description': 'Protects roots against nematodes and improves nitrogen retention.'
        }, allow_redirects=True)
        self.assertEqual(r_add.status_code, 200)
        self.assertIn("Organic Neem Cake Pellets", r_add.text)

    def test_02_add_plant_with_pot_variants(self):
        """Test Feature 1: Pot Type & Size Variants"""
        plant_data = {
            'name': 'Golden Pothos Deluxe',
            'category_id': '1',
            'price': '199.00',
            'discount_price': '179.00',
            'stock': '30',
            'description': 'Heart-shaped variegated green vine for air purification.',
            'sunlight': 'Indirect sunlight',
            'watering': 'Once a week',
            'temperature': '20C - 32C',
            'soil': 'Porous potting mix',
            'difficulty': 'Very Easy',
            'is_featured': '1',
            'is_bestseller': '1',
            'image_urls': 'https://images.unsplash.com/photo-1545241047-6083a3684587?w=800',
            'variant_name[]': ['4-inch Nursery Pot', '6-inch White Ceramic Pot', '8-inch Self-Watering Pot'],
            'pot_type[]': ['Plastic', 'Ceramic', 'Self-Watering'],
            'variant_extra_price[]': ['0.00', '150.00', '250.00'],
            'variant_stock[]': ['20', '10', '5']
        }
        r = self.s_admin.post(f"{BASE_URL}/admin/plants/add", data=plant_data, allow_redirects=True)
        self.assertEqual(r.status_code, 200)

        # Check storefront plant details page
        r_det = self.s_user.get(f"{BASE_URL}/plant/golden-pothos-deluxe")
        self.assertEqual(r_det.status_code, 200)
        self.assertIn("6-inch White Ceramic Pot", r_det.text)
        self.assertIn("Frequently Bought Together", r_det.text)

    def test_03_cart_with_variants_and_addons(self):
        """Test Cart with Pot Variant and Add-on Combo"""
        db = get_db()
        plant = db.execute("SELECT id FROM plants WHERE slug = 'golden-pothos-deluxe'").fetchone()
        self.assertIsNotNone(plant)
        plant_id = plant['id']
        variant = db.execute("SELECT id FROM plant_variants WHERE plant_id = ? ORDER BY id DESC LIMIT 1", (plant_id,)).fetchone()
        variant_id = variant['id'] if variant else ''
        addon = db.execute("SELECT id FROM addons LIMIT 1").fetchone()
        addon_id = addon['id'] if addon else 1
        db.close()

        # Add to cart with variant
        r_cart = self.s_user.post(f"{BASE_URL}/cart/add/{plant_id}", data={
            'quantity': 1,
            'variant_id': variant_id
        }, allow_redirects=True)
        self.assertEqual(r_cart.status_code, 200)

        # Add an add-on combo
        r_addon = self.s_user.get(f"{BASE_URL}/cart/add-addon/{addon_id}", allow_redirects=True)
        self.assertEqual(r_addon.status_code, 200)

        # View cart
        r_view = self.s_user.get(f"{BASE_URL}/cart")
        self.assertEqual(r_view.status_code, 200)
        self.assertIn("Order Summary", r_view.text)

    def test_04_abandoned_cart_tracking_and_whatsapp(self):
        """Test Feature 4: Abandoned Cart Tracking & 1-Click WhatsApp"""
        r_admin = self.s_admin.get(f"{BASE_URL}/admin/abandoned-carts")
        self.assertEqual(r_admin.status_code, 200)
        self.assertIn("Abandoned Cart Tracking", r_admin.text)

    def test_05_checkout_and_printable_invoice(self):
        """Test Feature 7: Checkout, Order creation, and Printable Invoice"""
        checkout_data = {
            'customer_name': 'Ananya Reddy',
            'customer_email': 'ananya@example.com',
            'customer_phone': '9876543210',
            'shipping_address': 'Flat 402, Green Meadows, Jubilee Hills',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500033',
            'payment_method': 'COD',
            'notes': 'Please ring doorbell on delivery'
        }
        r_checkout = self.s_user.post(f"{BASE_URL}/checkout", data=checkout_data, allow_redirects=True)
        self.assertEqual(r_checkout.status_code, 200)
        self.assertIn("Order #GRN-", r_checkout.text)

        # Get latest order id
        db = get_db()
        latest_order = db.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        order_id = latest_order['id']

        # Test Invoice Print for Admin
        r_inv = self.s_admin.get(f"{BASE_URL}/admin/orders/{order_id}/invoice")
        self.assertEqual(r_inv.status_code, 200)
        self.assertIn("TAX INVOICE / SLIP", r_inv.text)
        self.assertIn("Print Packing Slip & Invoice", r_inv.text)
        self.assertIn("Jubilee Hills", r_inv.text)

    def test_06_courier_tracking_and_damage_claim(self):
        """Test Feature 3 & 7: Courier AWB Dispatch & Customer Transit Damage Claim"""
        db = get_db()
        latest_order = db.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        order_id = latest_order['id']

        # Admin updates tracking
        r_track_update = self.s_admin.post(f"{BASE_URL}/admin/orders/{order_id}/tracking", data={
            'courier_name': 'Delhivery Air Climate',
            'tracking_number': 'DEL123456789IN'
        }, allow_redirects=True)
        self.assertEqual(r_track_update.status_code, 200)

        # Customer submits replacement claim
        claim_data = {
            'plant_name': 'Golden Pothos Deluxe',
            'reason': 'Damaged leaf stems on unboxing'
        }
        r_claim = self.s_user.post(f"{BASE_URL}/orders/{order_id}/claim-replacement", data=claim_data, allow_redirects=True)
        self.assertEqual(r_claim.status_code, 200)
        self.assertIn("Replacement Claim has been submitted", r_claim.text)

        # Admin reviews claims
        r_adm_claims = self.s_admin.get(f"{BASE_URL}/admin/replacements")
        self.assertEqual(r_adm_claims.status_code, 200)
        self.assertIn("Golden Pothos Deluxe", r_adm_claims.text)

    def test_07_flash_sale_and_photo_reviews(self):
        """Test Feature 5 & 6: Flash Sale Timer & Photo Review Moderation"""
        db = get_db()
        plant = db.execute("SELECT id FROM plants WHERE slug = 'golden-pothos-deluxe'").fetchone()
        plant_id = plant['id']
        db.close()

        # Create Flash Sale
        sale_data = {
            'title': 'Monsoon Green Blast',
            'discount_pct': '15',
            'ends_at': '2026-12-31T23:59',
            'banner_text': 'Monsoon Green Blast: 15% OFF Sitewide! Free shipping on all plants!',
            'is_active': '1'
        }
        r_sale = self.s_admin.post(f"{BASE_URL}/admin/promotions", data=sale_data, allow_redirects=True)
        self.assertEqual(r_sale.status_code, 200)

        # Check storefront top notice bar has countdown timer
        r_home = self.s_user.get(f"{BASE_URL}/")
        self.assertEqual(r_home.status_code, 200)
        self.assertIn("flash-sale-timer", r_home.text)
        self.assertIn("Monsoon Green Blast", r_home.text)

        # Submit photo review
        r_rev = self.s_user.post(f"{BASE_URL}/reviews/add/{plant_id}", data={
            'user_name': 'Kavya S',
            'rating': '5',
            'comment': 'Stunning glossy leaves! Arrived perfectly green and thriving on my balcony.'
        }, allow_redirects=True)
        self.assertEqual(r_rev.status_code, 200)

        # Check admin reviews moderation
        r_adm_rev = self.s_admin.get(f"{BASE_URL}/admin/reviews")
        self.assertEqual(r_adm_rev.status_code, 200)
        self.assertIn("Kavya S", r_adm_rev.text)

if __name__ == '__main__':
    unittest.main()
