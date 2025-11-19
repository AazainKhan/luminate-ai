# init_db.py
from tools.db import init_schema

if __name__ == "__main__":
    print("Initializing database schema...")
    init_schema()
    print("Database initialized successfully!")