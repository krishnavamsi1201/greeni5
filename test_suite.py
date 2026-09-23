import unittest
import sqlite3
from app import app
from database import query_db, get_db

class Greeni5TestSuite(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

    def test_01_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Greeni5', response.data)
        self.assertIn(b'Indoor Plants', response.data)
        self.assertIn(b'Featured Plants', response.data)
        print("[OK] Home page loaded with categories and featured plants")

    def test_02_catalog_and_filters(self):
        # All catalog
        resp = self.client.get('/catalog')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'All Botanical Varieties', resp.data)

        # Filter by category
        resp_cat = self.client.get('/catalog?category=indoor-plants')
        self.assertEqual(resp_cat.status_code, 200)
        self.assertIn(b'Monstera Deliciosa', resp_cat.data)

        # Filter by search
        resp_search = self.client.get('/catalog?search=Snake')
        self.assertEqual(resp_search.status_code, 200)
        self.assertIn(b'Snake Plant', resp_search.data)

        # Filter by sort price_asc
        resp_sort = self.client.get('/catalog?sort=price_asc')
        self.assertEqual(resp_sort.status_code, 200)
        print("[OK] Catalog, search, and category filters verified")

    def test_03_plant_details(self):
        resp = self.client.get('/plant/monstera-deliciosa')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Monstera Deliciosa', resp.data)
        self.assertIn(b'Sunlight', resp.data)
        self.assertIn(b'Watering', resp.data)
        self.assertIn(b'Customer Reviews', resp.data)
        print("[OK] Plant details page with care guide and reviews verified")

    def test_04_cart_operations(self):
        # Add to cart
        resp = self.client.post('/cart/add/1', data={'quantity': 2}, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['cart_count'], 2)

        # View cart
        resp_cart = self.client.get('/cart')
        self.assertEqual(resp_cart.status_code, 200)
        self.assertIn(b'Monstera Deliciosa', resp_cart.data)

        # Update cart quantity
        resp_up = self.client.post('/cart/update', data={'plant_id': 1, 'quantity': 3}, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(resp_up.status_code, 200)
        self.assertEqual(resp_up.get_json()['cart_count'], 3)
        print("[OK] Cart add, view, and quantity updates verified")

    def test_05_checkout_and_order_placement(self):
        with self.client:
            # Login as customer
            login_resp = self.client.post('/login', data={'email': 'customer@greeni5.com', 'password': 'Customer@123'}, follow_redirects=True)
            self.assertEqual(login_resp.status_code, 200)

            # Add plant to cart
            self.client.post('/cart/add/2', data={'quantity': 1})

            # Place order
            order_data = {
                'customer_name': 'Test Buyer',
                'customer_email': 'buyer@test.com',
                'customer_phone': '+91 9988776655',
                'shipping_address': '123 Test Garden Way',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560001',
                'payment_method': 'COD',
                'notes': 'Please call before delivery'
            }
            order_resp = self.client.post('/checkout', data=order_data, follow_redirects=False)
            self.assertEqual(order_resp.status_code, 302)
            self.assertIn('/order/success/', order_resp.location)

            # Follow to success page
            success_resp = self.client.get(order_resp.location)
            self.assertEqual(success_resp.status_code, 200)
            self.assertIn(b'Order Successfully Placed', success_resp.data)

            # Extract order number
            order_number = order_resp.location.split('/')[-1]

            # Track order
            track_resp = self.client.get(f'/order/track/{order_number}')
            self.assertEqual(track_resp.status_code, 200)
            self.assertIn(b'Pending', track_resp.data)
            print(f"[OK] Checkout and Order Placement verified (Order #{order_number})")

    def test_06_admin_workflow(self):
        with self.client:
            # Non-admin access check
            unauth = self.client.get('/admin/dashboard')
            self.assertEqual(unauth.status_code, 302)

            # Admin login
            login_adm = self.client.post('/login', data={'email': 'admin@greeni5.com', 'password': 'Admin@123'}, follow_redirects=True)
            self.assertEqual(login_adm.status_code, 200)

            # Admin dashboard
            dash_resp = self.client.get('/admin/dashboard')
            self.assertEqual(dash_resp.status_code, 200)
            self.assertIn(b'Nursery Business Overview', dash_resp.data)
            self.assertIn(b'Total Plants', dash_resp.data)

            # Admin plants list
            plants_resp = self.client.get('/admin/plants')
            self.assertEqual(plants_resp.status_code, 200)
            self.assertIn(b'Botanical Plant Inventory', plants_resp.data)

            # Admin add new plant
            new_plant_data = {
                'name': 'Golden Pothos Money Plant',
                'category_id': 1,
                'price': 349.0,
                'discount_price': 299.0,
                'stock': 20,
                'description': 'Lush trailing vine with heart-shaped leaves.',
                'sunlight': 'Low to medium indirect light',
                'watering': 'Water once a week',
                'temperature': '18C - 30C',
                'soil': 'Porous potting soil',
                'difficulty': 'Very Easy',
                'is_featured': '1',
                'image_urls': 'https://images.unsplash.com/photo-1545241047-6083a3684587?w=800'
            }
            add_resp = self.client.post('/admin/plants/add', data=new_plant_data, follow_redirects=True)
            self.assertEqual(add_resp.status_code, 200)
            self.assertIn(b'Golden Pothos Money Plant', add_resp.data)

            # Admin update order status
            orders_resp = self.client.get('/admin/orders')
            self.assertEqual(orders_resp.status_code, 200)
            self.assertIn(b'All Nursery Orders', orders_resp.data)

            # Update first order status to Shipped
            status_update = self.client.post('/admin/orders/1/status', data={'order_status': 'Shipped'}, follow_redirects=True)
            self.assertEqual(status_update.status_code, 200)
            self.assertIn(b'Order status updated to Shipped', status_update.data)

            # Admin customers view
            cust_resp = self.client.get('/admin/customers')
            self.assertEqual(cust_resp.status_code, 200)
            self.assertIn(b'Registered Plant Customers', cust_resp.data)

            print("[OK] Full Admin workflow (Dashboard, Plant CRUD, Order status change, Customers) verified")

    def test_07_contact_and_review(self):
        # Contact form submission
        contact_resp = self.client.post('/contact', data={
            'name': 'Gardener Priya',
            'email': 'priya@example.com',
            'subject': 'Care Inquiry',
            'message': 'Can I grow Bougainvillea in a 12-inch pot?'
        }, follow_redirects=True)
        self.assertEqual(contact_resp.status_code, 200)
        self.assertIn(b'Thank you for reaching out', contact_resp.data)

        # Review submission
        rev_resp = self.client.post('/review/add/1', data={
            'user_name': 'Meera Sen',
            'rating': '5',
            'comment': 'Stunning plant! Very well packaged.'
        }, follow_redirects=True)
        self.assertEqual(rev_resp.status_code, 200)
        self.assertIn(b'Your review has been published', rev_resp.data)
        print("[OK] Contact form and Review submission verified")

if __name__ == '__main__':
    unittest.main()
