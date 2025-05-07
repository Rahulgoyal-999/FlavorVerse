from django.urls import path, include
from . import views


urlpatterns=[

    path('profile/',views.profile_view,name='profilepage'),
    
    path('editprofile/',views.edit_profile_view,name='editprofilepage'),

    path('signup/', views.signup_view, name='signuppage'),
    
    path('login/', views.login_view, name='loginpage'),
    
    path('logout/', views.logout_view, name='logoutpage'),

    path('email-login/', views.email_login_view, name='email_login'),

]