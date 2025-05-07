from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import NewsletterSubscriber, APIKey
import requests

import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import APIKey
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from datetime import datetime

# Define decorators before they're used
def is_logged_in(request):
    """Helper function to check if a user is logged in through any method"""
    # Check standard Django authentication first
    if request.user and request.user.is_authenticated:
        print(f"DEBUG - is_logged_in: User is Django-authenticated as {request.user.username}")
        return True
        
    # Check our custom Flask session authentication
    if request.session.get('is_flask_authenticated', False):
        print(f"DEBUG - is_logged_in: User is Flask-authenticated as {request.session.get('user_email')}")
        return True
        
    print("DEBUG - is_logged_in: User is not authenticated")
    return False

def check_flask_auth(view_func):
    """Decorator to check Flask or Django authentication"""
    def wrapper(request, *args, **kwargs):
        # First, check if already Django authenticated
        if request.user and request.user.is_authenticated:
            print(f"DEBUG - check_flask_auth: Django auth found for {request.user.username}")
            
            # Ensure Flask session data is also set for compatibility
            if not request.session.get('is_flask_authenticated', False):
                request.session['is_flask_authenticated'] = True
                request.session['user_email'] = request.user.email
                request.session['user_data'] = {
                    'id': request.user.id,
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'role': 'user'  # Default role
                }
                request.session['flask_token'] = f"django_token_{request.user.id}_{int(datetime.now().timestamp())}"
                request.session.modified = True
                print("DEBUG - check_flask_auth: Added Flask session data for Django user")
            
            return view_func(request, *args, **kwargs)
        
        # Check Flask authentication
        if request.session.get('is_flask_authenticated', False):
            print("DEBUG - check_flask_auth: Flask session authentication found")
            
            # Special case for test tokens that bypass API verification
            flask_token = request.session.get('flask_token')
            if flask_token and (
                flask_token.startswith('test_') or 
                flask_token.startswith('mock_') or 
                flask_token.startswith('django_')
            ):
                print(f"DEBUG - check_flask_auth: Using {flask_token[:10]}... token, bypassing verification")
                return view_func(request, *args, **kwargs)
            
            # Normal verification path can be attempted here...
            # For simplicity, we'll just trust the session during development
            return view_func(request, *args, **kwargs)
        
        # No valid authentication
        print("DEBUG - check_flask_auth: Authentication check failed, redirecting to login")
        messages.error(request, 'Please login to continue')
        return redirect('loginpage')
    return wrapper

def check_auth(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.error(request, 'Please login to continue')
            return redirect('loginpage')
        try:
            # Verify with Flask that session is still valid
            response = requests.get(
                'http://127.0.0.1:5000/verify_session',
                headers={'Authorization': f"Bearer {request.session.get('user_email')}"},
                timeout=5
            )
            if response.status_code != 200:
                request.session.flush()
                messages.error(request, 'Session expired, please login again')
                return redirect('loginpage')
        except requests.RequestException:
            messages.error(request, 'Authentication service unavailable')
            return redirect('loginpage')
        return view_func(request, *args, **kwargs)
    return wrapper


def landingpage_view(request):
    return render(request, 'index.html')


@check_flask_auth
def homepage_view(request):
    print("DEBUG - homepage_view: Function entered")
    from RecipesApp.models import Recipe
    
    # Get the latest approved user-added recipes (limit to 5)
    user_recipes = Recipe.objects.filter(status='approved').order_by('-created_at')[:5]
    
    context = {
        'user_recipes': user_recipes
    }
    print("DEBUG - homepage_view: Rendering template")
    return render(request, "home.html", context)


@api_view(['GET'])
def about_api(request):
    """API endpoint for about us data"""
    response_data = {
        "data": {
            "description": "Welcome to FlavorVerse, your ultimate destination for culinary inspiration and recipe sharing. We're a community-driven platform where food enthusiasts from around the world come together to share their passion for cooking.",
            "mission": "To create a vibrant community where food lovers can discover, share, and celebrate the joy of cooking. We believe that great food brings people together and that everyone has something unique to contribute to the culinary world.",
            "stats": {
                "countries": "400+",
                "recipes": "10K+",
                "support": "24/7",
                "users": "50K+"
            },
            "title": "About FlavorVerse"
        },
        "success": True
    }
    return Response(response_data)

def aboutus_view(request):
    about_data = {
        "data": {
            "description": "Welcome to FlavorVerse, your ultimate destination for culinary inspiration and recipe sharing. We're a community-driven platform where food enthusiasts from around the world come together to share their passion for cooking.",
            "mission": "To create a vibrant community where food lovers can discover, share, and celebrate the joy of cooking. We believe that great food brings people together and that everyone has something unique to contribute to the culinary world.",
            "stats": {
                "countries": "400+",
                "recipes": "10K+",
                "support": "24/7",
                "users": "50K+"
            },
            "title": "About FlavorVerse"
        },
        "success": True
    }
    
    # Direct request for JSON via URL parameter
    if request.GET.get('response_type') == 'json':
        return JsonResponse(about_data)
    
    # Check both our enhanced detection and the middleware flag
    is_api_request = any([
        getattr(request, 'is_api_request', False),
        'application/json' in request.headers.get('Accept', ''),
        'postman' in request.headers.get('User-Agent', '').lower(),
        request.GET.get('format') == 'json',
        request.headers.get('X-Requested-With') == 'XMLHttpRequest',
    ])
    
    # Force API response for any request from Postman with query parameter 
    if 'postman' in request.headers.get('User-Agent', '').lower() or request.GET.get('api') == 'true':
        return JsonResponse(about_data)
    
    if is_api_request:
        return JsonResponse(about_data)
    
    # Otherwise return the HTML template
    return render(request, "AboutUs.html", {'about_data': about_data['data']})


def meetmyteam_view(request):
    return render(request,"MeetMyTeam.html")


@api_view(['GET'])
def contact_api(request):
    """API endpoint for contact data"""
    contact_data = {
        'email': 'flavorverse038@gmail.com',
        'phone': '+1 (555) 123-4567',
        'address': '123 Food Street, Culinary City, FC 12345',
        'social_media': {
            'facebook': 'https://facebook.com/flavorverse',
            'instagram': 'https://instagram.com/flavorverse',
            'twitter': 'https://twitter.com/flavorverse'
        }
    }
    
    try:
        # Try to fetch contact data from Flask API (optional)
        response = requests.get('http://127.0.0.1:5000/api/contact', timeout=5)
        if response.status_code == 200:
            contact_data = response.json()
    except requests.RequestException:
        # Silently use default data if API is unavailable
        pass
        
    return Response({
        'success': True,
        'data': contact_data
    })


def contactus_view(request):
    # Define the contact data to be used either in JSON or template response
    contact_data = {
        'email': 'flavorverse038@gmail.com',
        'phone': '+1 (555) 123-4567',
        'address': '123 Food Street, Culinary City, FC 12345',
        'social_media': {
            'facebook': 'https://facebook.com/flavorverse',
            'instagram': 'https://instagram.com/flavorverse',
            'twitter': 'https://twitter.com/flavorverse'
        }
    }
    
    try:
        # Try to fetch contact data from Flask API
        response = requests.get('http://127.0.0.1:5000/api/contact', timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        contact_data = response.json()
    except requests.RequestException as e:
        error_message = f"Failed to connect to the server: {str(e)}"
        print(f"Error fetching contact data: {error_message}")
        # We'll continue with the default contact_data defined above
    
    # Direct request for JSON via URL parameter
    if request.GET.get('response_type') == 'json':
        return JsonResponse({
            'success': True,
            'data': contact_data
        })
    
    # Check both our enhanced detection and the middleware flag
    is_api_request = any([
        getattr(request, 'is_api_request', False),
        'application/json' in request.headers.get('Accept', ''),
        'postman' in request.headers.get('User-Agent', '').lower(),
        request.GET.get('format') == 'json',
        request.headers.get('X-Requested-With') == 'XMLHttpRequest',
    ])
    
    # Force API response for any request from Postman with query parameter
    if 'postman' in request.headers.get('User-Agent', '').lower() or request.GET.get('api') == 'true':
        return JsonResponse({
            'success': True,
            'data': contact_data
        })
    
    if is_api_request:
        return JsonResponse({
            'success': True,
            'data': contact_data
        })
        
    # Otherwise return the HTML template
    return render(request, 'contactUs.html', {'contact_data': contact_data})


@csrf_exempt
def send_message(request):
    """Process contact form submission through Flask API"""
    if request.method == 'POST':
        try:
            # Prepare data for Flask API
            data = {
                'name': request.POST.get('name', ''),
                'email': request.POST.get('email', ''),
                'subject': request.POST.get('subject', 'FlavorVerse Feedback'),
                'message': request.POST.get('message', '')
            }

            # Send request to Flask API
            response = requests.post(
                'http://127.0.0.1:5000/api/contact/send',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            response_data = response.json()
            return JsonResponse(response_data, status=response.status_code)
            
        except requests.RequestException as e:
            print(f"Error sending message: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to send message. Please try again later.'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=400)




# ... (Keep all existing code before subscribe_newsletter function) ...

@csrf_exempt
def subscribe_newsletter(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                email = data.get('email', '')
            else:
                email = request.POST.get('email', '')
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide an email address.'
                }, status=400)

            # Basic email validation
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide a valid email address.'
                }, status=400)

            # Check if already subscribed
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This email is already subscribed to our newsletter.'
                }, status=400)
            
            # Try to connect to Flask API for email service
            try:
                # Attempt to connect to Flask API
                response = requests.post(
                    'http://127.0.0.1:5000/subscribe-newsletter',
                    json={'email': email},
                    timeout=5
                )
                response.raise_for_status()
                
                # If Flask API call succeeds, save subscriber
                subscriber = NewsletterSubscriber.objects.create(email=email)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Successfully subscribed to our newsletter! Please check your email for confirmation.'
                })
                
            except requests.RequestException as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Newsletter service is currently unavailable. Please try again later.'
                }, status=503)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data.'
            }, status=400)
        except Exception as e:
            print(f"Error processing subscription: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to subscribe. Please try again later.'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=400)

# ... (Keep all existing code after subscribe_newsletter function) ...

# You can continue adding more views or logic below!


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_api_key(request):
    name = request.data.get('name', f"API Key {request.user.api_keys.count() + 1}")
    api_key = APIKey.objects.create(user=request.user, name=name)
    return Response({
        'key': api_key.key,
        'name': api_key.name
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_api_keys(request):
    keys = request.user.api_keys.all().values('id', 'name', 'created', 'is_active')
    return Response(list(keys))




def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def login_view(request):
    print(f"DEBUG - login_view: Method = {request.method}")
    if request.method == 'POST':
        try:
            # Create a debug file to confirm we're reaching this point
            with open('login_debug.txt', 'a') as f:
                f.write(f"Login attempt at {datetime.now()}\n")
                
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            print(f"DEBUG - login_view: Login attempt with email = {email}, role = {role}")
            
            with open('login_debug.txt', 'a') as f:
                f.write(f"Email: {email}, Role: {role}\n")
            
            if not all([email, password, role]):
                messages.error(request, 'Please fill in all fields')
                return render(request, 'login.html')
            
            # Try to connect to a simple Flask endpoint first
            try:
                # Try to connect to the Flask API's root endpoint
                root_response = requests.get('http://127.0.0.1:5000/', timeout=3)
                with open('login_debug.txt', 'a') as f:
                    f.write(f"Flask API root response: {root_response.status_code}\n")
            except requests.RequestException as e:
                with open('login_debug.txt', 'a') as f:
                    f.write(f"Flask API connection error: {str(e)}\n")
                messages.error(request, f"Cannot connect to authentication service: {str(e)}. Please try again later.")
                return render(request, 'login.html')
            
            # Fixed test credentials for debugging - TEMPORARY
            # This creates a bypass if the Flask API is down
            if email == "admin@example.com" and password == "password123" and role == "admin":
                with open('login_debug.txt', 'a') as f:
                    f.write("Using test credentials bypass\n")
                
                # Set debug session data
                request.session['is_flask_authenticated'] = True
                request.session['user_email'] = email
                request.session['user_data'] = {
                    'id': 1,
                    'name': 'Test Admin',
                    'email': email,
                    'role': role
                }
                request.session['flask_token'] = "test_debug_token_for_development_only"
                request.session.modified = True
                
                messages.success(request, 'Login successful (DEBUG MODE)!')
                return redirect('homepage')
            
            # Normal Flask API authentication
            try:
                api_url = 'http://127.0.0.1:5000/api/login'
                api_data = {
                    'email': email,
                    'password': password,
                    'role': role
                }
                
                print(f"DEBUG - login_view: Sending request to Flask API: {api_url}")
                print(f"DEBUG - login_view: Request data: {api_data}")
                
                with open('login_debug.txt', 'a') as f:
                    f.write(f"Sending request to {api_url}\n")
                
                success = False
                
                # First try regular login
                try:
                    response = requests.post(
                        api_url,
                        json=api_data,
                        timeout=5
                    )
                    
                    with open('login_debug.txt', 'a') as f:
                        f.write(f"API response status: {response.status_code}\n")
                        f.write(f"API response: {response.text[:200]}...\n")
                    
                    success = True
                except requests.RequestException as e:
                    with open('login_debug.txt', 'a') as f:
                        f.write(f"Main API login failed: {str(e)}, trying test endpoint\n")
                    success = False
                
                # If regular login fails, try test endpoint
                if not success and '@example.com' in email:
                    try:
                        with open('login_debug.txt', 'a') as f:
                            f.write(f"Trying test login endpoint\n")
                        
                        test_response = requests.post(
                            'http://127.0.0.1:5000/api/test-login',
                            json=api_data,
                            timeout=5
                        )
                        
                        with open('login_debug.txt', 'a') as f:
                            f.write(f"Test API response status: {test_response.status_code}\n")
                            f.write(f"Test API response: {test_response.text[:200]}...\n")
                        
                        response = test_response
                        success = True
                    except requests.RequestException as e:
                        with open('login_debug.txt', 'a') as f:
                            f.write(f"Test API login also failed: {str(e)}\n")
                
                if success:
                    print(f"DEBUG - login_view: API response status: {response.status_code}")
                    print(f"DEBUG - login_view: API response: {response.text[:200]}...")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data.get('success'):
                                # Authentication successful
                                print("DEBUG - login_view: Authentication successful")
                                
                                # Set session data
                                request.session['is_flask_authenticated'] = True
                                request.session['user_email'] = email
                                request.session['user_data'] = data.get('user', {})
                                request.session['flask_token'] = data.get('token')
                                request.session.modified = True
                                
                                with open('login_debug.txt', 'a') as f:
                                    f.write(f"Authentication successful, token: {data.get('token')[:10]}...\n")
                                    
                                messages.success(request, 'Login successful!')
                                return redirect('homepage')
                            else:
                                error_msg = data.get('message', 'Invalid credentials')
                                print(f"DEBUG - login_view: API returned error: {error_msg}")
                                messages.error(request, error_msg)
                        except json.JSONDecodeError:
                            with open('login_debug.txt', 'a') as f:
                                f.write(f"JSON decode error on API response\n")
                            messages.error(request, 'Authentication service returned invalid data')
                    else:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('message', 'Authentication failed. Please try again.')
                        except:
                            error_msg = f'Authentication failed with status code {response.status_code}. Please try again.'
                        
                        messages.error(request, error_msg)
                    
            except requests.RequestException as e:
                with open('login_debug.txt', 'a') as f:
                    f.write(f"API request exception: {str(e)}\n")
                print(f"DEBUG - login_view: Request exception: {str(e)}")
                messages.error(request, f'Authentication service unavailable: {str(e)}')
                
        except Exception as e:
            with open('login_debug.txt', 'a') as f:
                f.write(f"Unexpected exception: {str(e)}\n")
            print(f"DEBUG - login_view: Unexpected exception: {str(e)}")
            messages.error(request, f'Authentication error: {str(e)}')
        
        # If we get here, authentication was attempted but failed
        return render(request, 'login.html')
    
    return render(request, 'login.html')

@check_flask_auth
def profile_view(request):
    user_data = request.session.get('user_data', {})
    return render(request, 'profile.html', {'user_data': user_data})

def logout_view(request):
    print("DEBUG - logout_view: Starting logout process")
    
    # Handle Django logout
    if request.user and request.user.is_authenticated:
        print(f"DEBUG - logout_view: Logging out Django user {request.user.username}")
        logout(request)
    
    # Handle Flask logout
    user_email = request.session.get('user_email')
    flask_token = request.session.get('flask_token')
    
    # Try to notify Flask API about logout (optional)
    if user_email and flask_token and not flask_token.startswith('django_'):
        try:
            print(f"DEBUG - logout_view: Notifying Flask API about logout for {user_email}")
            logout_response = requests.post(
                'http://127.0.0.1:5000/api/logout',
                json={'email': user_email},
                headers={'Authorization': f'Bearer {flask_token}'},
                timeout=5
            )
            print(f"DEBUG - logout_view: Flask API response: {logout_response.status_code}")
        except requests.RequestException as e:
            print(f"DEBUG - logout_view: Failed to notify Flask API: {str(e)}")
    
    # Clear all session data
    print("DEBUG - logout_view: Clearing session data")
    request.session['is_flask_authenticated'] = False
    request.session['user_email'] = None
    request.session['user_data'] = None
    request.session['flask_token'] = None
    
    # Flush the session to clear all data
    request.session.flush()
    
    messages.success(request, 'Logged out successfully!')
    print("DEBUG - logout_view: Redirecting to login page")
    return redirect('loginpage')

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({"message": "You are authenticated!"})

def direct_login_view(request):
    """Direct Django-based login that doesn't rely on Flask API (temporary solution)"""
    print(f"DEBUG - direct_login_view: Method = {request.method}")
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'user')
        
        print(f"DEBUG - direct_login_view: Login attempt with email = {email}, role = {role}")
        
        if not all([email, password]):
            messages.error(request, 'Please provide both email and password')
            return render(request, 'login.html')
        
        # For testing purposes - accept any credentials ending with @example.com
        # In production, this would validate against your actual user database
        if email and '@example.com' in email and password and len(password) >= 6:
            # Create mock user data for the session
            user_data = {
                'id': 999,
                'name': email.split('@')[0].title(),
                'email': email,
                'role': role
            }
            
            # Set up session
            request.session['is_flask_authenticated'] = True
            request.session['user_email'] = email
            request.session['user_data'] = user_data
            request.session['flask_token'] = f"mock_token_{email.split('@')[0]}_{int(datetime.now().timestamp())}"
            request.session.modified = True
            
            print(f"DEBUG - direct_login_view: Created mock session for {email}")
            print(f"DEBUG - direct_login_view: Session data = {request.session.items()}")
            
            messages.success(request, 'Login successful!')
            return redirect('homepage')
        else:
            print(f"DEBUG - direct_login_view: Invalid credentials for {email}")
            messages.error(request, 'Invalid email or password. Try using an @example.com email with a password of at least 6 characters.')
    
    # Get request - show the login form
    return render(request, 'login.html')

def django_login_view(request):
    """Simple login view that uses Django's authentication directly"""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        print(f"DEBUG - django_login_view: Login attempt with email={email}")
        
        # Try to authenticate with Django
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            print(f"DEBUG - django_login_view: Authentication successful for {email}")
            
            # Use Django's built-in login function
            login(request, user)
            
            # Set extra session data for API compatibility
            request.session['is_flask_authenticated'] = True
            request.session['user_email'] = email
            request.session['user_data'] = {
                'id': user.id,
                'name': user.get_full_name() or user.username or email.split('@')[0].title(),
                'email': email,
                'role': request.POST.get('role', 'user')
            }
            request.session['flask_token'] = f"django_token_{user.id}_{int(datetime.now().timestamp())}"
            request.session.modified = True
            
            messages.success(request, 'Login successful!')
            return redirect('homepage')
        else:
            print(f"DEBUG - django_login_view: Authentication failed for {email}")
            
            # Special case for @example.com emails during development
            if email and '@example.com' in email and len(password) >= 6:
                messages.warning(request, 'Using development bypass login. This would normally fail.')
                
                # Create session data for testing
                request.session['is_flask_authenticated'] = True
                request.session['user_email'] = email
                request.session['user_data'] = {
                    'id': 999,
                    'name': email.split('@')[0].title(),
                    'email': email,
                    'role': request.POST.get('role', 'user')
                }
                request.session['flask_token'] = f"test_token_{int(datetime.now().timestamp())}"
                request.session.modified = True
                
                return redirect('homepage')
            
            messages.error(request, "Invalid email or password.")
    
    return render(request, "login.html")

def debug_info_view(request):
    """View to show debug information about authentication status"""
    
    # Get authentication info
    flask_auth = request.session.get('is_flask_authenticated', False)
    django_auth = request.user.is_authenticated if request.user else False
    
    # Get user info
    flask_user = {
        'email': request.session.get('user_email'),
        'token': request.session.get('flask_token', '')[:10] + '...' if request.session.get('flask_token') else None,
        'data': request.session.get('user_data', {}),
    }
    
    django_user = {
        'username': request.user.username if django_auth else None,
        'email': request.user.email if django_auth else None,
        'id': request.user.id if django_auth else None,
        'is_staff': request.user.is_staff if django_auth else None,
    }
    
    # Get session info
    session_keys = list(request.session.keys())
    
    # Get headers info
    headers_info = {key: request.headers.get(key) for key in request.headers.keys()}
    
    # API detection results
    api_detection = {
        'middleware_flag': getattr(request, 'is_api_request', False),
        'accept_header': request.headers.get('Accept', ''),
        'user_agent': request.headers.get('User-Agent', ''),
        'format_param': request.GET.get('format'),
        'path_starts_with_api': request.path.startswith('/api/'),
        'is_postman': 'postman' in request.headers.get('User-Agent', '').lower(),
    }
    
    # Create context
    context = {
        'flask_authenticated': flask_auth,
        'django_authenticated': django_auth,
        'flask_user': flask_user,
        'django_user': django_user,
        'session_keys': session_keys,
        'session_data': {k: request.session.get(k) for k in session_keys if k not in ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']},
        'headers': headers_info,
        'api_detection': api_detection,
    }
    
    # Return as JSON for easy debugging
    return JsonResponse(context, json_dumps_params={'indent': 2})

def contact_admin_redirect(request):
    """Redirect to the Flask admin panel for contact messages"""
    from django.shortcuts import redirect
    return redirect('http://127.0.0.1:5000/admin/contact')

@login_required
def contact_messages_view(request):
    """View to display contact messages from Flask API"""
    try:
        # Force a sync if requested
        if 'sync' in request.GET:
            from FlavorverseApp.models import ContactMessage
            success = ContactMessage.sync_from_flask()
            if success:
                messages.success(request, "Successfully synced contact messages from Flask API.")
            else:
                messages.error(request, "Failed to sync contact messages from Flask API.")
        
        # Get all messages from Django database
        from FlavorverseApp.models import ContactMessage
        contact_messages = ContactMessage.objects.all().order_by('-created_at')
        
        # Return the template with messages
        return render(request, 'contact_messages.html', {
            'messages': contact_messages
        })
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('homepage')