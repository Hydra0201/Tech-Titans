from app.core.database import SessionLocal, init_db
from app.service.auth import register_user, login_user

def start_app():
    # Initialize database FIRST
    init_db()
    
    db = SessionLocal()
    print("=== Welcome to CarbonBalance ===")
    choice = input("1: Login\n2: Register\nChoose an option: ")

    user = None
    if choice == '1':
        user = login_user(db)
    elif choice == '2':
        user = register_user(db)

    if not user:
        print("Exiting app.")
        return

    db.close()

if __name__ == "__main__":
    start_app()