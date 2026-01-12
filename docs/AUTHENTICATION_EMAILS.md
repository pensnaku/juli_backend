# Authentication Email Flows

This document describes all authentication-related emails sent to users, including the complete flow, API endpoints, and email templates.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Email Templates](#2-email-templates)
3. [Signup Welcome Email](#3-signup-welcome-email)
4. [Email Confirmation](#4-email-confirmation)
5. [Password Reset](#5-password-reset)
6. [Implementation Guide](#6-implementation-guide)

---

## 1. Overview

The application sends 3 types of authentication emails:

| Email Type | Postmark Template Alias | Trigger |
|------------|-------------------------|---------|
| Welcome/Signup | `welcome-to-juli` | User signs up |
| Email Confirmation | `email-confirmation` | User requests resend of confirmation |
| Password Reset | `reset-password` | User requests password reset |

**Email Provider:** Postmark (api.postmarkapp.com)

**Sender Address:** `info@juli.co` (configurable via `POSTMARK_EMAIL_FROM_INFO`)

---

## 2. Email Templates

Templates are located in `docs/email_templates/`:

- `signup-email-confirmation.html` - Welcome email with confirmation link
- `reset-password.html` - Password reset email
- `email-layout.html` - Base layout wrapper for all emails

### Template Syntax

Templates use Jinja2 syntax with two blocks:

```html
{% block subject %}
Your Email Subject Here
{% endblock %}

{% block body %}
<p>Your email content here</p>
<a href="{{ variable }}">Link</a>
{% endblock %}
```

---

## 3. Signup Welcome Email

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SIGNUP FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  User                    App                     Backend                  Email Service
   │                       │                         │                          │
   │  Enter email/password │                         │                          │
   │──────────────────────>│                         │                          │
   │                       │                         │                          │
   │                       │  POST /auth/$signup     │                          │
   │                       │────────────────────────>│                          │
   │                       │                         │                          │
   │                       │                         │  1. Validate email/password
   │                       │                         │  2. Check if user exists │
   │                       │                         │  3. Create Patient       │
   │                       │                         │  4. Create User with:    │
   │                       │                         │     - emailConfirmationStatus: "pending"
   │                       │                         │                          │
   │                       │                         │  Send welcome email      │
   │                       │                         │─────────────────────────>│
   │                       │                         │                          │
   │                       │    { status: "OK" }     │                          │
   │                       │<────────────────────────│                          │
   │                       │                         │                          │
   │     Show success      │                         │                          │
   │<──────────────────────│                         │                          │
   │                       │                         │                          │
   │                       │                         │      Deliver email       │
   │<─────────────────────────────────────────────────────────────────────────────
   │                       │                         │                          │
   │  Click confirmation link                        │                          │
   │─────────────────────────────────────────────────>                          │
   │                       │                         │                          │
   │                       │                         │  Verify token            │
   │                       │                         │  Update emailConfirmationStatus: "completed"
   │                       │                         │                          │
   │     Show success page │                         │                          │
   │<────────────────────────────────────────────────│                          │
```

### API Endpoint

**POST /auth/$signup**

```json
// Request
{
  "resource": {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "storeCountry": "US",        // optional
    "storeRegion": "california"  // optional
  }
}

// Response
{
  "status": "OK"
}
```

**Security Notes:**
- Returns 200 OK even if email already exists (prevents user enumeration)
- Password must pass security validation
- Email is converted to lowercase

### Email Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `email_confirmation_link` | Signed URL to confirm email | `https://api.juli.co/auth/$confirm-account/{signed_token}` |
| `subject` | Email subject | "Welcome to juli" |

### Link Generation

```python
def generate_account_confirmation_link(user_id, user_email):
    return "{}/auth/$confirm-account/{}".format(
        config.backend_public_url,
        sign(
            {
                "user_id": user_id,
                "action": "confirm_email",
                "email": user_email,
            },
            key=config.secret_key,
            max_age=3600 * 24 * 4,  # 4 days expiry
        ),
    )
```

### Database Changes

**User created with:**
```json
{
  "resourceType": "User",
  "email": "user@example.com",
  "password": "<hashed>",
  "active": true,
  "userType": "patient",
  "data": {
    "emailConfirmationStatus": "pending",
    "patient": {
      "resourceType": "Patient",
      "id": "<patient_id>"
    },
    "storeCountry": "US",
    "storeRegion": "california"
  }
}
```

---

## 4. Email Confirmation

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMAIL CONFIRMATION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

  User                    App                     Backend                  Email Service
   │                       │                         │                          │
   │  Request resend       │                         │                          │
   │──────────────────────>│                         │                          │
   │                       │                         │                          │
   │                       │  POST /auth/$send-confirmation-link               │
   │                       │────────────────────────>│                          │
   │                       │                         │                          │
   │                       │                         │  Get user from session   │
   │                       │                         │  Generate confirmation link
   │                       │                         │                          │
   │                       │                         │  Send confirmation email │
   │                       │                         │─────────────────────────>│
   │                       │                         │                          │
   │                       │    { status: "OK" }     │                          │
   │                       │<────────────────────────│                          │
   │                       │                         │                          │
   │                       │                         │      Deliver email       │
   │<─────────────────────────────────────────────────────────────────────────────
   │                       │                         │                          │
   │  Click link in email  │                         │                          │
   │                       │                         │                          │
   │  GET /auth/$confirm-account/{token}             │                          │
   │─────────────────────────────────────────────────>                          │
   │                       │                         │                          │
   │                       │                         │  1. Verify signed token  │
   │                       │                         │  2. Check action = "confirm_email"
   │                       │                         │  3. Validate user email matches
   │                       │                         │  4. Update status to "completed"
   │                       │                         │                          │
   │     HTML success page │                         │                          │
   │<────────────────────────────────────────────────│                          │
```

### API Endpoints

**POST /auth/$send-confirmation-link** (Authenticated)

```json
// Request - No body needed, uses session user

// Response
{
  "status": "OK"
}
```

**GET /auth/$confirm-account/{token}** (Public)

```
// Success: Returns HTML page "email-confirmation"
// Failure: Returns HTML page "something-happen" with 400 status
```

### Email Template Variables

| Variable | Description |
|----------|-------------|
| `email_confirmation_link` | Signed URL to confirm email |
| `subject` | Email subject |

---

## 5. Password Reset

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PASSWORD RESET FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  User                    App                     Backend                  Email Service
   │                       │                         │                          │
   │  Enter email          │                         │                          │
   │──────────────────────>│                         │                          │
   │                       │                         │                          │
   │                       │  POST /auth/$send-reset-password-link             │
   │                       │────────────────────────>│                          │
   │                       │                         │                          │
   │                       │                         │  1. Find user by email   │
   │                       │                         │  2. Create ResetPasswordRequest
   │                       │                         │     with status: "active"│
   │                       │                         │  3. Generate reset link  │
   │                       │                         │                          │
   │                       │                         │  Send reset email        │
   │                       │                         │─────────────────────────>│
   │                       │                         │                          │
   │                       │    { status: "OK" }     │                          │
   │                       │<────────────────────────│                          │
   │                       │                         │                          │
   │                       │                         │      Deliver email       │
   │<─────────────────────────────────────────────────────────────────────────────
   │                       │                         │                          │
   │  Click link in email  │                         │                          │
   │──────────────────────>│                         │                          │
   │                       │                         │                          │
   │                       │  (App opens with token) │                          │
   │                       │                         │                          │
   │  Enter new password   │                         │                          │
   │──────────────────────>│                         │                          │
   │                       │                         │                          │
   │                       │  POST /auth/$reset-password                       │
   │                       │────────────────────────>│                          │
   │                       │                         │                          │
   │                       │                         │  1. Verify signed payload│
   │                       │                         │  2. Check action = "reset_password"
   │                       │                         │  3. Validate ResetPasswordRequest is active
   │                       │                         │  4. Update user password │
   │                       │                         │  5. Mark request "completed"
   │                       │                         │  6. Cancel other active requests
   │                       │                         │  7. Close all active sessions
   │                       │                         │                          │
   │                       │    { status: "OK" }     │                          │
   │                       │<────────────────────────│                          │
   │                       │                         │                          │
   │     Show success      │                         │                          │
   │<──────────────────────│                         │                          │
```

### API Endpoints

**POST /auth/$send-reset-password-link** (Public)

```json
// Request
{
  "resource": {
    "email": "user@example.com"
  }
}

// Response
{
  "status": "OK"
}
```

**Security Note:** Returns 200 OK even if email doesn't exist (prevents user enumeration)

**POST /auth/$reset-password** (Public)

```json
// Request
{
  "resource": {
    "password": "NewSecurePassword123!",
    "signed_payload": "<signed_token_from_email_link>"
  }
}

// Response (Success)
{
  "status": "OK"
}

// Response (Failure)
HTTP 400 Bad Request
```

**GET /links/reset-password/{token}** (Public - Universal Link)

Returns HTML page that triggers app deep link.

### Email Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `reset_password_link` | Signed URL to reset password | `https://links.juli.co/links/reset-password/{signed_token}` |
| `subject` | Email subject | "Reset your password" |

### Link Generation

```python
def generate_reset_password_link(user_id, reset_password_request_id):
    return "{}/links/reset-password/{}".format(
        config.mobile_app_universal_url,
        sign(
            {
                "user_id": user_id,
                "action": "reset_password",
                "request_id": reset_password_request_id,
            },
            key=config.secret_key,
            max_age=3600 * 24 * 1,  # 1 day expiry
        ),
    )
```

### Database Changes

**ResetPasswordRequest created:**
```json
{
  "resourceType": "ResetPasswordRequest",
  "user": { "resourceType": "User", "id": "<user_id>" },
  "status": "active"
}
```

**After successful reset:**
- ResetPasswordRequest status changed to "completed"
- All other active ResetPasswordRequests for user are "cancelled"
- All active user sessions are closed

---

## 6. Implementation Guide

### Required Environment Variables

```bash
# Email Service
POSTMARK_API_TOKEN=your_postmark_api_token
POSTMARK_EMAIL_FROM_DEFAULT=support@yourdomain.com
POSTMARK_EMAIL_FROM_INFO=info@yourdomain.com

# URLs
BACKEND_PUBLIC_URL=https://api.yourdomain.com
MOBILE_APP_UNIVERSAL_URL=https://links.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com

# Security
SECRET_KEY=your_secret_key_for_signing_tokens
```

### Token Expiry Times

| Token Type | Expiry |
|------------|--------|
| Email Confirmation | 4 days |
| Password Reset | 1 day |

### Database Models Required

```python
# User model
class User:
    id: str
    email: str
    password: str  # hashed
    active: bool
    userType: str  # "patient", "admin", etc.
    data: dict  # Contains emailConfirmationStatus, patient reference, etc.

# Patient model
class Patient:
    id: str
    # ... patient fields

# ResetPasswordRequest model
class ResetPasswordRequest:
    id: str
    user_id: str  # Foreign key to User
    status: str   # "active", "completed", "cancelled"
    created_at: datetime
```

### Email Sending Function

```python
async def send_postmark_template_email(
    to: str,
    template_alias: str,
    template_model: dict,
    sender: str = None
):
    """
    Send email using Postmark template.

    Args:
        to: Recipient email address
        template_alias: Postmark template alias (e.g., "welcome-to-juli")
        template_model: Variables to pass to template
        sender: Sender email address (defaults to config)
    """
    url = "https://api.postmarkapp.com/email/withTemplate"

    payload = {
        "From": sender or config.postmark_email_from_default,
        "To": to,
        "TemplateAlias": template_alias,
        "TemplateModel": template_model,
    }

    async with aiohttp.ClientSession() as session:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": config.postmark_api_token,
        }
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                logging.error(f"Failed to send email: {resp}")
```

### Token Signing/Verification

```python
from itsdangerous import URLSafeTimedSerializer

def sign(payload: dict, key: str, max_age: int) -> str:
    """Sign a payload with expiry."""
    serializer = URLSafeTimedSerializer(key)
    return serializer.dumps(payload)

def verify(token: str, key: str) -> dict | None:
    """Verify and decode a signed token."""
    serializer = URLSafeTimedSerializer(key)
    try:
        return serializer.loads(token, max_age=max_age)
    except Exception:
        return None
```

### Postmark Template Setup

Create these templates in Postmark dashboard:

1. **welcome-to-juli**
   - Variables: `email_confirmation_link`

2. **email-confirmation**
   - Variables: `email_confirmation_link`

3. **reset-password**
   - Variables: `reset_password_link`

---

## Email Template Files

The HTML templates are available in `docs/email_templates/`:

| File | Purpose |
|------|---------|
| `signup-email-confirmation.html` | Welcome email sent on signup |
| `reset-password.html` | Password reset email |
| `email-layout.html` | Base layout wrapper |
