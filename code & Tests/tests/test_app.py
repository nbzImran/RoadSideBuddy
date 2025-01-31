import unittest
from app import app, db, auth
from models.models import User, Service

class RoadSideBuddyTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Initialize the database
        db.create_all()

        # Test user credentials
        test_email = "test@example.com"
        test_password = "TestPass123"

        # Create Firebase user if not exists
        try:
            auth.create_user_with_email_and_password(test_email, test_password)
            print(f"Test Firebase user created: {test_email}")
        except Exception as e:
            print(f"Firebase user already exists or error: {e}")

        # Add user to the local database
        test_user = User(id="123", name="Test User", email=test_email, password=test_password)
        db.session.add(test_user)
        db.session.commit()




    def tearDown(self):
        """Clean up database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Helper Functions
    def login(self, email, password):
        """Helper function to log in a user."""
        return self.client.post('/login', data=dict(email=email, password=password), follow_redirects=True)

    def logout(self):
        """Helper function to log out a user."""
        return self.client.get('/logout', follow_redirects=True)

    # Test Cases
    def test_home_page(self):
        """Test the home page is accessible."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_signup(self):
        """Test user signup."""
        response = self.client.post('/signup', data=dict(
            email="newuser@example.com",
            password="password123",
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_logout(self):
       
        """Test login and logout."""
        response = self.client.post('/login', data=dict(
            email="newuser@example.com",
            password="password123"
        ), follow_redirects=True)

        # Debugging: Print the response if the login fails
        print(response.data.decode())

        if b"TOO_MANY_ATTEMPTS_TRY_LATER" in response.data:
            self.fail("Login blocked due to too many attempts. Wait or reset user status.")
        else:
            self.assertIn(b"Login successful!", response.data)

        # Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"You have been logged out.", response.data)

  
    def test_non_admin_access(self):
        """Test that a non-admin cannot access admin features."""
        # Login as regular user
        self.login("test@example.com", "hashed_password")
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"Access denied. Admins only.", response.data)

    def test_service_creation(self):
        """Test creating and fetching services."""
        with app.app_context():
            service = Service(id="tire_change", type="Tire Change", price=50.0, description="Flat tire replacement.")
            db.session.add(service)
            db.session.commit()

            # Verify service exists
            saved_service = Service.query.filter_by(id="tire_change").first()
            self.assertIsNotNone(saved_service)
            self.assertEqual(saved_service.type, "Tire Change")

    def test_request_service(self):
        """Test requesting a service."""
        # Step 1: Log in as a test user
        self.login("newuser@example.com", "password123")

        # Step 2: Add service to database
        with app.app_context():
            if not Service.query.filter_by(id="tire_change").first():
                service = Service(id="tire_change", type="Tire Change", price=50.0, description="Flat tire replacement.")
                db.session.add(service)
                db.session.commit()


       # Step 3: Request a service
        response = self.client.post('/request-service?service_id=tire_change', data={
            "location": "123 Main St, Albany, NY"
            }, follow_redirects=True)
    
        # Debugging: Print response if test fails
        print(response.data.decode())

        # Step 4: Check if request was successful
        self.assertIn(b" Service &#39;Tire Change&#39; requested successfully!", response.data)

if __name__ == "__main__":
    unittest.main()
