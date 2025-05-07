from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from social_core.pipeline.partial import partial
import uuid

User = get_user_model()

def get_avatar(backend, strategy, details, response, user=None, *args, **kwargs):
    """Get user avatar from social provider if available."""
    if user and not user.avatar:
        if backend.name == 'facebook':
            url = f"https://graph.facebook.com/{kwargs['uid']}/picture?type=large"
            # Save URL to user avatar
            try:
                user.avatar_url = url
                user.save()
            except Exception as e:
                pass
                
        elif backend.name == 'google-oauth2' and 'picture' in response:
            url = response.get('picture')
            try:
                user.avatar_url = url
                user.save()
            except Exception as e:
                pass
                
        elif backend.name == 'github' and 'avatar_url' in response:
            url = response.get('avatar_url')
            try:
                user.avatar_url = url
                user.save()
            except Exception as e:
                pass
                
        elif backend.name == 'linkedin-oauth2':
            if 'profilePicture' in response:
                try:
                    url = response.get('profilePicture', {}).get('displayImage~', {}).get('elements', [{}])[0].get('identifiers', [{}])[0].get('identifier')
                    if url:
                        user.avatar_url = url
                        user.save()
                except Exception as e:
                    pass

def update_user_details(backend, strategy, details, response, user=None, *args, **kwargs):
    """Update user details based on social login info."""
    if user:
        changed = False
        
        # Update name if not set
        if not user.name and details.get('fullname'):
            user.name = details.get('fullname')
            changed = True
        elif not user.name and details.get('first_name') and details.get('last_name'):
            user.name = f"{details.get('first_name')} {details.get('last_name')}"
            changed = True
            
        # If any changes were made, save the user
        if changed:
            user.save() 
            
def social_user_creation(strategy, details, backend, user=None, *args, **kwargs):
    """Custom user creation for social auth that handles RegisterUser model fields."""
    if user:
        return {'is_new': False}
        
    email = details.get('email')
    if not email:
        # If provider doesn't supply email, we can't create account automatically
        return strategy.redirect(f'/Register/signup/?social_error=email_required&provider={backend.name}')
        
    # Check if user with this email already exists
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        # Update social provider information for existing user
        existing_user.social_provider = backend.name
        existing_user.save()
        return {
            'is_new': False,
            'user': existing_user
        }
    
    # Generate data for required fields when creating new user
    name = details.get('fullname', '')
    if not name and details.get('first_name') and details.get('last_name'):
        name = f"{details.get('first_name')} {details.get('last_name')}"
    
    # Generate random values for required fields
    # These should be updated by the user later through profile completion
    random_phone = f"social-{uuid.uuid4().hex[:8]}"
    address = "Please update your address"
    gender = "Other"  # Default gender
    
    fields = {
        'email': email,
        'name': name or f"User-{uuid.uuid4().hex[:8]}",
        'phone': random_phone,
        'address': address,
        'gender': gender,
        'social_provider': backend.name
    }
    
    user = User.objects.create_user(**fields)
    return {
        'is_new': True,
        'user': user
    } 