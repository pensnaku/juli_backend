# Push Notifications Implementation Guide

This document describes how push notifications are implemented in the Aidbox backend for both iOS (APNs) and Android (FCM) devices.

## Overview

The push notification system consists of:
1. **Device Registration** - Users register their device tokens via `PushSubscription` resources
2. **Notification Creation** - Platform-specific payloads are generated
3. **Queue System** - Notifications are debounced to prevent duplicates
4. **Delivery** - Notifications are sent to APNs (iOS) or FCM (Android)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Trigger Event  │────▶│  Main Queue      │────▶│ Filtered Queue  │
│  (medication,   │     │  (debouncing)    │     │ (1s delay)      │
│   daily check)  │     └──────────────────┘     └────────┬────────┘
└─────────────────┘                                       │
                                                          ▼
                                              ┌───────────────────────┐
                                              │ send_push_notifications│
                                              │ _from_queue()         │
                                              └───────────┬───────────┘
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                          ┌─────────────────┐                         ┌─────────────────┐
                          │   iOS (APNs)    │                         │ Android (FCM)   │
                          │   aioapns lib   │                         │ REST API        │
                          └─────────────────┘                         └─────────────────┘
```

## Device Registration

Devices must register their push tokens by creating a `PushSubscription` resource:

```json
{
  "resourceType": "PushSubscription",
  "user": {
    "id": "<user-id>",
    "resourceType": "User"
  },
  "deviceToken": "<platform-specific-token>",
  "deviceType": "ios" | "android"
}
```

## Notification Payload Structure

Create notifications using a helper function that generates platform-specific payloads:

```python
def create_notification(title, text, data=None, aps_data=None):
    data = data or {}
    aps_data = aps_data or {}

    data["createdAt"] = format_date_time(get_now())

    return {
        "ios": {
            "aps": {
                "alert": {"title": title, "body": text},
                "badge": 0,
                "sound": "default",
                **aps_data,
            },
            "data": data,
        },
        "android": {
            "data": data,
            "notification": {"title": title, "body": text}
        },
    }
```

### iOS Payload (APNs)

The iOS payload follows Apple's [APNs documentation](https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/generating_a_remote_notification):

```json
{
  "aps": {
    "alert": {
      "title": "Notification Title",
      "body": "Notification body text"
    },
    "badge": 0,
    "sound": "default"
  },
  "data": {
    "createdAt": "2024-01-15T10:30:00Z",
    "customKey": "customValue"
  }
}
```

### Android Payload (FCM)

The Android payload follows [FCM documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#notification):

```json
{
  "message": {
    "token": "<device-token>",
    "notification": {
      "title": "Notification Title",
      "body": "Notification body text"
    },
    "data": {
      "createdAt": "2024-01-15T10:30:00Z",
      "customKey": "customValue"
    }
  }
}
```

---

## iOS Implementation (APNs)

### Dependencies

```
aioapns
```

### Configuration

| Config Key | Description |
|------------|-------------|
| `apns_pem_file` | Path to the APNs certificate PEM file |
| `use_sandbox` | Boolean - use sandbox (development) or production APNs server |

### Certificate Setup

1. Download your APNs certificate (.p12) from Apple Developer Portal
2. Convert to PEM format:
   ```bash
   openssl pkcs12 -in certificate.p12 -out apns.pem -nodes
   ```

### Client Initialization

```python
from aioapns import APNs, NotificationRequest

apns_client = APNs(
    client_cert="/path/to/apns.pem",
    use_sandbox=True,  # False for production
    no_cert_validation=True,  # May be needed for some SSL issues
)
```

### Sending Notifications

```python
from uuid import uuid4

async def send_ios_notification(device_token: str, notification: dict):
    request = NotificationRequest(
        device_token=device_token,
        message=notification["ios"],
        notification_id=str(uuid4()),
    )

    response = await apns_client.send_notification(request)

    if response.is_successful:
        print(f"Success: {response.status}")
    else:
        print(f"Failed: {response.status}, {response.description}")
        # Consider deleting invalid PushSubscription if token is invalid
```

### Error Handling

When APNs returns an unsuccessful response (e.g., invalid token), delete the `PushSubscription` resource to prevent future failed attempts:

```python
if not response.is_successful:
    await sdk.client.resource("PushSubscription", **subscription).delete()
```

---

## Android Implementation (FCM)

### Dependencies

```
google-auth
aiohttp
```

### Configuration

| Config Key | Description |
|------------|-------------|
| `fcm_service_account_file_path` | Path to Google service account JSON file |

### Service Account Setup

1. Go to Firebase Console > Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save the JSON file securely
4. Set the path in your configuration

### Authentication

FCM uses OAuth 2.0 with a service account:

```python
from google.oauth2 import service_account
from google.auth.transport.requests import Request

FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

def get_fcm_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        "/path/to/service-account.json",
        scopes=FCM_SCOPES
    )
    credentials.refresh(Request())

    return {
        "token": credentials.token,
        "project_id": credentials.project_id
    }
```

### Message Format

```python
def generate_fcm_message(device_token: str, notification: dict, data: dict, **kwargs):
    return {
        "message": {
            "token": device_token,
            "notification": notification,
            "data": data,
            **kwargs,
        }
    }
```

### Sending Notifications

```python
from aiohttp import ClientSession, ClientError

FCM_BASE_URL = "https://fcm.googleapis.com"

async def send_fcm_message(message: dict):
    access_data = get_fcm_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_data['token']}",
    }

    url = f"/v1/projects/{access_data['project_id']}/messages:send"

    async with ClientSession(FCM_BASE_URL, headers=headers) as session:
        async with session.post(url, json=message) as resp:
            if resp.status >= 400:
                raise ClientError(f"FCM error: {resp.status}")
            return await resp.json()
```

### Error Handling

When FCM returns an error (e.g., invalid token), delete the `PushSubscription`:

```python
try:
    await send_fcm_message(message)
except ClientError as ex:
    logger.error(f"FCM error for {subscription['id']}: {ex}")
    await sdk.client.resource("PushSubscription", **subscription).delete()
```

---

## Queue System (Debouncing)

The queue system prevents duplicate notifications when multiple events trigger rapidly:

```python
from asyncio import Queue, get_event_loop

MAIN_QUEUE = Queue()
FILTERED_QUEUE = Queue()

async def main_queue_worker():
    delays_list = []

    while True:
        notification_data = await MAIN_QUEUE.get()

        try:
            # Cancel existing delayed notification for same data
            existing = [d for d in delays_list if d[0] == notification_data]
            for delay_tuple in existing:
                delay_tuple[-1].cancel()

            # Schedule new notification with 1 second delay
            loop = get_event_loop()
            callback = loop.call_later(
                1,  # 1 second debounce
                FILTERED_QUEUE.put_nowait,
                notification_data
            )
            delays_list.append((notification_data, callback))
        finally:
            MAIN_QUEUE.task_done()

async def filtered_queue_worker():
    while True:
        notification_data = await FILTERED_QUEUE.get()

        try:
            user_pk = notification_data["user_pk"]
            notification = notification_data["notification"]
            await send_push_notifications_to_user(user_pk, notification)
        finally:
            FILTERED_QUEUE.task_done()
```

---

## Complete Send Flow

```python
async def send_push_notification(user_pk: str, notification: dict):
    """Add notification to the debouncing queue."""
    await MAIN_QUEUE.put({
        "user_pk": user_pk,
        "notification": notification
    })

async def send_push_notifications_to_user(user_pk: str, notification: dict):
    """Actually send notifications to all user devices."""

    # Fetch all device subscriptions for this user
    subscriptions = await sdk.client.resources("PushSubscription") \
        .search(user=user_pk) \
        .fetch_all()

    for sub in subscriptions:
        if sub["deviceType"] == "ios":
            # Send via APNs
            request = NotificationRequest(
                device_token=sub["deviceToken"],
                message=notification["ios"],
                notification_id=str(uuid4()),
            )
            response = await apns_client.send_notification(request)

            if not response.is_successful:
                await sdk.client.resource("PushSubscription", **sub).delete()

        elif sub["deviceType"] == "android":
            # Send via FCM
            message = generate_fcm_message(
                device_token=sub["deviceToken"],
                notification=notification["android"]["notification"],
                data=notification["android"]["data"],
            )
            try:
                await send_fcm_message(message)
            except ClientError:
                await sdk.client.resource("PushSubscription", **sub).delete()
```

---

## Usage Example

```python
# Create and send a notification
notification = create_notification(
    title="Medication Reminder",
    text="Time to take your medication!",
    data={"type": "medication_reminder", "medication_id": "123"},
)

await send_push_notification(user_id, notification)
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `APNS_PEM_FILE` | Path to APNs certificate PEM file | Yes (for iOS) |
| `USE_SANDBOX` | Use APNs sandbox environment | Yes (for iOS) |
| `FCM_SERVICE_ACCOUNT_FILE` | Path to Firebase service account JSON | Yes (for Android) |

---

## Testing

A test endpoint is available for manual testing:

```
POST /send-push-notification

{
  "userId": "user-123",
  "notification": {
    "title": "Test Notification",
    "text": "This is a test push notification",
    "data": {
      "customKey": "customValue"
    }
  }
}
```

---

## Notification Types

This section documents all push notifications sent by the backend.

### 1. Medication Reminder

**Trigger:** Scheduled medication notification time
**Source:** `periodic_tasks/medication_push.py`

| Field | Value |
|-------|-------|
| **Title** | `Time to talk to juli` |
| **Text** | `Did you take {medication_name} today?` |
| **Data** | `{"action": "medicationNotification", "medicationStatementId": "<id>", "patientId": "<id>", "medicationName": "<name>", "time": "<time>"}` |
| **APS Data** | `{"category": "MEDICATION_CATEGORY"}` |

---

### 2. Daily Check-in - Default

**Trigger:** Scheduled daily notification time (no recent responses)
**Source:** `periodic_tasks/daily_push.py`

| Field | Value |
|-------|-------|
| **Title** | `juli's Here to Help` |
| **Text** | `Providing juli with as much information as possible will help us help you. Pop into juli to answer a few daily questions.` |
| **Data** | `{"action": "openMessenger", "tabIndex": 1}` |
| **APS Data** | `{"badge": 1}` |

---

### 3. Daily Check-in - 2 Days Since Last Response

**Trigger:** User hasn't completed a questionnaire in 2 days
**Source:** `periodic_tasks/daily_push.py`

| Field | Value |
|-------|-------|
| **Title** | `Time to Talk to juli` |
| **Text** | `Hey {patient_name}, juli didn't hear from you yesterday. How are you doing?` |
| **Data** | `{"action": "openMessenger", "tabIndex": 1}` |
| **APS Data** | `{"badge": 1}` |

---

### 4. Daily Check-in - 3 Days Since Last Response

**Trigger:** User hasn't completed a questionnaire in 3 days
**Source:** `periodic_tasks/daily_push.py`

| Field | Value |
|-------|-------|
| **Title** | `Check in with juli` |
| **Text** | `Just checking to see how your past few days have been. juli would love to hear from you!` |
| **Data** | `{"action": "openMessenger", "tabIndex": 1}` |
| **APS Data** | `{"badge": 1}` |

---

### 5. Daily Check-in - 4 Days Since Last Response

**Trigger:** User hasn't completed a questionnaire in 4 days
**Source:** `periodic_tasks/daily_push.py`

| Field | Value |
|-------|-------|
| **Title** | `Share Your Progress` |
| **Text** | `Did you know that the best way to keep {condition_name} under control is through a daily routine? Share your current progress so juli can better help you.` |
| **Data** | `{"action": "openMessenger", "tabIndex": 1}` |
| **APS Data** | `{"badge": 1}` |

---

### 6. Daily Check-in - 5+ Days Since Last Response (With Score)

**Trigger:** User hasn't completed a questionnaire in 5+ days and has a previous juli score
**Source:** `periodic_tasks/daily_push.py`

| Field | Value |
|-------|-------|
| **Title** | `What's the Score?` |
| **Text** | `juli misses you. Your latest juli score was {score}. That qualifies as {assessment} for your condition. juli wonders what your score would be now?` |
| **Data** | `{"action": "openMessenger", "tabIndex": 1}` |
| **APS Data** | `{"badge": 1}` |

---

### 7. Maintenance/Admin Broadcast

**Trigger:** Manual admin operation
**Endpoint:** `POST /maintenance/notify-platform-users`
**Source:** `maintenance/operations.py`

| Field | Value |
|-------|-------|
| **Title** | Custom (provided in request) |
| **Text** | Custom (provided in request) |
| **Data** | None |
| **APS Data** | None |

This is an admin endpoint for broadcasting custom notifications to all iOS or Android users. Requires a confirmation code for safety.

---

## Troubleshooting

### iOS Issues

1. **Certificate errors**: Ensure PEM file is correctly converted from .p12
2. **SSL verification errors**: May need `no_cert_validation=True` temporarily
3. **Invalid tokens**: APNs will return error; delete the PushSubscription

### Android Issues

1. **Authentication errors**: Verify service account file path and permissions
2. **Invalid tokens**: FCM returns 400/404; delete the PushSubscription
3. **Project ID mismatch**: Ensure service account matches your Firebase project
