from tools.db import _conn

try:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print("Successfully connected to PostgreSQL!")
            print("PostgreSQL version:", version[0])
            
            # Test if our tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """)
            tables = [row[0] for row in cur.fetchall()]
            print("\nTables in database:", ", ".join(tables) if tables else "No tables found")
            
except Exception as e:
    print("Error connecting to PostgreSQL:", e)
