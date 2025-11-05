# Authentication Guide

This guide explains how to use the authentication system in the Juli Backend API.

## Overview

The authentication system uses:
- **Email and Password** for user credentials
- **JWT (JSON Web Tokens)** for session management
- **Bcrypt** for secure password hashing
- **OAuth2** password flow (compatible with Swagger UI)

## Registration

### Endpoint
`POST /api/v1/auth/register`

### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

### Response
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null
}
```

### Example (curl)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### Example (Python requests)
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "email": "user@example.com",
        "password": "securepassword123",
        "full_name": "John Doe"
    }
)
user = response.json()
print(user)
```

## Login

### Option 1: OAuth2 Form Login (Swagger Compatible)

**Endpoint:** `POST /api/v1/auth/login`

**Content-Type:** `application/x-www-form-urlencoded`

**Form Data:**
- `username`: user's email
- `password`: user's password

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

### Option 2: JSON Login

**Endpoint:** `POST /api/v1/auth/login/json`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Example (Python requests):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login/json",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)
token_data = response.json()
access_token = token_data["access_token"]
print(f"Token: {access_token}")
```

## Using the Access Token

Once you have an access token, include it in the `Authorization` header for protected endpoints:

```
Authorization: Bearer <your-access-token>
```

### Example (curl)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Example (Python requests)
```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)
user_info = response.json()
print(user_info)
```

### Example (JavaScript fetch)
```javascript
const token = "your-access-token-here";

fetch("http://localhost:8000/api/v1/auth/me", {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Get Current User

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null
}
```

## Test Token Validity

**Endpoint:** `POST /api/v1/auth/test-token`

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null
}
```

## Protecting Your Endpoints

To protect an endpoint and require authentication, use the `get_current_user` dependency:

```python
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/protected-route")
def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.email}!",
        "user_id": current_user.id
    }
```

### For Superuser-Only Endpoints

```python
from app.core.deps import get_current_superuser

@router.delete("/admin-only-route")
def admin_route(current_user: User = Depends(get_current_superuser)):
    return {"message": "Admin access granted"}
```

## Token Expiration

- Default token expiration: 30 minutes
- Configure in `.env` with `ACCESS_TOKEN_EXPIRE_MINUTES`
- After expiration, users must login again to get a new token

## Security Best Practices

1. **Use HTTPS in production** - Never send tokens over HTTP
2. **Change SECRET_KEY** - Generate a secure secret key:
   ```bash
   openssl rand -hex 32
   ```
3. **Store tokens securely** - Use httpOnly cookies or secure storage in mobile apps
4. **Implement refresh tokens** - For longer sessions (not included in this basic implementation)
5. **Add rate limiting** - Prevent brute force attacks on login endpoints
6. **Use strong passwords** - Minimum 8 characters enforced by default

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Incorrect email or password"
}
```

### 403 Forbidden
```json
{
  "detail": "The user doesn't have enough privileges"
}
```

## Testing with Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" button (top right)
3. Login using the `/api/v1/auth/login` endpoint
4. Copy the access token
5. Paste it in the authorization dialog
6. Click "Authorize"
7. All protected endpoints will now include the token automatically