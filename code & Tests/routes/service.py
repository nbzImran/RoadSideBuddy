from flask import Blueprint, request, jsonify
from models.models import db, Service, Request
import uuid

service_bp = Blueprint("service", __name__)

@service_bp.route("/request-service", methods=["POST"])
def request_service():
    """
    Handle a POST request to create a new service request.
    Expects JSON data with 'user_id', 'service_type', and 'location'.
    """
    try:
        # Parse and validate request data
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        user_id = data.get("user_id")
        service_type = data.get("service_type")
        location = data.get("location")
        cost = data.get("cost", 0.0)  # Default to 0.0 if not provided

        if not user_id or not service_type or not location:
            return jsonify({"error": "Missing required fields (user_id, service_type, location)"}), 400

        # Check if the service type exists in the database
        service = Service.query.filter_by(id=service_type).first()
        if not service:
            return jsonify({"error": f"Service type '{service_type}' does not exist"}), 404

        # Create a new request object
        new_request = Request(
            id=str(uuid.uuid4()),
            user_id=user_id,
            Service_id=service.id,
            location=location,
            status="Pending",
            cost=cost if cost > 0 else service.price  # Use provided cost or service's default price
        )

        # Save to the database
        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            "message": "Service requested successfully",
            "request_id": new_request.id
        }), 201

    except Exception as e:
        # Log the error and return a server error response
        print(f"Error creating service request: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500
