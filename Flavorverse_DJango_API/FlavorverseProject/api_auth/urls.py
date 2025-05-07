from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register_view, name='api_register'),
    path('login/', views.login_view, name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('protected/', views.ProtectedView.as_view(), name='api_protected'),
    path('test-auth/', views.test_auth, name='api_test_auth'),
]