import bcrypt
from sqlalchemy.orm import Session
from app.models.users import User
from datetime import datetime, timezone

def register_user(db: Session):
    username = input("Choose a username: ")
    email = input("Enter your email: ")
    password = input("Create a password: ")

    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        print("Username or email already exists.")
        return None

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(
        username=username,
        email=email,
        password_hash=hashed.decode('utf-8'),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    print("Registration successful.")
    return user

def login_user(db: Session):
    username = input("Username: ")
    password = input("Password: ")

    user = db.query(User).filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        print("Invalid username or password.")
        return None

    print(f"Welcome, {user.username}!")
    return user
