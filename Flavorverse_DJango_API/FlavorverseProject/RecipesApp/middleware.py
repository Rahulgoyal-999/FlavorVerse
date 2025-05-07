# Create a new file called middleware.py in your app directory

class LanguageMiddleware:
    """
    Middleware to handle language preferences for users
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if language is already set in session
        if 'language' not in request.session:
            # Try to get language from authenticated user's preference
            if request.user.is_authenticated:
                try:
                    from .models import UserLanguagePreference
                    preference = UserLanguagePreference.objects.get(user=request.user)
                    request.session['language'] = preference.language
                except Exception:
                    # Fall back to browser language or default
                    self._set_language_from_header(request)
            else:
                # Not logged in, use browser header
                self._set_language_from_header(request)
                
        # Continue processing
        response = self.get_response(request)
        return response
        
    def _set_language_from_header(self, request):
        """Set language from browser Accept-Language header"""
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Extract primary language code (e.g., 'en-US' -> 'en')
            lang_code = accept_language.split(',')[0].split('-')[0].lower()
            
            # List of supported language codes
            supported_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'hi', 'ar', 'ru']
            
            if lang_code in supported_langs:
                request.session['language'] = lang_code
            else:
                # Default to English if language not supported
                request.session['language'] = 'en'
        else:
            # No header, default to English
            request.session['language'] = 'en'


# Add this to your settings.py:
"""
MIDDLEWARE = [
    # ... your other middleware classes
    'yourapp.middleware.LanguageMiddleware',
]
"""