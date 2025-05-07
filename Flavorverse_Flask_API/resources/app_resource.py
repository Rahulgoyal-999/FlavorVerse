from flask_restful import Resource, reqparse
from flask import jsonify, request
import bcrypt
import jwt
import datetime
import sqlite3
from functools import wraps

# Setup database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create users table if not exists
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Create tables on module import
create_tables()

# JWT Secret Key
SECRET_KEY = 'your-secret-key'  # Change this to a secure secret key in production

# Parser for registration
registration_parser = reqparse.RequestParser()
registration_parser.add_argument('username', type=str, required=True, help='Username is required')
registration_parser.add_argument('email', type=str, required=True, help='Email is required')
registration_parser.add_argument('password', type=str, required=True, help='Password is required')

# Parser for login
login_parser = reqparse.RequestParser()
login_parser.add_argument('email', type=str, required=True, help='Email is required')
login_parser.add_argument('password', type=str, required=True, help='Password is required')

class UserRegistration(Resource):
    def post(self):
        data = registration_parser.parse_args()
        
        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        if cursor.fetchone():
            conn.close()
            return {'message': 'User with this email already exists'}, 400
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
        if cursor.fetchone():
            conn.close()
            return {'message': 'User with this username already exists'}, 400
        
        # Hash the password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Insert new user
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (data['username'], data['email'], hashed_password.decode('utf-8'))
            )
            conn.commit()
            conn.close()
            
            return {
                'message': 'User registered successfully',
                'user': {
                    'username': data['username'],
                    'email': data['email']
                }
            }, 201
            
        except Exception as e:
            conn.close()
            return {'message': f'Error: {str(e)}'}, 500

class UserLogin(Resource):
    def post(self):
        data = login_parser.parse_args()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
            # Generate token
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, SECRET_KEY, algorithm='HS256')
            
            conn.close()
            return {
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            }, 200
        
        conn.close()
        return {'message': 'Invalid credentials'}, 401

# Token verification decorator (for protected routes)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return {'message': 'Token is missing'}, 401
        
        try:
            token = token.split(" ")[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data
        except:
            return {'message': 'Token is invalid'}, 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated 