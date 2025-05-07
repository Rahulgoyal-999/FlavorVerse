from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password

User = get_user_model()

API_MODE = True  # Set to True to ensure all responses are in JSON format

def ensure_json_response(view_func):
    def wrapper(request, *args, **kwargs):
        print(f"API Request: {request.method} {request.path}")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {request.headers}")
        
        if API_MODE and not (request.content_type and 'json' in request.content_type.lower()):
            print(f"Warning: Request content-type is not application/json: {request.content_type}")
        
        response = view_func(request, *args, **kwargs)
        
        if API_MODE and not isinstance(response, Response):
            print("Warning: Converting non-Response to JSON Response")
            return Response({
                'success': False,
                'error': 'Internal API configuration error. Contact administrator.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return response
    return wrapper

@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_json_response
def register_view(request):
    """
    API endpoint for user registration
    Expected request body:
    {
        "name": "string",
        "email": "string",
        "password": "string"
    }
    """
    try:
        data = request.data

        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(email=data['email']).exists():
            return Response({
                'success': False,
                'message': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate password
        try:
            validate_password(data['password'])
        except ValidationError as e:
            return Response({
                'success': False,
                'message': 'Password validation failed',
                'errors': e.messages
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        user = User.objects.create(
            name=data['name'],
            email=data['email'],
            password=make_password(data['password'])
        )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred during registration',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_json_response
def login_view(request):
    print("Login API called")
    
    # Handle both JSON and form data
    if request.content_type == 'application/json':
        # JSON data
        email = request.data.get('email')
        password = request.data.get('password')
        print(f"JSON login attempt: {email}")
    else:
        # Form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(f"Form login attempt: {email}")
    
    if not email or not password:
        print("Missing email or password")
        return Response({
            'success': False,
            'error': 'Please provide both email and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get user by email
        user = User.objects.get(email=email)
        print(f"User found: {user.email}")
        
        # Check password manually
        if check_password(password, user.password):
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
            print("Login successful")
            return Response({
                'success': True,
                'message': 'Login successful',
                'tokens': tokens,
                'user': {
                    'email': user.email,
                    'name': user.name,
                    'id': user.id
                }
            }, status=status.HTTP_200_OK)
        else:
            print("Invalid password")
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        print(f"User not found: {email}")
        return Response({
            'success': False,
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'You have access to this protected view',
            'user': {
                'email': request.user.email,
                'name': request.user.name,
                'id': request.user.id
            }
        })

@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_json_response
def test_auth(request):
    """Simple test endpoint to verify API is working"""
    return Response({
        'success': True,
        'message': 'API is working',
        'endpoint': 'test-auth',
        'method': request.method,
    })
