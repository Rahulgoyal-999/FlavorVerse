from flask import Flask, render_template, redirect, request, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_restful import Resource, Api
from flask_jwt_extended import get_jwt_identity
from flask import jsonify

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app, resources={
    r"/*": {  # Allow CORS for all routes
        "origins": ["http://127.0.0.1:8000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
    }
})

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.urandom(24).hex()
app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for now to get the form working

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'flavorverse038@gmail.com'
app.config['MAIL_PASSWORD'] = 'csuo rfrb majh pqdi'  # Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'flavorverse038@gmail.com'

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
jwt = JWTManager(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)
csrf = CSRFProtect(app)

migrate = Migrate(app, db)

# Load environment variables
load_dotenv()

# About Us data
about_data = {
    "title": "About FlavorVerse",
    "description": "Welcome to FlavorVerse, your ultimate destination for culinary inspiration and recipe sharing. We're a community-driven platform where food enthusiasts from around the world come together to share their passion for cooking.",
    "mission": "To create a vibrant community where food lovers can discover, share, and celebrate the joy of cooking. We believe that great food brings people together and that everyone has something unique to contribute to the culinary world.",
    "stats": {
        "recipes": "10K+",
        "users": "50K+",
        "countries": "100+",
        "support": "24/7"
    }
}

# Contact information
contact_data = {
    "email": "flavorverse038@gmail.com",
    "phone": "+1 (555) 123-4567",
    "address": "123 Food Street, Culinary City, FC 12345",
    "social_media": {
        "facebook": "https://facebook.com/flavorverse",
        "instagram": "https://instagram.com/flavorverse",
        "twitter": "https://twitter.com/flavorverse"
    }
}

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    birthdate = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class ContactMessage(db.Model):
    __tablename__ = 'contact_message'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, name, email, message, subject=None):
        self.name = name
        self.email = email
        self.message = message
        self.subject = subject or 'FlavorVerse Contact Form'

class Recipe(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('recipes', lazy=True))

    def __init__(self, title, ingredients, instructions, image_url, category, user_id):
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.image_url = image_url
        self.category = category
        self.user_id = user_id

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscriber'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, email):
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()  # This will ensure all tables including ContactMessage are created

@app.route("/more_info", methods=['GET'])
def more_info():
    return render_template('more_info.html', user=current_user)

@app.route("/save_more_info", methods=['POST'])
def save_more_info():
    if request.method == "POST":
        mobile = request.form.get("mobile")
        address = request.form.get("address")
        gender = request.form.get("gender")
        birthdate = request.form.get("birthdate")

        current_user.mobile = mobile
        current_user.address = address
        current_user.gender = gender
        current_user.birthdate = birthdate

        db.session.commit()
        flash("More information updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)

@app.route('/')
def landing():
    return redirect(url_for('home'))

@app.route("/home")
def home():
    return render_template("index.html")

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Only update fields that were filled out
        if name and name != current_user.name:
            current_user.name = name

        if email and email != current_user.email:
            # Check if email already exists for another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already in use by another account.', 'error')
                return redirect(url_for('edit_profile'))
            current_user.email = email

        if password:
            current_user.set_password(password)

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            return redirect(url_for('edit_profile'))

    return render_template('edit_profile.html')

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    login_failed = False
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            login_failed = True

    return render_template("login.html", login_failed=login_failed)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if not server_running:
        return jsonify({'error': 'Server is not running', 'message': 'Cannot add recipe when server is not running'}), 503
    if request.method == 'POST':
        # Gather form data
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image_url = request.form.get('image_url', '')
        category = request.form['category']
        user_id = current_user.id

        # Save in Flask DB
        new_recipe = Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            image_url=image_url,
            category=category,
            user_id=user_id
        )
        db.session.add(new_recipe)
        db.session.commit()

        # Send to Django API
        django_api_url = "http://127.0.0.1:8000/api/recipes/"
        payload = {
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "image_url": image_url,
            "category": category,
            "user_id": user_id  # or whatever Django expects
        }
        try:
            response = requests.post(django_api_url, json=payload, timeout=5)
            if response.status_code == 201:
                flash('Recipe also added to Django!', 'success')
            else:
                flash('Recipe added in Flask, but not in Django: ' + response.text, 'warning')
        except Exception as e:
            flash('Recipe added in Flask, but Django API not reachable.', 'warning')

        return redirect(url_for('my_recipes'))
    return render_template('add_recipe.html')

@app.route('/recipe_added')
def recipe_added():
    title = request.args.get('title')
    image_url = request.args.get('image_url')
    return render_template('recipe_added.html', title=title, image_url=image_url)

@app.route('/recipes', methods=['GET', 'POST'])
def recipes_page():
    search_query = request.args.get('search')
    category_filter = request.args.get('category')
    
    # Start by querying all recipes from the database
    filtered_recipes = Recipe.query

    if search_query:
        filtered_recipes = filtered_recipes.filter(Recipe.title.ilike(f'%{search_query}%'))
    
    if category_filter:
        filtered_recipes = filtered_recipes.filter(Recipe.category.ilike(f'%{category_filter}%'))
    
    # Execute the query to get the filtered results
    filtered_recipes = filtered_recipes.all()

    no_results = len(filtered_recipes) == 0
    
    return render_template('recipes.html', recipes=filtered_recipes, no_results=no_results, category_filter=category_filter)

@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    recipe_to_delete = Recipe.query.get(recipe_id)
    if recipe_to_delete:
        db.session.delete(recipe_to_delete)
        db.session.commit()
    
    return redirect(url_for('recipes_page'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        current_user.name = name
        current_user.email = email
        
        if password:
            current_user.set_password(password)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))
    
    return render_template("profile.html", name=current_user.name, email=current_user.email)

@app.route("/aboutus")
def aboutus():
    return render_template("AboutUs.html")

@app.route("/contactus")
def contactus():
    return render_template("ContactUs.html")

# Initialize Flask-RESTful API
api = Api(app)

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        subject = data.get('subject', 'FlavorVerse Contact Form').strip()

        if not all([name, email, message]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            }), 400

        # Save to database
        new_message = ContactMessage(
            name=name,
            email=email,
            message=message,
            subject=subject
        )
        db.session.add(new_message)
        db.session.commit()

        # Create email message
        msg = Message(
            f'FlavorVerse Contact: {subject}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_USERNAME']],
            reply_to=email
        )
        
        msg.html = render_template(
            'contact_email.html',
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        msg.body = f"From: {name}\nEmail: {email}\nSubject: {subject}\n\nMessage:\n{message}"
        
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully!'
        })
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        db.session.rollback()  # Rollback the database session in case of error
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending your message. Please try again later.'
        }), 500

@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        email = data.get('email', '').strip()

        if not email:
            return jsonify({
                'success': False,
                'message': 'Please provide an email address.'
            }), 400

        # Check if email already exists
        existing_subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing_subscriber:
            if existing_subscriber.is_active:
                return jsonify({
                    'success': False,
                    'message': 'This email is already subscribed to our newsletter.'
                })
            else:
                # Reactivate subscription
                existing_subscriber.is_active = True
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Your subscription has been reactivated!'
                })
        
        # Create new subscriber
        subscriber = NewsletterSubscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()
        
        try:
            # Send welcome email
            msg = Message(
                'Welcome to FlavorVerse Newsletter!',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            
            msg.html = render_template('newsletter_welcome_email.html', email=email)
            msg.body = f"Welcome to FlavorVerse Newsletter!\n\nThank you for subscribing to our newsletter. You'll now receive regular updates about recipes, cooking tips, and community events."
            
            mail.send(msg)
        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")
            # Don't return error to user, subscription was still successful
        
        return jsonify({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter!'
        })
        
    except Exception as e:
        print(f"Error subscribing to newsletter: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your subscription.'
        }), 500

@app.route("/meetmyteam")
def meetmyteam():
    return render_template("MeetMyTeam.html")

@app.route("/allrecipes")
def allrecipes():
    return render_template("allrecipes.html")

@app.route("/veg")
def veg():
    return render_template("veg.html")

@app.route("/nonveg")
def nonveg():
    return render_template("nonveg.html")

@app.route("/soups")
def soups():
    return render_template("soups.html")

@app.route("/desserts")
def desserts():
    return render_template("desserts.html")

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

@app.route('/api/about', methods=['GET'])
def get_about_data():
    try:
        return jsonify({
            'success': True,
            'data': about_data
        })
    except Exception as e:
        print(f"Error fetching about data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching about data.'
        }), 500

@app.route('/api/contact', methods=['GET'])
def get_contact():
    try:
        return jsonify(contact_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact/send', methods=['POST'])
def send_contact_message():
    try:
        # Try to get JSON data first, fallback to form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject', 'FlavorVerse Feedback')
        message = data.get('message')

        if not all([name, email, message]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            }), 400

        # Save to database
        new_message = ContactMessage(
            name=name,
            email=email,
            message=message,
            subject=subject
        )
        db.session.add(new_message)
        db.session.commit()

        # Create and send email
        msg = Message(
            f'FlavorVerse Contact: {subject}',
            sender='flavorverse038@gmail.com',
            recipients=['flavorverse038@gmail.com'],
            reply_to=email
        )
        
        msg.html = render_template(
            'contact_email.html',
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        msg.body = f"From: {name}\nEmail: {email}\nSubject: {subject}\n\nMessage:\n{message}"
        
        mail.send(msg)

        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully!'
        }), 200

    except Exception as e:
        print(f"Error sending message: {str(e)}")  # Log the error
        db.session.rollback()  # Rollback in case of database error
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending your message. Please try again later.'
        }), 500

# Django API configuration
DJANGO_API_URL = "http://localhost:8000/api"  # Update this with your Django API URL

# Global variable to track server status
server_running = False  # Start with server not running

@app.before_request
def check_server_status():
    """Check if the server is running before processing any request"""
    # Allow health check endpoint without server running check
    if request.endpoint == 'api_health_check':
        return None
        
    # For all other endpoints, check if server is running
    if not server_running:
        return jsonify({
            'error': 'Server is not running',
            'message': 'The Flask server is currently not running. Please try again later.'
        }), 503

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """Health check endpoint for Django to verify Flask API is running"""
    global server_running
    server_running = True
    return jsonify({
        'status': 'ok',
        'message': 'Flask API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    """Endpoint to simulate server shutdown"""
    global server_running
    server_running = False
    return jsonify({
        'status': 'shutdown',
        'message': 'Flask API is now offline'
    }), 200

@app.route('/api/recipes', methods=['GET'])
def api_get_recipes():
       """API endpoint to get all recipes, or filter by user_id"""
       if not server_running:
           return jsonify({
               'error': 'Server is not running',
               'message': 'Cannot fetch recipes when server is not running'
           }), 503

       try:
           user_id = request.args.get('user_id')
           if user_id:
               recipes = Recipe.query.filter_by(user_id=user_id).all()
           else:
               recipes = Recipe.query.all()
           recipes_data = [{
               'id': recipe.id,
               'title': recipe.title,
               'ingredients': recipe.ingredients,
               'instructions': recipe.instructions,
               'image_url': recipe.image_url,
               'category': recipe.category,
               'user_id': recipe.user_id,
               # Add status if you use it in your Django template
               'status': getattr(recipe, 'status', 'pending')
           } for recipe in recipes]
           
           return jsonify({
               'success': True,
               'recipes': recipes_data
           }), 200
       except Exception as e:
           return jsonify({
               'success': False,
               'message': str(e)
           }), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def api_get_recipe(recipe_id):
    """API endpoint to get a single recipe"""
    if not server_running:
        return jsonify({
            'error': 'Server is not running',
            'message': 'Cannot fetch recipe when server is not running'
        }), 503

    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({
                'success': False,
                'message': 'Recipe not found'
            }), 404
            
        recipe_data = {
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'image_url': recipe.image_url,
            'category': recipe.category,
            'user_id': recipe.user_id
        }
        
        return jsonify({
            'success': True,
            'recipe': recipe_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/recipes', methods=['POST'])
def api_add_recipe():
    if not server_running:
        return jsonify({
            'error': 'Server is not running',
            'message': 'Cannot add recipe when server is not running'
        }), 503

    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'ingredients', 'instructions', 'category', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
                
        # Create a new recipe
        new_recipe = Recipe(
            title=data['title'],
            ingredients=data['ingredients'],
            instructions=data['instructions'],
            image_url=data.get('image_url', ''),
            category=data['category'],
            user_id=data['user_id']
        )
        
        db.session.add(new_recipe)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe added successfully',
            'recipe': {
                'id': new_recipe.id,
                'title': new_recipe.title,
                'ingredients': new_recipe.ingredients,
                'instructions': new_recipe.instructions,
                'image_url': new_recipe.image_url,
                'category': new_recipe.category,
                'user_id': new_recipe.user_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def api_update_recipe(recipe_id):
    """API endpoint to update a recipe"""
    if not server_running:
        return jsonify({
            'error': 'Server is not running',
            'message': 'Cannot update recipe when server is not running'
        }), 503

    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({
                'success': False,
                'message': 'Recipe not found'
            }), 404
            
        data = request.get_json()
        
        # Update recipe fields
        if 'title' in data:
            recipe.title = data['title']
        if 'ingredients' in data:
            recipe.ingredients = data['ingredients']
        if 'instructions' in data:
            recipe.instructions = data['instructions']
        if 'image_url' in data:
            recipe.image_url = data['image_url']
        if 'category' in data:
            recipe.category = data['category']
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe updated successfully',
            'recipe': {
                'id': recipe.id,
                'title': recipe.title,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions,
                'image_url': recipe.image_url,
                'category': recipe.category,
                'user_id': recipe.user_id
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def api_delete_recipe(recipe_id):
    """API endpoint to delete a recipe"""
    if not server_running:
        return jsonify({
            'error': 'Server is not running',
            'message': 'Cannot delete recipe when server is not running'
        }), 503

    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({
                'success': False,
                'message': 'Recipe not found'
            }), 404
            
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recipe deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/test-login', methods=['POST'])
def test_login():
    """Simple test endpoint for login that doesn't require database access"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        
        print(f"Test login attempt for email: {email}, role: {role}")
        
        # Accept any credentials with @example.com domain
        if email and '@example.com' in email and password and len(password) >= 6:
            # Generate dummy token
            test_token = "test_token_" + email.split('@')[0] + "_" + str(int(datetime.utcnow().timestamp()))
            
            return jsonify({
                'success': True,
                'message': 'Test login successful',
                'user': {
                    'id': 999,
                    'name': email.split('@')[0].title(),
                    'email': email,
                    'role': role
                },
                'token': test_token
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid test credentials. Use an @example.com email and password with at least 6 characters.'
            }), 401
            
    except Exception as e:
        print(f"Test login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Test login error: {str(e)}'
        }), 500

@app.route('/admin')
@login_required
def admin():
    # Check if user has admin privileges
    # For simplicity, we can assume the first user in the database is an admin
    if current_user.id != 1:
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('home'))
    
    return render_template('admin.html')

@app.route('/admin/contact-messages')
@login_required
def admin_contact_messages():
    # Check if user has admin privileges
    if current_user.id != 1:
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('home'))
    
    try:
        # Get all contact messages ordered by creation date (newest first)
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        
        # Debug: print message count and details
        print(f"DEBUG: Found {len(messages)} contact messages")
        for msg in messages:
            print(f"DEBUG: Message ID: {msg.id}, From: {msg.name}, Subject: {msg.subject}")
            
        return render_template('admin_messages.html', messages=messages)
    except Exception as e:
        # Log any errors
        print(f"ERROR in admin_contact_messages: {str(e)}")
        flash(f"Error loading messages: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/admin/contact')
@login_required
def admin_contact():
    # This is an alias for admin_contact_messages for easier access
    return admin_contact_messages()

@app.route('/contact/admin')
@login_required
def contact_admin_redirect():
    # Check if user has admin privileges
    if current_user.id != 1:
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('home'))
    
    # Redirect to the contact messages page
    return redirect(url_for('admin_contact_messages'))

@app.route('/test-contact-message')
@login_required
def test_contact_message():
    # Create a test contact message
    try:
        # Create a new test message
        test_message = ContactMessage(
            name="Test User",
            email="test@example.com",
            message="This is a test message to verify database functionality.",
            subject="Test Message"
        )
        
        # Save to database
        db.session.add(test_message)
        db.session.commit()
        
        # Debug info
        print(f"DEBUG: Created test message with ID: {test_message.id}")
        
        flash("Test message created successfully!", "success")
        return redirect(url_for('admin_contact_messages'))
    except Exception as e:
        # Log any errors
        print(f"ERROR in test_contact_message: {str(e)}")
        db.session.rollback()
        flash(f"Error creating test message: {str(e)}", "danger")
        return redirect(url_for('admin'))

@app.route('/api/contact/messages', methods=['GET'])
def api_get_contact_messages():
    """API endpoint to retrieve all contact messages"""
    try:
        # Get all contact messages ordered by creation date (newest first)
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        
        # Convert messages to JSON-serializable format
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'name': msg.name,
                'email': msg.email,
                'subject': msg.subject or 'No Subject',
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        # Return as JSON
        return jsonify({
            'success': True,
            'messages': messages_data
        }), 200
        
    except Exception as e:
        print(f"API get contact messages error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching contact messages: {str(e)}'
        }), 500

@app.route('/api/auth/verify', methods=['POST'])
def api_auth_verify():
    """API endpoint to verify user credentials from Django backend"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({
                'success': False, 
                'message': 'Both email and password are required'
            }), 400
            
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            return jsonify({
                'success': True,
                'message': 'Credentials verified',
                'user_id': user.id,
                'name': user.name,
                'email': user.email
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 200  # Still 200 to indicate API worked properly
            
    except Exception as e:
        print(f"API auth verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Authentication verification error: {str(e)}'
        }), 500

@app.route('/api/profile/update', methods=['PUT'])
def api_update_profile():
    """API endpoint to update user profile from Django frontend"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
            
        # Get user from database
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        # Update fields if provided
        if 'name' in data and data['name']:
            user.name = data['name']
            
        if 'email' in data and data['email']:
            # Check if email already exists for another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({
                    'success': False,
                    'message': 'Email already in use by another account'
                }), 400
            user.email = data['email']
            
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            
        if 'mobile' in data:
            user.mobile = data['mobile']
            
        if 'address' in data:
            user.address = data['address']
            
        if 'gender' in data:
            user.gender = data['gender']
            
        if 'birthdate' in data:
            user.birthdate = data['birthdate']
            
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'mobile': user.mobile,
                'address': user.address,
                'gender': user.gender,
                'birthdate': user.birthdate
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }), 500

@app.route('/my_recipes')
@login_required
def my_recipes():
    if not server_running:
        return jsonify({'error': 'Server is not running', 'message': 'Cannot fetch recipes when server is not running'}), 503
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    no_results = len(user_recipes) == 0
    return render_template('my_recipes.html', recipes=user_recipes, no_results=no_results)

if __name__ == "__main__":
    # Set server_running to True when the server starts
    server_running = True
    # Run the Flask app on all network interfaces
    app.run(host='127.0.0.1', port=5000, debug=True)
