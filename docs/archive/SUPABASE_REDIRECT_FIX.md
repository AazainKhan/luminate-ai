# Supabase Redirect URL Fix for Chrome Extensions

## Issues
1. Email redirects to `localhost:3000` instead of Chrome extension
2. OTP expires before user can click
3. Module resolution errors in build

## Root Cause
Chrome extensions can't directly receive redirect URLs from email links. Supabase needs special configuration.

## Solution

### Option 1: Manual Token Entry (Recommended for MVP)
Don't use emailRedirectTo - have users copy token from email and paste it.

### Option 2: Web Redirect Page
Create a web page that receives the Supabase redirect and opens the extension.

### Option 3: Configure Supabase Dashboard
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add redirect URLs:
   - `chrome-extension://[your-extension-id]/*`
   - `http://localhost:1947/*` (Plasmo dev server)

## Current Fix Applied
- Removed `emailRedirectTo` from OTP request
- Extension will listen for auth state changes
- User clicks link in email → Supabase verifies → Extension detects session

## Next Steps

### 1. Configure Supabase Dashboard
Go to: **Authentication → URL Configuration**

Add these redirect URLs:
```
chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/*
http://localhost:1947/*
```

### 2. Rebuild Extension
```bash
cd extension
rm -rf .plasmo node_modules/.cache .parcel-cache
npm run dev
```

### 3. Test Flow
1. User enters email
2. Receives OTP email
3. Clicks link in email
4. Supabase verifies token
5. Extension detects auth state change
6. User is logged in

## Alternative: Token-Based Flow
If redirect doesn't work, implement manual token entry:
- User receives email with token
- Enters token in extension
- Extension verifies token with Supabase

---

**Status:** Code updated, Supabase dashboard configuration needed

