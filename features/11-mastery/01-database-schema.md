# Feature 11: Student Mastery Tracking - Database Schema

## Goal
Create comprehensive Student Model schema in Supabase

## Database Schema

### Tables to Create in Supabase

1. **concepts** (Static Course Data)
```sql
CREATE TABLE concepts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  parent_concept_id TEXT REFERENCES concepts(id),
  prerequisites TEXT[],
  course_id TEXT DEFAULT 'COMP237'
);
```

2. **course_material** (RAG Index - stored in ChromaDB, metadata in Supabase)
- Actual content stored in ChromaDB
- Metadata can be synced to Supabase for queries

3. **student_mastery** (Dynamic Student Data)
```sql
CREATE TABLE student_mastery (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  concept_tag TEXT NOT NULL,
  mastery_score FLOAT CHECK (mastery_score >= 0 AND mastery_score <= 1),
  decay_factor FLOAT DEFAULT 0.95,
  last_assessed_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, concept_tag)
);
```

4. **interactions** (Interaction Log)
```sql
CREATE TABLE interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL, -- 'question_asked', 'quiz_attempt', 'explanation_viewed'
  concept_focus TEXT,
  outcome TEXT, -- 'correct', 'incorrect', 'confusion_detected', 'passive_read'
  sentiment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Row Level Security (RLS)

```sql
-- Students can only see their own mastery
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can view own mastery"
  ON student_mastery FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Students can update own mastery"
  ON student_mastery FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Students can insert own mastery"
  ON student_mastery FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

## Next Steps
- Feature 11: Implement Evaluator Node
- Feature 11: Create Evaluator Node

