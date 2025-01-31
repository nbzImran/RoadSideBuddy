from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash


bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User Model for storing user information."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)  # UUID format
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Hashed password
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default="user") #"user" or "admin"
    admin_request = db.Column(db.Boolean, default=False) # Track admin users
    is_admin = db.Column(db.Boolean, default=False) # Add the is_admin
    token = db.Column(db.String, nullable=True)  # Store Firebase ID token



    requests = db.relationship('Request', backref='user', lazy=True)

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password = generate_password_hash(password).decode('utf-8')

    def check_password_hash(self, password):
        """Check the hashed password."""
        return bcrypt.check_password_hash(self.password, password)
    


class Service(db.Model):
    """Service Model for available services."""
    __tablename__ = 'services'

    id = db.Column(db.String(36), primary_key=True)  # UUID format
    type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    requests = db.relationship('Request', backref='service', lazy=True)


class Driver(db.Model):
    """Driver Model for storing driver details."""
    __tablename__ = 'drivers'

    id = db.Column(db.String(36), primary_key=True)  # UUID format
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    completed_services = db.Column(db.Integer, default=0)
    location = db.Column(db.JSON, nullable=True)  # Store location as JSON (lat, lng)

    requests = db.relationship('Request', backref='driver', lazy=True)


class Request(db.Model):
    """Request Model for service requests."""
    __tablename__ = 'requests'

    id = db.Column(db.String(36), primary_key=True)  # UUID format
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String(36), db.ForeignKey('drivers.id'), nullable=True)
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)
    location = db.Column(db.JSON, nullable=True)  # Store location as JSON (lat, lng)
    status = db.Column(db.String(50), default="Pending")  # Pending, Completed, Canceled
    cost = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship('Rating', backref='request', lazy=True)


class Rating(db.Model):
    """Rating Model for service feedback."""
    __tablename__ = 'ratings'

    id = db.Column(db.String(36), primary_key=True)  # UUID format
    request_id = db.Column(db.String(36), db.ForeignKey('requests.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def connect_db(app):
    """Connect the database to the Flask app."""
    db.app = app
    db.init_app(app)
