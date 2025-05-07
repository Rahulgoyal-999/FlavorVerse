import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

def test_api_connection():
    """Test if the API is accessible"""
    url = f"{BASE_URL}/test-auth/"
    response = requests.get(url)
    print(f"API Connection Test: {response.status_code}")
    print(json.dumps(response.json(), indent=4))
    return response.status_code == 200

def register_user(email, name, password, phone=None, address=None, gender=None):
    """Register a new user"""
    url = f"{BASE_URL}/register/"
    data = {
        "email": email,
        "name": name,
        "password": password
    }
    
    # Add optional fields if provided
    if phone:
        data["phone"] = phone
    if address:
        data["address"] = address
    if gender:
        data["gender"] = gender
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    print(f"Registration Response: {response.status_code}")
    print(json.dumps(response.json(), indent=4))
    return response.json() if response.status_code in (200, 201) else None

def login_user(email, password):
    """Login a user and get tokens"""
    url = f"{BASE_URL}/login/"
    data = {
        "email": email,
        "password": password
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    print(f"Login Response: {response.status_code}")
    print(json.dumps(response.json(), indent=4))
    return response.json() if response.status_code == 200 else None

def test_protected_endpoint(access_token):
    """Test accessing a protected endpoint"""
    url = f"{BASE_URL}/protected/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    print(f"Protected Endpoint Response: {response.status_code}")
    print(json.dumps(response.json(), indent=4))
    return response.status_code == 200

def refresh_token(refresh_token):
    """Get a new access token using the refresh token"""
    url = f"{BASE_URL}/token/refresh/"
    data = {"refresh": refresh_token}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    print(f"Token Refresh Response: {response.status_code}")
    print(json.dumps(response.json(), indent=4))
    return response.json().get("access") if response.status_code == 200 else None

def main():
    """Run a complete API test flow"""
    # Step 1: Test API connection
    if not test_api_connection():
        print("API connection failed. Make sure the Django server is running.")
        return
    
    # Step 2: Register a new user
    email = "testuser@example.com"
    name = "Test User"
    password = "StrongPassword123!"
    register_response = register_user(email, name, password)
    
    if not register_response:
        print("Registration failed.")
        
        # Try logging in instead (in case user already exists)
        login_response = login_user(email, password)
        if not login_response:
            print("Login also failed. API might not be working correctly.")
            return
        
        # Get tokens from login response
        access_token = login_response["tokens"]["access"]
        refresh_token = login_response["tokens"]["refresh"]
    else:
        # Get tokens from registration response
        access_token = register_response["tokens"]["access"]
        refresh_token = register_response["tokens"]["refresh"]
    
    # Step 3: Test protected endpoint
    test_protected_endpoint(access_token)
    
    # Step 4: Test token refresh
    new_access_token = refresh_token(refresh_token)
    if new_access_token:
        print("Successfully refreshed token.")
        # Test protected endpoint with new token
        test_protected_endpoint(new_access_token)

if __name__ == "__main__":
    main() 