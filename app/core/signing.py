"""HMAC-SHA256 token signing for email confirmation and password reset links"""
import hashlib
import hmac
import json
import struct
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta
from typing import Optional


def _b64_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).decode("ascii").strip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return urlsafe_b64decode((data + padding).encode("ascii"))


def _make_signature(key: str, msg: bytes) -> bytes:
    return hmac.new(key.encode(), msg, hashlib.sha256).digest()


def _verify_signature(key: str, signature: bytes, msg: bytes) -> bool:
    return hmac.compare_digest(signature, _make_signature(key, msg))


def sign(data: dict, key: str, max_age: int = 3600) -> str:
    """
    Sign data with HMAC-SHA256 and embed an expiration timestamp.

    Args:
        data: Dictionary payload to sign
        key: Secret key for signing
        max_age: Token validity in seconds (default: 1 hour)

    Returns:
        URL-safe base64 encoded signed token
    """
    if not key:
        raise ValueError("Empty string is not allowed as a key")

    expires_at = datetime.utcnow() + timedelta(seconds=max_age)

    msg_bytes = json.dumps(data, separators=(",", ":")).encode()
    timestamp_bytes = struct.pack("!I", int(expires_at.timestamp()))

    signature = _make_signature(key, timestamp_bytes + msg_bytes)

    return _b64_encode(signature + timestamp_bytes + msg_bytes)


def verify(signed_data: str, key: str) -> Optional[dict]:
    """
    Verify a signed token and return the payload if valid.

    Args:
        signed_data: The signed token string
        key: Secret key used for signing

    Returns:
        The original data dict if signature is valid and not expired, None otherwise
    """
    if not key:
        raise ValueError("Empty string is not allowed as a key")

    try:
        decoded = _b64_decode(signed_data)
    except Exception:
        return None

    digest_size = hashlib.sha256().digest_size

    if len(decoded) <= digest_size + 4:
        return None

    signature = decoded[:digest_size]
    timestamp_bytes = decoded[digest_size:digest_size + 4]
    msg_bytes = decoded[digest_size + 4:]

    if not _verify_signature(key, signature, timestamp_bytes + msg_bytes):
        return None

    expiration_timestamp = struct.unpack("!I", timestamp_bytes)[0]
    if expiration_timestamp < datetime.utcnow().timestamp():
        return None

    return json.loads(msg_bytes.decode())
