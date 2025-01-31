from flask import Blueprint, jsonify

driver_bp = Blueprint('driver', __name__)

@driver_bp.route('/track-driver/<request_id>', methods=['GET'])
def track_driver(request_id):
    # mock driver data; replace with realtime logic

    driver_data = {
        "driver_id": "unique_driver_id",
        "Location": {
            "latitude": 40.7128,
            "longtitude": -74.0060
        },
        "eta": "15 minutes"
    }
    return jsonify(driver_data), 200
    