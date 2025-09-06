import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("JWT_SECRET:", os.getenv('JWT_SECRET'))