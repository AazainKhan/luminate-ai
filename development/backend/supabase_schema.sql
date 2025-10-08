-- ============================================================================
-- COMP-237 Educate Mode Database Schema
-- Supabase PostgreSQL
-- ============================================================================
-- 
-- Execute this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/sql
--
-- Tables:
--   1. students - Student profiles with browser fingerprinting
--   2. session_history - All student interactions (Navigate + Educate modes)
--   3. topic_mastery - Week-by-week mastery tracking for 8 COMP-237 topics
--   4. misconceptions - Detected student misconceptions (50+ types)
--   5. quiz_responses - Student quiz attempts and results
--   6. spaced_repetition - Spaced repetition scheduling
--
-- Features:
--   - UUID primary keys
--   - Week tracking (1-14 for COMP-237)
--   - Row Level Security (RLS) enabled
--   - Indexes for performance
--   - Helper function: get_or_create_student()
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table 1: Students
-- ============================================================================
CREATE TABLE IF NOT EXISTS students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    browser_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_fingerprint UNIQUE (browser_fingerprint)
);

-- Create index for faster fingerprint lookups
CREATE INDEX IF NOT EXISTS idx_students_fingerprint ON students(browser_fingerprint);

COMMENT ON TABLE students IS 'Student profiles identified by browser fingerprint';
COMMENT ON COLUMN students.browser_fingerprint IS 'Unique browser fingerprint for anonymous student identification';

-- ============================================================================
-- Table 2: Session History
-- ============================================================================
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
CREATE INDEX IF NOT EXISTS idx_session_week ON session_history(week_number);

COMMENT ON TABLE session_history IS 'All student interactions in both Navigate and Educate modes';
COMMENT ON COLUMN session_history.mode IS 'Navigate (info retrieval) or Educate (tutoring)';
COMMENT ON COLUMN session_history.week_number IS 'COMP-237 course week (1-14) if identifiable';

-- ============================================================================
-- Table 3: Topic Mastery (COMP-237 Aligned)
-- ============================================================================
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
        'agents', 
        'search_algorithms', 
        'machine_learning', 
        'neural_networks', 
        'nlp', 
        'computer_vision', 
        'ai_ethics'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

COMMENT ON TABLE topic_mastery IS 'Student mastery levels for 8 major COMP-237 topics';
COMMENT ON COLUMN topic_mastery.mastery_level IS 'Percentage mastery (0-100)';

-- ============================================================================
-- Table 4: Misconceptions (COMP-237 Specific - 50+ Types)
-- ============================================================================
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

COMMENT ON TABLE misconceptions IS 'Detected student misconceptions (DFS/BFS confusion, overfitting, etc.)';
COMMENT ON COLUMN misconceptions.misconception_type IS 'Type from 50+ COMP-237 misconception database';
COMMENT ON COLUMN misconceptions.resolved IS 'True after 3 consecutive correct demonstrations';

-- ============================================================================
-- Table 5: Quiz Responses
-- ============================================================================
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

COMMENT ON TABLE quiz_responses IS 'Student quiz attempts and results for mastery tracking';

-- ============================================================================
-- Table 6: Spaced Repetition Schedule
-- ============================================================================
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

COMMENT ON TABLE spaced_repetition IS 'Spaced repetition scheduling for optimal learning retention';

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================
-- Enable RLS on all tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE misconceptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE spaced_repetition ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (students can view their own data)
-- Note: These are simplified policies. Adjust based on auth requirements.

-- Drop existing policies if they exist (to make script idempotent)
DROP POLICY IF EXISTS "Allow anonymous student creation" ON students;
DROP POLICY IF EXISTS "Students can view own data" ON students;
DROP POLICY IF EXISTS "Students can insert sessions" ON session_history;
DROP POLICY IF EXISTS "Students can view own sessions" ON session_history;
DROP POLICY IF EXISTS "Allow topic mastery inserts" ON topic_mastery;
DROP POLICY IF EXISTS "Allow topic mastery views" ON topic_mastery;
DROP POLICY IF EXISTS "Allow misconception inserts" ON misconceptions;
DROP POLICY IF EXISTS "Allow misconception views" ON misconceptions;
DROP POLICY IF EXISTS "Allow quiz inserts" ON quiz_responses;
DROP POLICY IF EXISTS "Allow quiz views" ON quiz_responses;
DROP POLICY IF EXISTS "Allow spaced rep inserts" ON spaced_repetition;
DROP POLICY IF EXISTS "Allow spaced rep views" ON spaced_repetition;

-- Allow anonymous access for students table (browser fingerprinting)
CREATE POLICY "Allow anonymous student creation" ON students
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Students can view own data" ON students
    FOR SELECT USING (true);

-- Session history policies
CREATE POLICY "Students can insert sessions" ON session_history
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Students can view own sessions" ON session_history
    FOR SELECT USING (true);

-- Similar policies for other tables (simplified for anonymous access)
CREATE POLICY "Allow topic mastery inserts" ON topic_mastery
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow topic mastery views" ON topic_mastery
    FOR SELECT USING (true);

CREATE POLICY "Allow misconception inserts" ON misconceptions
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow misconception views" ON misconceptions
    FOR SELECT USING (true);

CREATE POLICY "Allow quiz inserts" ON quiz_responses
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow quiz views" ON quiz_responses
    FOR SELECT USING (true);

CREATE POLICY "Allow spaced rep inserts" ON spaced_repetition
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow spaced rep views" ON spaced_repetition
    FOR SELECT USING (true);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Get or create student by browser fingerprint
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

COMMENT ON FUNCTION get_or_create_student IS 'Get existing student by fingerprint or create new one';

-- ============================================================================
-- Optional: Enable Realtime (for live leaderboards/progress tracking)
-- ============================================================================
-- Uncomment to enable realtime updates for topic mastery
-- ALTER PUBLICATION supabase_realtime ADD TABLE topic_mastery;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these to verify schema is created correctly:

-- Check tables
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Check indexes
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;

-- Test get_or_create_student function
-- SELECT get_or_create_student('test-fingerprint-123');

-- Check student was created
-- SELECT * FROM students;

-- ============================================================================
-- NEW: Notes System
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID REFERENCES students(id) ON DELETE CASCADE,
  topic VARCHAR(100),
  content TEXT NOT NULL,
  context JSONB, -- Related messages, sources, etc.
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_student ON notes(student_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_topic ON notes(topic);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_notes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notes_updated_at_trigger
BEFORE UPDATE ON notes
FOR EACH ROW
EXECUTE FUNCTION update_notes_updated_at();

-- ============================================================================
-- NEW: Concept Graph / Relationships
-- ============================================================================

CREATE TABLE IF NOT EXISTS concept_relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_topic VARCHAR(100) NOT NULL,
  target_topic VARCHAR(100) NOT NULL,
  relationship_type VARCHAR(50) NOT NULL, -- 'prerequisite', 'related', 'next_step'
  strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_concept_source ON concept_relationships(source_topic);
CREATE INDEX IF NOT EXISTS idx_concept_target ON concept_relationships(target_topic);
CREATE INDEX IF NOT EXISTS idx_concept_type ON concept_relationships(relationship_type);

-- Prevent duplicate relationships
CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_unique 
ON concept_relationships(source_topic, target_topic, relationship_type);

-- ============================================================================
-- ENHANCED: Quiz Responses Table (add new columns)
-- ============================================================================

-- Add new columns to existing quiz_responses table
DO $$ 
BEGIN
    -- Add question_data column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quiz_responses' AND column_name = 'question_data'
    ) THEN
        ALTER TABLE quiz_responses ADD COLUMN question_data JSONB;
    END IF;
    
    -- Add time_taken_seconds column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'quiz_responses' AND column_name = 'time_taken_seconds'
    ) THEN
        ALTER TABLE quiz_responses ADD COLUMN time_taken_seconds INTEGER;
    END IF;
END $$;

-- ============================================================================
-- Helper Functions for Concept Graph
-- ============================================================================

-- Function to get related concepts
CREATE OR REPLACE FUNCTION get_related_concepts(
    p_topic VARCHAR(100),
    p_relationship_type VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE (
    topic VARCHAR(100),
    relationship VARCHAR(50),
    strength FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN cr.source_topic = p_topic THEN cr.target_topic
            ELSE cr.source_topic
        END as topic,
        cr.relationship_type as relationship,
        cr.strength
    FROM concept_relationships cr
    WHERE (cr.source_topic = p_topic OR cr.target_topic = p_topic)
      AND (p_relationship_type IS NULL OR cr.relationship_type = p_relationship_type)
    ORDER BY cr.strength DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to seed initial concept relationships (COMP-237 topics)
CREATE OR REPLACE FUNCTION seed_concept_relationships()
RETURNS void AS $$
BEGIN
    -- Clear existing relationships
    TRUNCATE concept_relationships;
    
    -- Machine Learning fundamentals
    INSERT INTO concept_relationships (source_topic, target_topic, relationship_type, strength) VALUES
    ('Introduction to AI', 'Machine Learning', 'next_step', 0.9),
    ('Machine Learning', 'Supervised Learning', 'prerequisite', 0.95),
    ('Machine Learning', 'Unsupervised Learning', 'prerequisite', 0.9),
    ('Machine Learning', 'Neural Networks', 'next_step', 0.85),
    
    -- Neural Networks
    ('Neural Networks', 'Perceptron', 'prerequisite', 0.9),
    ('Neural Networks', 'Backpropagation', 'prerequisite', 0.95),
    ('Neural Networks', 'Deep Learning', 'next_step', 0.9),
    ('Backpropagation', 'Gradient Descent', 'prerequisite', 0.95),
    
    -- Clustering
    ('Unsupervised Learning', 'K-means Clustering', 'prerequisite', 0.9),
    ('Unsupervised Learning', 'Hierarchical Clustering', 'related', 0.8),
    ('K-means Clustering', 'Mean Shift', 'related', 0.75),
    
    -- Search Algorithms
    ('Introduction to AI', 'Search Algorithms', 'prerequisite', 0.85),
    ('Search Algorithms', 'A* Algorithm', 'prerequisite', 0.9),
    ('Search Algorithms', 'Informed Search', 'prerequisite', 0.85),
    
    -- Optimization
    ('Gradient Descent', 'Stochastic Gradient Descent', 'next_step', 0.85),
    ('Gradient Descent', 'Adam Optimizer', 'next_step', 0.8),
    
    -- Related topics
    ('Perceptron', 'Logistic Regression', 'related', 0.7),
    ('K-means Clustering', 'PCA', 'related', 0.6),
    ('Neural Networks', 'CNN', 'next_step', 0.85),
    ('Neural Networks', 'RNN', 'next_step', 0.8);
    
    RAISE NOTICE 'Seeded concept relationships for COMP-237 topics';
END;
$$ LANGUAGE plpgsql;

-- Seed the relationships
SELECT seed_concept_relationships();

-- ============================================================================
-- Schema Complete! 🎉
-- ============================================================================
-- Next steps:
--   1. Test connection from Python: python development/backend/test_supabase.py
--   2. Integrate notes and concept graph endpoints
--   3. Build agentic UI components
-- ============================================================================
