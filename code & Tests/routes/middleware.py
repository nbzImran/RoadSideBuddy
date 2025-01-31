from pyrebase import initialize_app as pyrebase_init
from functools import wraps
from flask import request, jsonify
from firebase_admin import auth, datetime
from authentication import firebase_config

firebase = pyrebase_init(firebase_config)
database = firebase.database()

def firebase_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        print (f"the token: {token}")
        print(f"Headers: {request.headers}")
        if not token:
            print("Authorization token missing.")
            return jsonify({"message": f"Authorization token is missing! {token}"}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
            print(f"Token verified for user: {decoded_token['uid']}")

             # Store token details in Firebase Realtime Database
            user_data = {
                "uid": decoded_token['uid'],
                "email": decoded_token.get('email', 'N/A'),
                "auth_time": datetime.fromtimestamp(decoded_token['auth_time']).isoformat(),
                "issued_at": datetime.fromtimestamp(decoded_token['iat']).isoformat(),
                "expires_at": datetime.fromtimestamp(decoded_token['exp']).isoformat(),
                "ip": request.remote_addr,
                "timestamp": datetime.utcnow().isoformat(),
            }

            database.child("auth_log").push(user_data)
            print("User authentication log stored in firebase realtime database.")    

        except auth.ExpiredIdTokenError:
            print("Token has expired.")
            return jsonify({"message": "Token has expired!"}), 401
        except auth.InvalidIdTokenError:
            print("Invalid token.")
            return jsonify({"message": "Invalid token!"}), 401
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return jsonify({"message": "Authentication error!", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function
