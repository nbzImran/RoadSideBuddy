from models.models import db, Service
from app import app



with app.app_context():
    services = [
        Service(id="tire_change", type="Tire Change", price=50.0, description="Flat tire replacement."),
        Service(id="battery_service", type="Battery Service", price=70.0, description="Jump start or replace your battery."),
        Service(id="lockout", type="Lockout", price=40.0, description="Unlock your car safely."),
        Service(id="fuel_delivery", type="Fuel Delivery", price=30.0, description="Deliver fuel to your location.")
    ]
    db.session.bulk_save_objects(services)
    db.session.commit()
