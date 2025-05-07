# FlavorVerse API Documentation

## Testing API Connection

**Endpoint:** `http://127.0.0.1:8000/api/test-auth/`

**Method:** GET

**Headers:** None required

**Response:**

```json
{
  "success": true,
  "message": "API is working",
  "endpoint": "test-auth",
  "method": "GET"
}
```

## User Registration API

**Endpoint:** `http://127.0.0.1:8000/api/register/`

**Method:** POST

**Headers:**

- Content-Type: application/json

**Request Body (JSON):**

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "StrongPassword123!",
  "phone": "1234567890",
  "address": "123 Main St",
  "gender": "male"
}
```

## User Login API

**Endpoint:** `http://127.0.0.1:8000/api/login/`

**Method:** POST

**Headers:**

- Content-Type: application/json

**Request Body (JSON):**

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

## Protected API (Test Authentication)

**Endpoint:** `http://127.0.0.1:8000/api/protected/`

**Method:** GET

**Headers:**

- Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

## Token Refresh

**Endpoint:** `http://127.0.0.1:8000/api/token/refresh/`

**Method:** POST

**Headers:**

- Content-Type: application/json

**Request Body (JSON):**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Token Verify

**Endpoint:** `http://127.0.0.1:8000/api/token/verify/`

**Method:** POST

**Headers:**

- Content-Type: application/json

**Request Body (JSON):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Troubleshooting

If you're getting HTML responses instead of JSON:

1. Make sure you've set the Content-Type header to "application/json"
2. For authenticated endpoints, include the Authorization header with "Bearer" prefix
3. Verify the server is running at http://127.0.0.1:8000
4. Check that you're using the right HTTP method (GET, POST, etc.)
5. Ensure the request body is valid JSON format
