"""
Authentication module supporting JWT, PIN authentication, QR Badge scanning, and RBAC.
"""
import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify

JWT_SECRET = os.environ.get("JWT_SECRET", "kiosk-industry-edge-secret-key-2026")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 7 days


def create_token(user_id: int, role: str = "member") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session token"}), 401
        request.user_id = payload["user_id"]
        request.user_role = payload.get("role", "member")
        return fn(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if request.user_role not in allowed_roles:
                return jsonify({"error": f"Access denied. Requires one of roles: {allowed_roles}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
