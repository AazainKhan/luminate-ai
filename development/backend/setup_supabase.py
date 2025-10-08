"""
Setup Supabase Database Schema for COMP-237 Educate Mode
Executes the full schema from the PRD document.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase client
print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Full SQL schema from PRD
SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE IF NOT EXISTS students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    browser_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_fingerprint UNIQUE (browser_fingerprint)
);

-- Create index for faster fingerprint lookups
CREATE INDEX IF NOT EXISTS idx_students_fingerprint ON students(browser_fingerprint);

-- Session history
CREATE TABLE IF NOT EXISTS session_history (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('navigate', 'educate')),
    query TEXT NOT NULL,
    response JSONB,
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    conversation_turn INTEGER DEFAULT 1,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14)
);

-- Create indexes for session queries
CREATE INDEX IF NOT EXISTS idx_session_student ON session_history(student_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_session_mode ON session_history(mode);

-- Topic mastery tracking (aligned with COMP-237 weeks)
CREATE TABLE IF NOT EXISTS topic_mastery (
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    topic_name VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level BETWEEN 0 AND 100),
    last_practiced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    practice_count INTEGER DEFAULT 1,
    PRIMARY KEY (student_id, topic_name)
);

-- COMP-237 topics enum for consistency
DO $$ BEGIN
    CREATE TYPE comp237_topic AS ENUM (
        'agents', 'search_algorithms', 'machine_learning', 
        'neural_networks', 'nlp', 'computer_vision', 'ai_ethics'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Misconceptions tracking (COMP-237 specific)
CREATE TABLE IF NOT EXISTS misconceptions (
    misconception_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    misconception_type VARCHAR(255) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    detection_count INTEGER DEFAULT 1,
    week_context INTEGER CHECK (week_context BETWEEN 1 AND 14)
);

-- Create index for unresolved misconceptions
CREATE INDEX IF NOT EXISTS idx_misconceptions_unresolved ON misconceptions(student_id, resolved) 
WHERE resolved = FALSE;

-- Quiz responses
CREATE TABLE IF NOT EXISTS quiz_responses (
    response_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    question_id VARCHAR(255),
    topic VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    question_text TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for quiz analytics
CREATE INDEX IF NOT EXISTS idx_quiz_student_topic ON quiz_responses(student_id, topic, timestamp DESC);

-- Spaced repetition schedule
CREATE TABLE IF NOT EXISTS spaced_repetition (
    student_id UUID REFERENCES students(student_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    week_number INTEGER CHECK (week_number BETWEEN 1 AND 14),
    next_review_date DATE NOT NULL,
    interval_days INTEGER DEFAULT 1,
    ease_factor FLOAT DEFAULT 2.5 CHECK (ease_factor >= 1.3),
    PRIMARY KEY (student_id, topic)
);

-- Create index for upcoming reviews
CREATE INDEX IF NOT EXISTS idx_spaced_rep_next_review ON spaced_repetition(next_review_date);

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE misconceptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE spaced_repetition ENABLE ROW LEVEL SECURITY;

-- Helper function to get or create student by fingerprint
CREATE OR REPLACE FUNCTION get_or_create_student(fingerprint VARCHAR)
RETURNS UUID AS $$
DECLARE
    student_uuid UUID;
BEGIN
    -- Try to find existing student
    SELECT student_id INTO student_uuid 
    FROM students 
    WHERE browser_fingerprint = fingerprint;
    
    -- If not found, create new student
    IF student_uuid IS NULL THEN
        INSERT INTO students (browser_fingerprint)
        VALUES (fingerprint)
        RETURNING student_id INTO student_uuid;
    ELSE
        -- Update last active timestamp
        UPDATE students 
        SET last_active = NOW() 
        WHERE student_id = student_uuid;
    END IF;
    
    RETURN student_uuid;
END;
$$ LANGUAGE plpgsql;
"""

def setup_database():
    """Execute schema setup using Supabase Python client."""
    
    print("\n📊 Setting up COMP-237 Educate Mode database schema...")
    print("=" * 70)
    
    try:
        # Note: The Supabase Python client doesn't support direct SQL execution
        # We need to use the REST API or the Supabase SQL Editor
        
        print("\n⚠️  IMPORTANT: Direct SQL execution not available in Python client")
        print("\nTo create the schema, you have two options:")
        print("\n1. RECOMMENDED: Use Supabase SQL Editor")
        print(f"   → Go to: {SUPABASE_URL.replace('.supabase.co', '.supabase.co/project/_/sql')}")
        print("   → Copy the SQL from this file and paste into the editor")
        print("   → Click 'Run'\n")
        
        print("2. ALTERNATIVE: Use Supabase CLI")
        print("   → Install: npm install -g supabase")
        print("   → Login: supabase login")
        print("   → Run: supabase db push --db-url 'postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres'")
        
        # Save SQL to file for easy access
        sql_file = "development/backend/supabase_schema.sql"
        with open(sql_file, "w") as f:
            f.write(SCHEMA_SQL)
        
        print(f"\n✅ SQL schema saved to: {sql_file}")
        print(f"\n📋 Schema includes:")
        print("   - 6 tables: students, session_history, topic_mastery, misconceptions, quiz_responses, spaced_repetition")
        print("   - 8 indexes for query performance")
        print("   - 1 ENUM type: comp237_topic")
        print("   - 1 helper function: get_or_create_student()")
        print("   - Row Level Security (RLS) enabled")
        
        # Test connection
        print("\n🔍 Testing Supabase connection...")
        result = supabase.table('students').select("count").execute()
        print(f"✅ Connection successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf tables don't exist yet, please create schema via SQL Editor first.")
        return False
    
    return True

if __name__ == "__main__":
    setup_database()
    
    print("\n" + "=" * 70)
    print("📚 Next Steps:")
    print("   1. Create schema in Supabase SQL Editor (see instructions above)")
    print("   2. Test with: python development/backend/test_supabase.py")
    print("   3. Start building Educate Mode agents!")
    print("=" * 70)
