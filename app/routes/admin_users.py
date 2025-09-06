from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation
from ..services.auth import AuthService
from ..models.user import RoleEnum, AccessLevelEnum
from ..services.auth import AuthService
from functools import wraps

admin_users_bp = Blueprint("admin_users", __name__)

@admin_users_bp.post("/admin/users")
def create_user():
    """
    POST /admin/users — create a user using AuthService.
    Body: { name, email, password, role, default_access_level }
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_fields = ['email', 'password', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": "bad_request",
            "hint": {
                "required": ["email", "password", "role"],
                "role_allowed": [role.value for role in RoleEnum],
                "default_access_level_allowed": [access.value for access in AccessLevelEnum],
            },
        }), 400

    try:
        # Use AuthService to create user
        new_user = AuthService.create_user(data)
        
        # Convert datetime to ISO format for JSON response
        if isinstance(new_user.get("created_at"), datetime):
            new_user["created_at"] = new_user["created_at"].isoformat()
        
        return jsonify({"user": new_user}), 201

    except ValueError as e:
        # Handle validation errors from AuthService
        error_msg = str(e)
        if "already exists" in error_msg:
            return jsonify({"error": "email_exists"}), 409
        elif "Invalid" in error_msg:
            return jsonify({"error": "bad_request", "message": error_msg}), 400
        else:
            return jsonify({"error": "bad_request", "message": error_msg}), 400
            
    except IntegrityError as e:
        # Handle database integrity errors
        orig = getattr(e, "orig", None)
        sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)

        if isinstance(orig, UniqueViolation) or sqlstate == "23505":
            return jsonify({"error": "email_exists"}), 409

        current_app.logger.exception("create_user failed (integrity)")
        return jsonify({"error": "server_error"}), 500

    except Exception as e:
        current_app.logger.exception("create_user failed")
        if current_app.config.get("TESTING"):
            return jsonify({"error": "server_error", "detail": str(e)}), 500
        return jsonify({"error": "server_error"}), 500
    

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract user ID from JWT (you'll need to implement JWT parsing)
        # For now, this is a placeholder - you'll need to integrate with your JAuthService
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "unauthorized"}), 401
            
        # You'll need to implement JWT verification here
        # For now, this is a simplified version
        try:
            # This is a placeholder - integrate with your JWT verification
            user_id = 1  # This should come from JWT verification
            if not AuthService.is_admin(user_id):
                return jsonify({"error": "forbidden", "message": "Admin access required"}), 403
        except Exception:
            return jsonify({"error": "unauthorized"}), 401
            
        return f(*args, **kwargs)
    return decorated

@admin_users_bp.get("/admin/users")
@admin_required
def get_all_users():
    """GET /admin/users — get all users (admin only)"""
    try:
        users = AuthService.get_all_users()
        return jsonify({"users": users}), 200
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return jsonify({"error": "server_error"}), 500

@admin_users_bp.get("/admin/users/<int:user_id>")
@admin_required
def get_user(user_id):
    """GET /admin/users/<id> — get specific user (admin only)"""
    try:
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "not_found"}), 404
        return jsonify({"user": user}), 200
    except Exception as e:
        current_app.logger.error(f"Get user error: {str(e)}")
        return jsonify({"error": "server_error"}), 500

@admin_users_bp.put("/admin/users/<int:user_id>")
@admin_required
def update_user(user_id):
    """PUT /admin/users/<id> — update user (admin only)"""
    data = request.get_json(silent=True) or {}
    
    try:
        updated_user = AuthService.update_user(user_id, data)
        if not updated_user:
            return jsonify({"error": "not_found"}), 404
            
        return jsonify({"user": updated_user}), 200
        
    except ValueError as e:
        return jsonify({"error": "bad_request", "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Update user error: {str(e)}")
        return jsonify({"error": "server_error"}), 500