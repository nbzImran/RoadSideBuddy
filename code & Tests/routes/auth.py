from flask import Blueprint, request, jsonify, current_app
from models.models import db, User
import uuid
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from firebase_admin import auth

auth_bp = Blueprint("auth", __name__)

def firebase_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Authorization token is missing!"}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
        except auth.ExpiredIdTokenError:
            return jsonify({"message": "Token has expired!"}), 401
        except auth.InvalidIdTokenError:
            return jsonify({"message": "Invalid token!"}), 401
        except Exception as e:
            return jsonify({"message": "Authentication error!", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        firebase_user = auth.create_user(
            email=data['email'],
            password=data['password'],
            display_name=data.get('name')
        )
        new_user = User(
            id=firebase_user.uid,
            name=data.get('name'),
            email=data['email'],
            password=generate_password_hash(data['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully!", "user_id": firebase_user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        token = jwt.encode({
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"message": "Login successful!", "token": token}), 200
    return jsonify({"message": "Invalid email or password"}), 401

@auth_bp.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = auth.get_user(user_id)
        return jsonify({
            "user_id": user.uid,
            "name": user.display_name,
            "email": user.email
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@auth_bp.route('/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    try:
        data = request.json
        user = auth.update_user(
            user_id,
            email=data.get('email'),
            display_name=data.get('name'),
            password=data.get('password')
        )
        return jsonify({"message": "Profile updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/protected', methods=['GET'])
@firebase_token_required
def protected_route():
    return jsonify({"message": f"Welcome, user {request.user['email']}!"})
