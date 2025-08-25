from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import text  # <- add this

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

from app.db.engine import init_db, engine  # import AFTER load_dotenv

def main():
    print("Creating tables…")
    init_db()
    # simple connectivity check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # <- wrap with text()
    print("Done.")

if __name__ == "__main__":
    main()

