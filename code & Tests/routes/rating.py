from flask import Blueprint, request, jsonify
from models.models import db, Rating
import uuid

rating_bp = Blueprint('rating', __name__)

@rating_bp.route('/rate-service', methods=['POST'])
def rate_service():
    data = request.json
    try:
        new_rating = Rating(
            id=str(uuid.uuid4()),
            request_id=data['request_id'],
            rating=data['rating'],
            review=data.get('review')
        )
        db.session.add(new_rating)
        db.session.commit()

        return jsonify({"message": "Thank you for your feedback!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
