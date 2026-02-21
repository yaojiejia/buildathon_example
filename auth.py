"""
Authentication module for the example task app.
Contains intentional security bugs for testing.
"""

import jwt
import time
from functools import wraps
from flask import request, jsonify

# BUG: Hardcoded secret key in source code
SECRET_KEY = "super-secret-key-12345"

# BUG: Token expiry set to 30 days — way too long
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 30


def create_token(user_id: int, username: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": time.time() + TOKEN_EXPIRY_SECONDS,
        # BUG: No 'iat' (issued at) claim, makes revocation impossible
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        # BUG: Not checking token expiry properly — time.time() vs datetime
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication on an endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        # BUG: Only checks for "Bearer " prefix, doesn't handle edge cases
        # like extra spaces, lowercase "bearer", etc.
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid token format"}), 401

        token = auth_header[7:]
        payload = decode_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Attach user info to request
        request.user_id = payload["user_id"]
        request.username = payload["username"]

        return f(*args, **kwargs)

    return decorated

