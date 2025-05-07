from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.views.generic import RedirectView


urlpatterns = [
    path('', views.landingpage_view, name='landingpage'),
    path('home/', views.homepage_view, name='homepage'),
    path('about/', views.aboutus_view, name='aboutpage'),
    path('contact/', views.contactus_view, name='contactpage'),
    path('contact/admin/', RedirectView.as_view(url='http://127.0.0.1:5000/admin/contact'), name='contact_admin'),
    path('contact/messages/', views.contact_messages_view, name='contact_messages'),
    path('myteam/', views.meetmyteam_view, name='myteampage'),
    
    # Login URL options - from simplest to most complex
    path('login/', views.django_login_view, name='loginpage'),  # Pure Django auth
    path('direct-login/', views.direct_login_view, name='direct_loginpage'),  # Session-based auth
    path('flask-login/', views.login_view, name='flask_loginpage'),  # Flask API-based auth
    
    path('logout/', views.logout_view, name='logoutpage'),
    path('profile/', views.profile_view, name='profilepage'),
    path('send-message/', views.send_message, name='send_message'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    
    # Debug path
    path('debug-info/', views.debug_info_view, name='debug_info'),
    
    # Existing registration URLs...
    
    # ... your other URL patterns
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/about/', views.about_api, name='about_api'),
    path('api/contact/', views.contact_api, name='contact_api'),
    path('api/login/', views.django_login_view, name='api_login'),  # Use Django-native auth for API too
    
    # Force JSON routes for debugging Postman issues
    path('about/json/', views.about_api, name='about_json'),
    path('contact/json/', views.contact_api, name='contact_json'),
]