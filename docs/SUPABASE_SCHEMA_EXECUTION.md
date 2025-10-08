# Execute Supabase Schema - Quick Guide

**Target**: Create COMP-237 Educate Mode database tables  
**Database**: https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk

---

## Method 1: Supabase SQL Editor (Recommended)

### Steps:

1. **Open SQL Editor**
   ```
   https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/sql
   ```

2. **Create New Query**
   - Click "+ New query" button (top right)
   - Name it: "COMP-237 Educate Mode Schema"

3. **Copy SQL Schema**
   - Open file: `development/backend/supabase_schema.sql`
   - Copy entire contents (Ctrl+A, Ctrl+C)

4. **Paste and Execute**
   - Paste into SQL Editor
   - Click "Run" (bottom right)
   - Wait for success message

5. **Verify Tables Created**
   ```sql
   -- Run this query to check tables
   SELECT tablename FROM pg_tables 
   WHERE schemaname = 'public' 
   ORDER BY tablename;
   ```
   
   **Expected output** (6 tables):
   - misconceptions
   - quiz_responses
   - session_history
   - spaced_repetition
   - students
   - topic_mastery

---

## Method 2: Python Script (Alternative)

If you prefer to use Python:

```bash
# 1. Ensure you're in the backend directory
cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend

# 2. Activate virtual environment
source ../../.venv/bin/activate

# 3. Install supabase if not already
pip install supabase

# 4. Run setup script
python setup_supabase.py

# 5. Follow on-screen instructions to copy SQL to Supabase SQL Editor
```

---

## Verification Steps

### 1. Check Tables Exist

In Supabase SQL Editor, run:

```sql
-- List all tables
SELECT 
    tablename,
    schemaname
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

### 2. Test Helper Function

```sql
-- Test get_or_create_student function
SELECT get_or_create_student('test-fingerprint-12345');
```

Should return a UUID.

### 3. Check Student Was Created

```sql
SELECT * FROM students;
```

Should show 1 row with `browser_fingerprint = 'test-fingerprint-12345'`.

### 4. Test Insert Session

```sql
-- Get the student_id from previous query
INSERT INTO session_history (student_id, mode, query, response)
VALUES (
    (SELECT student_id FROM students WHERE browser_fingerprint = 'test-fingerprint-12345'),
    'navigate',
    'What is machine learning?',
    '{"content": "Machine learning is..."}'::jsonb
);

-- Verify insert
SELECT * FROM session_history;
```

---

## Test Python Connection

Once schema is created, test from Python:

```bash
python test_supabase.py
```

**Expected output**:
```
🔗 Supabase Configuration
===============================================================
SUPABASE_URL: https://jedqonaiqpnqollmylkk.supabase.co
SUPABASE_ANON_KEY: sbp_96bdc15c1996f1b2...

✅ Supabase Python client installed

🔗 Connecting to Supabase...
✅ Connection successful!

📊 Testing database query...
✅ Query successful!
   Students table exists and has 1 records

🎉 Setup Complete!
```

---

## Common Issues

### Issue: "relation does not exist"
**Solution**: Schema not yet created. Follow Method 1 above.

### Issue: "permission denied"
**Solution**: Check RLS policies. The schema includes basic policies, but you may need to adjust.

### Issue: "function get_or_create_student does not exist"
**Solution**: Ensure you ran the ENTIRE schema SQL, including the function definition at the end.

### Issue: Python import error
```
ModuleNotFoundError: No module named 'supabase'
```
**Solution**:
```bash
pip install supabase
```

---

## Next Steps After Schema Creation

1. ✅ **Test connection**: `python test_supabase.py`
2. ✅ **Update FastAPI**: Add Supabase logging to endpoints
3. ✅ **Build UI**: Add tabs and chat history sidebar
4. ✅ **Math Agent**: Start building Math Translation Agent

---

## Schema Summary

**Tables Created**:
- `students` (1 row so far)
- `session_history` (0 rows)
- `topic_mastery` (0 rows)
- `misconceptions` (0 rows)
- `quiz_responses` (0 rows)
- `spaced_repetition` (0 rows)

**Indexes Created**: 8 total
- `idx_students_fingerprint`
- `idx_session_student`
- `idx_session_mode`
- `idx_session_week`
- `idx_misconceptions_unresolved`
- `idx_quiz_student_topic`
- `idx_spaced_rep_next_review`

**Functions Created**:
- `get_or_create_student(fingerprint)` - Returns UUID

**Types Created**:
- `comp237_topic` - ENUM type for 7 topics

**RLS Policies**: All tables have basic policies enabled

---

## Support

If you encounter any issues:

1. Check Supabase Logs:
   ```
   https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/logs
   ```

2. Check the SQL schema file:
   ```
   development/backend/supabase_schema.sql
   ```

3. All SQL is idempotent (`IF NOT EXISTS`), so you can re-run safely.

---

**Ready?** Open the SQL Editor and let's create those tables! 🚀
