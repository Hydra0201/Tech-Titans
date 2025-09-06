from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text
from ..db.engine import SessionLocal
from ..schema.user import UserRole

from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Access the JWT_SECRET
JWT_SECRET  = os.getenv("JWT_SECRET")

JWT_ALGORITHM = "HS256"

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(hashed_password: str, password: str) -> bool:
        """Verify a stored password against one provided by user."""
        return check_password_hash(hashed_password, password)
    
    @staticmethod
    def generate_token(user_id: int, email: str, role: str) -> str:
        """Generate JWT token for authenticated user."""
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload if valid."""
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if successful."""
        with SessionLocal() as session:
            user = session.execute(
                text("SELECT * FROM users WHERE email = :email AND is_active = TRUE"),
                {'email': email}
            ).mappings().first()
            
            if not user or not AuthService.verify_password(user['password_hash'], password):
                return None
            
            return dict(user)
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user account (admin only)."""
        with SessionLocal() as session:
            # Check if user already exists
            existing_user = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {'email': user_data['email']}
            ).scalar()
            
            if existing_user:
                raise ValueError("User already exists")
            
            # Validate role
            try:
                role = UserRole(user_data['role'])
            except ValueError:
                raise ValueError("Invalid role")
            
            # Hash password
            password_hash = AuthService.hash_password(user_data['password'])
            
            # Create user
            user_insert_data = {
                'email': user_data['email'],
                'password_hash': password_hash,
                'role': role.value,
                'name': user_data.get('name'),
                'is_active': True
            }
            
            result = session.execute(
                text("""
                    INSERT INTO users (email, password_hash, role, name, is_active)
                    VALUES (:email, :password_hash, :role, :name, :is_active)
                    RETURNING id, email, role, name, is_active, created_at
                """),
                user_insert_data
            )
            new_user = result.mappings().first()
            session.commit()
            
            return dict(new_user)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        with SessionLocal() as session:
            user = session.execute(
                text("""
                    SELECT id, email, role, name, is_active, created_at
                    FROM users WHERE id = :user_id
                """),
                {'user_id': user_id}
            ).mappings().first()
            
            return dict(user) if user else None
    
    @staticmethod
    def get_all_users() -> list:
        """Get all users (admin only)."""
        with SessionLocal() as session:
            users = session.execute(
                text("""
                    SELECT id, email, role, name, is_active, created_at
                    FROM users ORDER BY created_at DESC
                """)
            ).mappings().all()
            
            return [dict(user) for user in users]
    
    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information (admin only)."""
        with SessionLocal() as session:
            # Check if user exists
            existing_user = session.execute(
                text("SELECT id FROM users WHERE id = :user_id"),
                {'user_id': user_id}
            ).scalar()
            
            if not existing_user:
                return None
            
            # Validate role if provided
            if 'role' in update_data:
                try:
                    UserRole(update_data['role'])
                    update_data['role'] = update_data['role']  # Keep as string for SQL
                except ValueError:
                    raise ValueError("Invalid role")
            
            # Build update query dynamically
            set_clauses = []
            params = {'user_id': user_id}
            
            for field in ['email', 'name', 'is_active', 'role']:
                if field in update_data:
                    set_clauses.append(f"{field} = :{field}")
                    params[field] = update_data[field]
            
            if not set_clauses:
                raise ValueError("No fields to update")
            
            set_clause = ", ".join(set_clauses)
            
            result = session.execute(
                text(f"""
                    UPDATE users 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                    RETURNING id, email, role, name, is_active, created_at
                """),
                params
            )
            updated_user = result.mappings().first()
            session.commit()
            
            return dict(updated_user) if updated_user else None
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user has admin role."""
        with SessionLocal() as session:
            user_role = session.execute(
                text("SELECT role FROM users WHERE id = :user_id AND is_active = TRUE"),
                {'user_id': user_id}
            ).scalar()
            
            return user_role == UserRole.ADMIN.value if user_role else False