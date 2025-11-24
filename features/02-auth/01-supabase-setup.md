# Feature 02: Authentication System - Supabase Setup

## Goal
Configure Supabase project and authentication for passwordless email OTP

## Tasks
- [x] Create Supabase project documentation
- [ ] Create Supabase project (manual step)
- [ ] Configure email templates
- [ ] Setup Row Level Security policies
- [ ] Configure redirect URLs for Chrome Extension

## Supabase Configuration Steps

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project: "luminate-ai-course-marshal"
   - Note down: Project URL and Anon Key

2. **Configure Authentication**
   - Enable Email provider
   - Configure email templates (OTP)
   - Set redirect URLs:
     - `chrome-extension://[EXTENSION_ID]/*`
     - `http://localhost:1947/*` (for Plasmo dev)

3. **Database Schema**
   - Will be created in Feature 11 (Student Mastery Tracking)
   - For now, auth.users table is sufficient

## Environment Variables Needed
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY (for backend)

## Next Steps
- Implement frontend auth in `extension/src/sidepanel.tsx`
- Implement backend auth middleware in `backend/app/api/middleware.py`

