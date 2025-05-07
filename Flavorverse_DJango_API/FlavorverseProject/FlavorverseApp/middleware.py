from django.contrib import messages
from .utils import is_flask_api_available, enforce_api_dependency
import logging
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

class APIDetectionMiddleware:
    """
    Middleware to detect API requests including Postman, adding a flag to the request
    so views can easily check if the request is from an API client.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Add is_api_request attribute to all requests
        request.is_api_request = any([
            'application/json' in request.headers.get('Accept', ''),
            'postman' in request.headers.get('User-Agent', '').lower(),
            request.GET.get('format') == 'json',
            request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            request.path.startswith('/api/'),
        ])
        
        response = self.get_response(request)
        return response

class FlaskAPICheckMiddleware:
    """
    Middleware to check if the Flask API is available.
    Blocks authentication attempts when Flask is down and shows a warning message.
    Also logs out users if the API remains unavailable for too long.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._api_checked = False
        self._api_available = False
        
    def __call__(self, request):
        # Only check once per request cycle
        if not self._api_checked:
            self._api_available = is_flask_api_available()
            self._api_checked = True
            
        # Add a flag to the request
        request.flask_api_available = self._api_available
        
        # Check for API dependency enforcement (logs out users if API is down too long)
        # Skip this for login/logout pages
        if not request.path.startswith('/admin/login') and not request.path.startswith('/logout'):
            user_logged_out = enforce_api_dependency(request)
            if user_logged_out:
                # Redirect to login page
                return redirect('/admin/login/')
        
        # Handle login attempts when Flask API is down
        if not self._api_available:
            # Check if this is an admin login attempt
            is_admin_login = request.path.startswith('/admin/login') and request.method == 'POST'
            is_login_page = request.path.startswith('/admin/login')
            
            if is_admin_login:
                # Redirect back to login page with an error message
                logger.warning("Login attempt blocked - Flask API is unavailable")
                messages.error(request, "⚠️ Login failed: The authentication service (Flask API) is not available. Please start the Flask server and try again.")
                return redirect(request.path)  # Redirect back to login page
            
            # Show warning on login page
            if is_login_page:
                messages.warning(request, "⚠️ The authentication service (Flask API) is not available. You cannot log in until the Flask server is started.")
            
            # Show warning in admin panel for already authenticated users
            elif request.path.startswith('/admin/') and hasattr(request, 'user') and request.user.is_authenticated:
                messages.error(request, "⚠️ The Flask API is not available. Some features may not work correctly and you may be logged out in your next session!")
                logger.warning("Flask API is not available. Admin functionality may be limited.")
        
        response = self.get_response(request)
        return response 