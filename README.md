# Flavorverse API

A Django-based RESTful API service for the Flavorverse recipe sharing platform.

## Features

- User Authentication
  - Registration
  - Login with JWT tokens
  - Protected routes
- Recipe Management
- User Profile Management

## Prerequisites

- Python 3.8+
- Django
- Django REST Framework
- PostgreSQL (optional, SQLite by default)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Flavorverse_DJango_API
```

2. Create a virtual environment and activate it:
```bash
python -m venv env 
source env/bin/activate  # On Windows use: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables (optional):
Create a `.env` file in the root directory and add:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=your-database-url (optional)
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication

#### Register User
- **URL**: `/api/register/`
- **Method**: `POST`
- **Data Params**:
  ```json
  {
    "name": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Success Response**: `201 CREATED`
  ```json
  {
    "success": true,
    "message": "User registered successfully",
    "user": {
      "id": "integer",
      "name": "string",
      "email": "string"
    },
    "tokens": {
      "refresh": "string",
      "access": "string"
    }
  }
  ```

#### Login
- **URL**: `/api/login/`
- **Method**: `POST`
- **Data Params**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "message": "Login successful",
    "tokens": {
      "refresh": "string",
      "access": "string"
    },
    "user": {
      "id": "integer",
      "name": "string",
      "email": "string"
    }
  }
  ```

### Protected Routes

All protected routes require an Authorization header:
```
Authorization: Bearer <access_token>
```

## Error Handling

The API uses conventional HTTP response codes:
- `2xx` for success
- `4xx` for client errors
- `5xx` for server errors

Error responses follow this format:
```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Optional array of specific errors"]
}
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
We follow PEP 8 guidelines for Python code. You can check your code style using:
```bash
flake8 .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please raise an issue in the repository or contact the development team.

# FlavorVerse

