from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from RegistrationApp import models
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
import string
import uuid
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@login_required
def profile_view(request):
    user = request.user
    context = {
        'name': user.name,
        'email': user.email,
        'avatar': user.avatar.url if user.avatar else None,
    }
    return render(request, "profile.html", context)


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.name = request.POST['name']
        user.email = request.POST['email']
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            if user.avatar:
                # Delete old avatar file if it exists
                user.avatar.delete(save=False)
            user.avatar = request.FILES['avatar']
        
        # Handle password change
        password = request.POST.get('password')
        if password:
            try:
                validate_password(password)
                user.set_password(password)
            except ValidationError as e:
                messages.error(request, '\n'.join(e.messages))
                return render(request, 'edit_profile.html', {
                    'name': user.name,
                    'email': user.email,
                    'avatar': user.avatar.url if user.avatar else None,
                })
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profilepage')
    
    return render(request, 'edit_profile.html', {
        'name': request.user.name,
        'email': request.user.email,
        'avatar': request.user.avatar.url if request.user.avatar else None,
    })



# def more_info_view(request):
#     return render(request, 'more_info.html')



def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')
        
        if password != cpassword:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
        else:
            try:
                validate_password(password)
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    phone=phone,
                    address=address,
                    gender=gender,
                    password=password
                )
                
                # Generate tokens for the new user
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                
                messages.success(request, 'Registration successful! You can now login.')
                return redirect('loginpage')
            except ValidationError as e:
                for error in e:
                    messages.error(request, error)

    return render(request, 'signup.html')


           

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')
        # user = authenticate(request, email=email, password=password)
        # if user:
        #     login(request, user)
        #     return redirect('homepage')
        # else:
        #     messages.error(request, "Invalid credentials. Please try again.")


        user = authenticate(request, email=email, password=password)
        if user:
            # Determine if the role matches the actual user status
            if (selected_role == 'admin' and user.is_superuser) or (selected_role == 'user' and not user.is_superuser):
                login(request, user)
                return redirect('homepage')
            else:
                messages.error(request, "Invalid credentials: Role mismatch")
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')




@login_required
def logout_view(request):
    logout(request)
    return redirect('landingpage')



def email_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate verification code
            verification_code = ''.join(random.choices(string.digits, k=6))
            # Store in session
            request.session['email_verification'] = {
                'email': email,
                'code': verification_code
            }
            # Send email
            send_mail(
                'FlavorVerse Login Verification',
                f'Your verification code is: {verification_code}',
                'flavorverse038@gmail.com',  # Use your actual from email
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Verification code sent to your email')
            return redirect('email_verification')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email')
    return render(request, 'email_login.html')

def get_backend_path_for_user(user):
    for backend in get_backends():
        if hasattr(backend, 'get_user'):
            try:
                if backend.get_user(user.pk):
                    return backend.__module__ + '.' + backend.__class__.__name__
            except Exception:
                continue
    # Fallback to ModelBackend
    return 'django.contrib.auth.backends.ModelBackend'



