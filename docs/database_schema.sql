-- Luminate AI Course Marshal - Database Schema
-- Run this in Supabase SQL Editor
-- Updated: December 2025 - Added agent tracking fields

-- Concepts table (static course data)
CREATE TABLE IF NOT EXISTS concepts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  parent_concept_id TEXT REFERENCES concepts(id),
  prerequisites TEXT[],
  course_id TEXT DEFAULT 'COMP237',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Student Mastery table
CREATE TABLE IF NOT EXISTS student_mastery (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  concept_tag TEXT NOT NULL,
  mastery_score FLOAT CHECK (mastery_score >= 0 AND mastery_score <= 1) DEFAULT 0.0,
  decay_factor FLOAT DEFAULT 0.95,
  last_assessed_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, concept_tag)
);

-- Interactions log table (UPDATED: added agent tracking)
CREATE TABLE IF NOT EXISTS interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('question_asked', 'quiz_attempt', 'explanation_viewed', 'code_executed')),
  concept_focus TEXT,
  outcome TEXT CHECK (outcome IN ('correct', 'incorrect', 'confusion_detected', 'passive_read')),
  sentiment TEXT,
  -- NEW: Agent tracking fields (December 2025)
  intent TEXT,  -- 'tutor', 'math', 'coder', 'syllabus_query', 'fast'
  agent_used TEXT,  -- Which specialized agent handled the request
  scaffolding_level TEXT CHECK (scaffolding_level IN ('hint', 'example', 'guided', 'explain', NULL)),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_student_mastery_user_id ON student_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_student_mastery_concept ON student_mastery(concept_tag);
CREATE INDEX IF NOT EXISTS idx_interactions_student_id ON interactions(student_id);
CREATE INDEX IF NOT EXISTS idx_interactions_concept ON interactions(concept_focus);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at);

-- Row Level Security Policies

-- Enable RLS
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Students can view their own mastery
CREATE POLICY "Students can view own mastery"
  ON student_mastery FOR SELECT
  USING (auth.uid() = user_id);

-- Students can update their own mastery
CREATE POLICY "Students can update own mastery"
  ON student_mastery FOR UPDATE
  USING (auth.uid() = user_id);

-- Students can insert their own mastery
CREATE POLICY "Students can insert own mastery"
  ON student_mastery FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Students can view their own interactions
CREATE POLICY "Students can view own interactions"
  ON interactions FOR SELECT
  USING (auth.uid() = student_id);

-- Students can insert their own interactions
CREATE POLICY "Students can insert own interactions"
  ON interactions FOR INSERT
  WITH CHECK (auth.uid() = student_id);

-- Admins can view all (for analytics)
CREATE POLICY "Admins can view all mastery"
  ON student_mastery FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.email LIKE '%@centennialcollege.ca'
    )
  );

CREATE POLICY "Admins can view all interactions"
  ON interactions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.email LIKE '%@centennialcollege.ca'
    )
  );

