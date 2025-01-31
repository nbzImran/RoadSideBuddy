import os
from flask import Flask, request, redirect, url_for, flash, render_template, session
from forms import SignupForm, LoginForm, ProfileForm, ServiceForm, EmailForm
from flask_debugtoolbar import DebugToolbarExtension
from firebase_admin import credentials, initialize_app, auth as admin_auth, datetime, db as rdb
from pyrebase import initialize_app as pyrebase_init
from mapbox import Directions
from models.models import connect_db, User, Service, db
from config import Config
from authentication import firebase_config
from flask_login import current_user, LoginManager, logout_user, login_user
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
load_dotenv()





app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)


#Redirect to login page if unauthorized
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user with ID:{user_id}")
    return User.query.get(user_id)

connect_db(app)
with app.app_context():
    db.drop_all()
    db.create_all()



#Debug Toolbar Configuration
app.debug = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', "its a secret")
print(f"SECRET_KEY: {app.config['SECRET_KEY']}")

# app.config['DEBUG_TB_INTERCEP_REDIRECTS'] = False
# toolbar = DebugToolbarExtension(app)



# Fucntions to set admin role using custom claims
def set_admin_role(uid):
    try:
        admin_auth.set_custom_user_claims(uid, {"role": "admin"})
        user_record = admin_auth.get_user('Wreg2mrlUhNVFHlhrnO8Bjnof2P2')
        print(user_record.custom_claims)  # Should output {'role': 'admin'}

        print(f"Admin role assigned to user {uid}.")
    except Exception as e:
        print(f"Error setting admin role: {e}")

def is_admin():
    """Check if the current user has an admin role."""
    try:
        token = session.get('token')  # Retrieve the token from the session
        if not token:
            print(f"Token is not available. {token}")
            return False

        # Verify the ID token
        decoded_token = admin_auth.verify_id_token(token)
        print(f"Decoded token: {decoded_token}")  # Log for debugging
        return decoded_token.get("role") == "admin"
    except Exception as e:
        print(f"Error verifying token: {e}")
        return False







# pyrebase firebase init
firebase = pyrebase_init(firebase_config)
database = firebase.database()
auth = firebase.auth()

# Firebase Initialization
cred = credentials.Certificate('//Users/imrannabizada/Desktop/RoadSideBuddy/code & Tests/firebase/roadsidebuddy-35064-firebase-adminsdk-fbsvc-99d790f84b.json')
firebase_app = initialize_app(cred, {"databaseURL": [Config.DATABASE_URL]})



# Register Blupints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.service import service_bp



app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(service_bp, url_prefix="/service")



@app.route('/')
def home():
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
    return render_template('home.html', admin_email=admin_email)

from seed_services import services

with app.app_context():
    if not Service.query.first():  # Check if the Service table is empty
        print("Seeding the Service table...")
        services = [
            Service(id="tire_change", type="Tire Change", price=50.0, description="Flat tire replacement."),
            Service(id="battery_service", type="Battery Service", price=70.0, description="Jump start or replace your battery."),
            Service(id="lockout", type="Lockout", price=40.0, description="Unlock your car safely."),
            Service(id="fuel_delivery", type="Fuel Delivery", price=30.0, description="Deliver fuel to your location.")
        ]
        db.session.bulk_save_objects(services)
        db.session.commit()
        print("Service table seeded!")



    


################################################################
# Create and Request routes

# Route for requesting a roadside service
@app.route('/request-service', methods=['GET', 'POST'])
def request_service():
    form = ServiceForm()

    service_id = request.args.get('service_id')
    service = Service.query.filter_by(id=service_id).first()
    print(f"Service ID received: {service_id}")  # Debugging



    # ref = rdb.reference('request_service')
    

    # Retrieve the selected service from the database
    print(f"Service found: {service}")  # Debugging


    if request.method == 'POST':
        # Use the authenticated user's ID``
        user_id = current_user.id
        location = request.form.get('location')
        print(f"user: {user_id}, location: {location}")


        
        # Create request data
        request_data = {
                "user_id": user_id,
                "service_id": service.id,
                "location": location,
                "status": "Pending",
                "cost": service.price,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
    
        #Store in Firebase Realtime Database
        try:
            firebase.database().child('requests').push(request_data)
            flash(f"Service '{service.type}' requested successfully! Total cost: ${service.price:.2f}", "success")
        except Exception as e:
            print(f"Firebase Database Error: {e}")
            flash("Error storing your request. Please try again.", "danger")

        return redirect(url_for('home'))
    


    return render_template('request_service.html', service=service, form=form)


# Route for viewing user request history
@app.route('/history', methods=['GET'])
def history():
    try:
        # Get user ID from the current session or authenticated user
        user_id = current_user.id  # Ensure Flask-Login is set up

        # Fetch all requests for the logged-in user
        requests_ref = firebase.database().child("requests").order_by_child("user_id").equal_to(user_id).get()
        
        # Format data for rendering
        service_history = []
        if requests_ref.each():
            for request in requests_ref.each():
                service_history.append(request.val())
        
        return render_template('history.html', service_history=service_history)
    except Exception as e:
        print(f"Error fetching service history: {e}")
        flash("Could not fetch your service history. Please try again later.", "danger")
        return redirect(url_for('home'))
    


@app.route('/service-details/<service_id>', methods=['GET'])
def service_details(service_id):
    try:
        # Fetch the service details from Firebase Realtime Database
        service_data = database.child("requests").order_by_child("service_id").equal_to(service_id).get()

        # Check if the service exists
        if not service_data.each():
            flash("Service details not found.", "danger")
            return redirect(url_for('history'))

        # Get the service details (assuming a single service matches)
        service = next(iter(service_data.each())).val()

        return render_template('service_details.html', service=service)
    except Exception as e:
        print(f"Error fetching service details: {e}")
        flash("Error fetching service details. Please try again.", "danger")
        return redirect(url_for('history'))

    


@app.route('/cancel-service/<service_id>', methods=['POST'])
def cancel_service(service_id):
    try:
        # Fetch the service request(s) associated with the given service_id
        requests_ref = database.child("requests").order_by_child("service_id").equal_to(service_id).get()

        if not requests_ref.each():
            flash("No service requests found for the given service ID.", "danger")
            return redirect(url_for('history'))

        # Update the status of all matching requests to "Canceled"
        for request_item in requests_ref.each():
            database.child("requests").child(request_item.key()).update({"status": "Canceled"})

        flash("Service requests canceled successfully.", "success")
    except Exception as e:
        print(f"Error canceling service requests: {e}")
        flash("Error canceling the service requests. Please try again.", "danger")

    return redirect(url_for('history'))


##################################################################
# Admin user and delete

# Route to request admin privileges
@app.route('/request-admin', methods=['GET', 'POST'])
def request_admin():
    if not current_user.is_authenticated:
        flash("You need to be logged in to request admin access.", "danger")
        return redirect(url_for('login'))

    if current_user.role == "admin":
        flash("You are already an admin.", "info")
        return redirect(url_for('home'))

    if current_user.admin_request:
        flash("You have already requested admin access. Please wait for approval.", "info")
        return redirect(url_for('home'))

    # Mark the user as having requested admin access
    current_user.admin_request = True
    db.session.commit()

    flash("Your request to become an admin has been submitted. An admin will review your request.", "success")
    return redirect(url_for('home'))


@app.route('/admin/users', methods=['GET'])
def list_users():
    if not current_user.is_authenticated or not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Use Firebase Admin SDK to list all users
        users = []
        for user in admin_auth.list_users().iterate_all():
            users.append({
                "uid": user.uid,
                "email": user.email,
                "disabled": user.disabled
            })
        
        return render_template('admin_users.html', users=users)
    except Exception as e:
        print(f"Error listing users: {e}")
        flash("Error fetching users. Please try again.", "danger")
        return redirect(url_for('admin_dashboard'))
    


@app.route('/admin/block-user/<uid>', methods=['POST'])
def block_user(uid):
    if not current_user.is_authenticated or not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Block the user by disabling their account
        admin_auth.update_user(uid, disabled=True)
        flash("User blocked successfully.", "success")
    except Exception as e:
        print(f"Error blocking user: {e}")
        flash("Error blocking the user. Please try again.", "danger")

    return redirect(url_for('list_users'))


@app.route('/admin/unblock-user/<uid>', methods=['POST'])
def unblock_user(uid):
    if not current_user.is_authenticated or not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Unblock the user by enabling their account
        admin_auth.update_user(uid, disabled=False)
        flash("User unblocked successfully.", "success")
    except Exception as e:
        print(f"Error unblocking user: {e}")
        flash("Error unblocking the user. Please try again.", "danger")

    return redirect(url_for('list_users'))



@app.route('/promote-to-admin', methods=['GET', 'POST'])
def promote_to_admin():
    form = EmailForm()
    if request.method == "GET":
        # Render the form
        if not current_user.is_authenticated:
            flash("You need to be logged in to request admin access.", "danger")
            return redirect(url_for('login'))

        # Fetch users for display in the template
        users = User.query.all()  # Assuming you're using SQLAlchemy

        return render_template("promote_to_admin.html", form=form, users=users)  # Pass users to template

    # Handle POST request (Promotion logic)
    if not current_user.is_authenticated:
        flash("You need to be logged in to request admin access.", "danger")
        return redirect(url_for('login'))

    if current_user.role == "admin":
        flash("You are already an admin.", "info")
        return redirect(url_for('admin_dashboard'))  # Prevent loop

    if current_user.admin_request:
        flash("You have already requested admin access. Please wait for approval.", "info")
        return redirect(url_for('home'))

    # Mark the user as having requested admin access
    current_user.admin_request = True
    db.session.commit()
    flash("Your request to become an admin has been submitted. An admin will review your request.", "success")
    return redirect(url_for('home'))




@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if not current_user.is_authenticated or current_user.role != "admin":
        flash("Access denied. Only admins can create other admins.", "danger")
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form.get("email")

        # Find the user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('create_admin'))

        # Promote the user to admin
        user.role = "admin"
        db.session.commit()
        flash(f"User {email} has been promoted to admin.", "success")
        return redirect(url_for('home'))

    return render_template('create_admin.html')


@app.route('/admin/users', methods=['GET'])
def admin_list_users():
    if not current_user.is_authenticated or not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Use Firebase Admin SDK to list all users
        users = []
        for user in admin_auth.list_users().iterate_all():
            users.append({
                "uid": user.uid,
                "email": user.email,
                "disabled": user.disabled
            })
        
        return render_template('admin_users.html', users=users)
    except Exception as e:
        print(f"Error listing users: {e}")
        flash("Error fetching users. Please try again.", "danger")
        return redirect(url_for('admin_dashboard'))


def set_admin_role(uid):
    try:
        admin_auth.set_custom_user_claims(uid, {"role": "admin"})
        print(f"Admin role assigned to user {uid}.")
    except Exception as e:
        print(f"Error setting admin role: {e}")

    
# Route to request admin privileges
@app.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))
    
    return render_template('admin_dashboard.html')



@app.route('/admin/services', methods=['GET'])
def admin_services():
    if not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Fetch all service requests from Firebase
        services_ref = database.child("requests").get()

        services = []
        if services_ref.each():
            for service in services_ref.each():
                services.append({"id": service.key(), **service.val()})

        return render_template('admin_services.html', services=services)
    except Exception as e:
        print(f"Error fetching services: {e}")
        flash("Error fetching services. Please try again later.", "danger")
        return redirect(url_for('home'))





@app.route('/admin/delete-service/<service_id>', methods=['POST'])
def admin_delete_service(service_id):
    if not is_admin():
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    try:
        # Fetch the service request by ID
        requests_ref = database.child("requests").order_by_key().equal_to(service_id).get()

        if not requests_ref.each():
            flash("Service not found.", "danger")
            return redirect(url_for("admin_services"))

        for request_item in requests_ref.each():
            database.child("requests").child(request_item.key()).remove()

        flash("Service deleted successfully.", "success")
    except Exception as e:
        print(f"Error deleting service: {e}")
        flash("Error deleting the service. Please try again.", "danger")

    return redirect(url_for('admin_services'))





#################################################################
# signUp, Log-in/Log-out and profile routes

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Create a new user using Pyrebase
            user = auth.create_user_with_email_and_password(email, password)
            token = user['idToken']  # Firebase ID token

            # Decode the token to get the user UID
            decoded_token = admin_auth.verify_id_token(token)
            uid = decoded_token['uid']

            # Check if the user already exists in your database
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                # Create a new user in the database
                new_user = User(id=uid, name=email.split('@')[0], email=email, password="")
                db.session.add(new_user)
                db.session.commit()

            # Log the user in using Flask-Login
            login_user(new_user)
            flash("Signup successful! You are now logged in.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            error_message = str(e)
            flash(f"Error during signup: {error_message}", "danger")


    return render_template('signup.html', form=form)
  

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        try:
            # Authenticate the user using Firebase Auth
            user = auth.sign_in_with_email_and_password(email, password)
            token = user['idToken']  # Retrieve Firebase ID token
            print(f"Token: {token}")

            decoded_token = admin_auth.verify_id_token(token)
            uid = decoded_token['uid']

            # Check if the user exists in the database
            local_user = User.query.filter_by(email=email).first()
            if not local_user:
                # If the user doesn't exist, create a new one
                local_user = User(id=uid, name=email.split('@')[0], email=email, password="")
                db.session.add(local_user)
                db.session.commit()

            # Store the token and role in the session
            session['token'] = token
            session['role'] = decoded_token.get("role", "user")
            login_user(local_user)

            # Redirect based on role
            if session['role'] == "admin":
                flash("Welcome, Admin!", "success")
                return redirect(url_for('admin_dashboard'))

            flash("Login successful!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            error_message = str(e)
            flash(f"Login failed: {error_message}", "danger")
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


# Route for user logout
@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

# Route for user profile update
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Add profile update logic
        current_user.name = form.name.data
        if form.password.data:
                current_user.set_password(form.password.data)
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('home'))
    return render_template('profile.html', form=form)


###################################################################
# seed admin account
with app.app_context():
    admin_email = "Imran.nabizada@icloud.com"
    try:
        # Use Firebase Admin SDK to get or create the admin user
        try:
            admin_user = admin_auth.get_user_by_email(admin_email)
        except admin_auth.UserNotFoundError:
            admin_user = admin_auth.create_user(
                email=admin_email,
                password="Internet@11",
                display_name="Admin User"
            )
            print(f"Admin user created with email {admin_email}.")

        # Set the admin role using custom claims
        set_admin_role(admin_user.uid)

        # Add the admin user to the local database if not already present
        local_admin = User.query.filter_by(email=admin_email).first()
        if not local_admin:
            local_admin = User(
                id=admin_user.uid,
                name="Admin User",
                email=admin_email,
                password=generate_password_hash("Internet@11", method='pbkdf2:sha256')
            )
            db.session.add(local_admin)
            db.session.commit()
            print(f"Admin user added to local database with email {admin_email}.")
    except Exception as e:
        print(f"Error initializing admin user: {e}")







if __name__ =='__main__':
    app.run(debug=True)

