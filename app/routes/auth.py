from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
import jwt
from ..services.auth import AuthService

auth_bp = Blueprint("auth", __name__)

def _norm_email(v: str | None) -> str:
    return (v or "").strip().lower()

def _jwt_encode(payload: dict) -> str:
    secret = current_app.config.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET not configured")
    return jwt.encode(payload, secret, algorithm="HS256")

@auth_bp.post("/auth/login")
def login():
    """
    POST /auth/login — verify email/password and issue a JWT.
    Uses AuthService for authentication.
    """
    data = request.get_json(silent=True) or {}
    email = _norm_email(data.get("email"))
    password = data.get("password") or ""
    
    if not email or not password:
        return {"error": "bad_request", "message": "email and password required"}, 400

    try:
        # Use AuthService for authentication
        user = AuthService.authenticate_user(email, password)
        if not user:
            return {"error": "invalid_credentials"}, 401

        # Generate JWT token using your existing method
        now = datetime.now(timezone.utc)
        exp = now + timedelta(hours=int(current_app.config.get("JWT_EXPIRES_HOURS", 24)))

        token = _jwt_encode({
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        })

        # Return user data (excluding sensitive fields)
        user_response = {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "default_access_level": user["default_access_level"],
        }
        
        return jsonify({"access_token": token, "user": user_response}), 200

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return {"error": "server_error"}, 500