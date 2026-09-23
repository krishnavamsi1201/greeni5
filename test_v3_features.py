import requests
import sqlite3
import unittest
import urllib.parse

BASE_URL = "http://127.0.0.1:5000"

def get_db():
    conn = sqlite3.connect('greeni5.db')
    conn.row_factory = sqlite3.Row
    return conn

class TestGreeni5V3Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s_admin = requests.Session()
        login_resp = cls.s_admin.post(f"{BASE_URL}/login", data={
            'email': 'admin@greeni5.com',
            'password': 'Admin@123'
        }, allow_redirects=True)
        assert login_resp.status_code == 200, "Admin login failed"

        cls.s_user = requests.Session()

    def test_01_plant_quiz(self):
        """Test Feature 1: 'Find My Perfect Plant' Interactive Quiz"""
        r = self.s_user.get(f"{BASE_URL}/plant-quiz?location=indoor&sunlight=indirect&experience=beginner")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Find Your", r.text)
        self.assertIn("Perfect Living Plant", r.text)
        self.assertIn("Top Recommended Plants For You", r.text)
        self.assertIn("Retake Quiz", r.text)

    def test_02_gift_order_checkout(self):
        """Test Feature 3: 'Gift a Plant' Checkout with Greeting & Wrap Fee"""
        db = get_db()
        plant = db.execute("SELECT * FROM plants WHERE is_featured = 1 ORDER BY id ASC LIMIT 1").fetchone()
        plant_id = plant['id']
        db.close()

        # Add plant to cart
        r_cart = self.s_user.post(f"{BASE_URL}/cart/add/{plant_id}", data={'quantity': 1}, allow_redirects=True)
        self.assertEqual(r_cart.status_code, 200)

        # Checkout with Gift Option
        checkout_data = {
            'customer_name': 'Vikram Aditya',
            'customer_email': 'vikram@example.com',
            'customer_phone': '9876501234',
            'shipping_address': 'Villa 14, Palm Meadows, Whitefield',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560066',
            'payment_method': 'COD',
            'notes': 'Please ring before delivery',
            'is_gift': '1',
            'gift_recipient_name': 'Priya Sharma',
            'gift_message': 'Happy Birthday Priya! Wishing you prosperity with this beautiful green plant!'
        }
        r_chk = self.s_user.post(f"{BASE_URL}/checkout", data=checkout_data, allow_redirects=True)
        self.assertEqual(r_chk.status_code, 200)
        self.assertIn("Order #GRN-", r_chk.text)

        # Verify DB entry
        db = get_db()
        order = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        self.assertEqual(order['is_gift'], 1)
        self.assertEqual(order['gift_recipient_name'], 'Priya Sharma')
        self.assertIn('Happy Birthday Priya', order['gift_message'])
        self.assertEqual(order['gift_wrap_fee'], 49.0)

    def test_03_printable_invoice_gift_card(self):
        """Test Feature 3: Printable Tax Invoice / Slip has Gift Card Section"""
        db = get_db()
        order = db.execute("SELECT id, order_number FROM orders WHERE is_gift = 1 ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        order_id = order['id']

        r_inv = self.s_admin.get(f"{BASE_URL}/admin/orders/{order_id}/invoice")
        self.assertEqual(r_inv.status_code, 200)
        self.assertIn("SPECIAL GIFT PACKING & GREETING CARD", r_inv.text)
        self.assertIn("Priya Sharma", r_inv.text)
        self.assertIn("Gift Packaging & Card", r_inv.text)

    def test_04_watering_schedule_and_whatsapp(self):
        """Test Feature 4: WhatsApp Watering Calendar on Order Tracking & Dashboard"""
        db = get_db()
        order = db.execute("SELECT id, order_number FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        order_number = order['order_number']

        # Check Order Tracking page
        r_trk = self.s_user.get(f"{BASE_URL}/order/track/{order_number}")
        self.assertEqual(r_trk.status_code, 200)
        self.assertIn("Living Plant Care & Watering Calendar", r_trk.text)
        self.assertIn("Sync Schedule to WhatsApp", r_trk.text)
        self.assertIn("https://wa.me/?text=", r_trk.text)

        # Login as customer and check Dashboard
        s_cust = requests.Session()
        s_cust.post(f"{BASE_URL}/login", data={'email': 'customer@greeni5.com', 'password': 'Customer@123'})
        r_dash = s_cust.get(f"{BASE_URL}/dashboard")
        self.assertEqual(r_dash.status_code, 200)
        self.assertIn("My Dashboard", r_dash.text)

if __name__ == '__main__':
    unittest.main()
