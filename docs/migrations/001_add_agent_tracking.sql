-- Luminate AI Course Marshal - Schema Migration
-- Run this to add new columns to existing tables
-- Date: December 2025

-- Add new agent tracking columns to interactions table
ALTER TABLE interactions 
  ADD COLUMN IF NOT EXISTS intent TEXT,
  ADD COLUMN IF NOT EXISTS agent_used TEXT,
  ADD COLUMN IF NOT EXISTS scaffolding_level TEXT CHECK (scaffolding_level IN ('hint', 'example', 'guided', 'explain', NULL));

-- Add index for intent-based queries (useful for analytics)
CREATE INDEX IF NOT EXISTS idx_interactions_intent ON interactions(intent);
CREATE INDEX IF NOT EXISTS idx_interactions_agent ON interactions(agent_used);

-- Comment: This migration adds tracking for:
-- - intent: The detected intent (tutor, math, coder, syllabus_query, fast)
-- - agent_used: Which specialized agent handled the request
-- - scaffolding_level: For tutor agent, the level of scaffolding used
