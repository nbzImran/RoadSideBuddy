from flask import Blueprint, jsonify
from models.models import Request

user_bp = Blueprint("user", __name__)

@user_bp.route("/service-history/<user_id>", methods=["GET"])
def service_history(user_id):
    try:
        # Fetch service history for the user
        requests = Request.query.filter_by(user_id=user_id).all()
        history = [
            {
                "request_id": req.id,
                "service_id": req.service_id,
                "status": req.status,
                "cost": req.cost,
                "created_at": req.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for req in requests
        ]
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
