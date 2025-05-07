from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from RegistrationApp import views as reg_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', include('FlavorverseApp.urls')),
    path('Register/', include('RegistrationApp.urls')),
    path('Recipes/', include('RecipesApp.urls')),
    path('login/', reg_views.login_view, name='login'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('api/', include('api_auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
