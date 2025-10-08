"""
Test Supabase Connection for COMP-237 Educate Mode
Simple connection test and schema verification.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

print("=" * 70)
print("🔗 Supabase Configuration")
print("=" * 70)
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_ANON_KEY: {SUPABASE_ANON_KEY[:20]}..." if SUPABASE_ANON_KEY else "SUPABASE_ANON_KEY: Not set")
print()

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ ERROR: Supabase credentials not found in .env file")
    print("\nPlease add to your .env file:")
    print("SUPABASE_URL=https://jedqonaiqpnqollmylkk.supabase.co")
    print("SUPABASE_ANON_KEY=your_anon_key")
    sys.exit(1)

try:
    from supabase import create_client
    
    print("✅ Supabase Python client installed")
    print("\n🔗 Connecting to Supabase...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Connection successful!")
    
    # Test query
    print("\n📊 Testing database query...")
    try:
        result = supabase.table('students').select("count").execute()
        print(f"✅ Query successful!")
        print(f"   Students table exists and has {result.count} records")
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("⚠️  Tables not yet created. Please run the SQL schema:")
            print(f"\n   1. Go to: {SUPABASE_URL.replace('.supabase.co', '.supabase.co/project/_/sql')}")
            print("   2. Copy contents of: development/backend/supabase_schema.sql")
            print("   3. Paste into SQL Editor and click 'Run'")
        else:
            print(f"⚠️  Query error: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Setup Complete!")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("   1. Create database schema (see instructions above)")
    print("   2. Update Navigate mode to use gemini-2.0-flash")
    print("   3. Update Educate mode to use gemini-2.5-flash")
    print("   4. Build parent orchestrator agent")
    print("   5. Update Chrome extension UI with tabs and chat history")
    
except ImportError:
    print("❌ Supabase Python client not installed")
    print("\n📦 Install with:")
    print("   pip install supabase")
    print("\nOr if using virtual environment:")
    print("   source .venv/bin/activate")
    print("   pip install supabase")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
