import os


class Config:
    FIREBASE_CREDENTIALS = 'backend/firebase/roadsidebuddy-35064-firebase-adminsdk-fbsvc-99d790f84b.json'
    DATABASE_URL = ("FIREBASE_DATABASE_URL", "https://roadsidebuddy-35064-default-rtdb.firebaseio.com/")
    SECRET_KEY = os.getenv("SECRET_KEY", "its a secret key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///roadside_buddy.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "your-mapbox-token")
    CLICKSEND_USERNAME = os.getenv("CLICKSEND_USERNAME", "")
    CLICKSEND_API_KEY = os.getenv("CLICKSEND_API_KEY", "")
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'admin@example.com')  # Admin email
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'yourpassword')  # App-specific password
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')  # Recipient (admin) email


Config = Config()