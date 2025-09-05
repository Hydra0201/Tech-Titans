from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

from app.db.engine import SessionLocal
from app.services.auth import AuthService

def create_first_admin():
    """Create the first admin user if no users exist"""
    with SessionLocal() as session:
        from sqlalchemy import text
        user_count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        if user_count == 0:
            admin_data = {
                "email": "aaron@gmail.com",
                "password": "12345",
                "role": "admin",
                "name": "Aaron"
            }
            
            try:
                admin_user = AuthService.create_user(admin_data)
                print(f" First admin user created successfully!")
                print(f"   Email: {admin_user['email']}")
                print(f"   Password: {admin_data['password']}")
            except Exception as e:
                print(f" Error creating admin user: {e}")
        else:
            print("  Users already exist in database, skipping admin creation")

if __name__ == "__main__":
    create_first_admin()