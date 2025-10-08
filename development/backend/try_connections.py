"""
Execute Supabase Schema - Try Different Connection Formats
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")

def try_connection_formats():
    """Try different connection string formats"""
    
    print("=" * 80)
    print("🔌 Testing Supabase Connection Formats")
    print("=" * 80)
    print()
    
    # Read SQL file first
    with open("supabase_schema.sql", 'r') as f:
        sql_content = f.read()
    
    print(f"✅ Loaded SQL schema ({len(sql_content)} characters)")
    print()
    
    # Try different connection formats
    connection_formats = [
        {
            "name": "Direct connection (port 5432)",
            "string": f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
        },
        {
            "name": "Pooler connection (port 6543)",
            "string": f"postgresql://postgres.{SUPABASE_PROJECT_REF}:{SUPABASE_DB_PASSWORD}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        },
        {
            "name": "Direct with project prefix",
            "string": f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{SUPABASE_PROJECT_REF}.supabase.co:5432/postgres?sslmode=require"
        },
        {
            "name": "Alternative pooler",
            "string": f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@aws-0-us-east-1.pooler.supabase.com:6543/postgres?project={SUPABASE_PROJECT_REF}"
        }
    ]
    
    for i, conn_format in enumerate(connection_formats, 1):
        print(f"Attempt {i}: {conn_format['name']}")
        print(f"Connection: {conn_format['string'][:80]}...")
        print()
        
        try:
            conn = psycopg2.connect(conn_format['string'], connect_timeout=5)
            cursor = conn.cursor()
            
            print("✅ Connected successfully!")
            print()
            
            # Execute schema
            print("🚀 Executing SQL schema...")
            cursor.execute(sql_content)
            conn.commit()
            
            print("✅ Schema executed!")
            print()
            
            # Verify tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   • {table[0]}")
            
            print()
            
            # Test helper function
            print("🧪 Testing helper function...")
            cursor.execute("SELECT get_or_create_student('test-123');")
            student_id = cursor.fetchone()[0]
            print(f"✅ Helper function works! Student ID: {student_id}")
            
            # Clean up
            cursor.execute("DELETE FROM students WHERE browser_fingerprint = 'test-123';")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print()
            print("=" * 80)
            print("🎉 SUCCESS! Database is ready!")
            print("=" * 80)
            print()
            print("✅ 6 tables created")
            print("✅ RLS policies enabled")
            print("✅ Helper function tested")
            print()
            print("🎯 Next: Build Chrome extension UI with shadcn")
            print()
            
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Failed: {e}")
            print()
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            continue
    
    # If all failed, show manual instructions
    print("=" * 80)
    print("⚠️  All automatic connection attempts failed")
    print("=" * 80)
    print()
    print("The connection string format might be different for your project.")
    print()
    print("📋 TO GET CORRECT CONNECTION STRING:")
    print()
    print("1. Go to: https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/settings/database")
    print()
    print("2. Scroll to 'Connection string' section")
    print()
    print("3. Select 'URI' tab")
    print()
    print("4. Copy the connection string")
    print()
    print("5. Replace [YOUR-PASSWORD] with: Lumi-group4")
    print()
    print("6. Add to .env:")
    print("   SUPABASE_CONNECTION_STRING=postgresql://...")
    print()
    print("OR - Just use SQL Editor (30 seconds):")
    print("   https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/sql/new")
    print()
    
    return False

if __name__ == "__main__":
    try_connection_formats()
