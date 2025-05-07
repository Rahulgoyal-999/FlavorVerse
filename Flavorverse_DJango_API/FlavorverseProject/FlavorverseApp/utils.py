import requests
import logging
import time
from django.contrib.auth import logout
from django.contrib import messages

logger = logging.getLogger(__name__)

# Global variable to track last successful API connection
_last_successful_api_check = 0

def is_flask_api_available():
    """
    Check if the Flask API is available by making a simple health check request.
    Returns True if the API is available, False otherwise.
    
    Also updates the global last successful check timestamp.
    """
    global _last_successful_api_check
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
        if response.status_code == 200:
            _last_successful_api_check = time.time()
            return True
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Flask API health check failed: {str(e)}")
        return False

def enforce_api_dependency(request):
    """
    Enforce that the Flask API has been available recently.
    If not, log the user out and show a message.
    
    Returns True if the user was logged out, False otherwise.
    """
    global _last_successful_api_check
    
    # Only check for authenticated users
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return False
        
    # If API has never been successfully checked, always enforce dependency
    if _last_successful_api_check == 0:
        if not is_flask_api_available():
            logger.warning(f"Logging out user {request.user.email} - Flask API unavailable and no previous successful connection")
            logout(request)
            messages.error(request, "You have been logged out because the Flask API is unavailable. Please start the Flask server and log in again.")
            return True
            
    # Check if it's been more than 5 minutes since last successful check
    api_timeout = 300  # 5 minutes in seconds
    time_since_last_check = time.time() - _last_successful_api_check
    
    if time_since_last_check > api_timeout:
        # Only log out if the API is currently unavailable
        if not is_flask_api_available():
            logger.warning(f"Logging out user {request.user.email} - Flask API unavailable for more than {api_timeout} seconds")
            logout(request)
            messages.error(request, "You have been logged out because the Flask API has been unavailable for too long. Please start the Flask server and log in again.")
            return True
            
    return False 