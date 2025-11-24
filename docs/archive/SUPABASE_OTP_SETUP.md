# Supabase OTP Setup for Chrome Extension

## Current Issue
OTP link redirects to `localhost:3000` and shows "otp_expired" error.

## Root Cause
Supabase needs redirect URLs to be whitelisted in the dashboard. Chrome extension URLs need special handling.

## Solution: Configure Supabase Dashboard

### Step 1: Get Your Extension ID
1. Go to `chrome://extensions/`
2. Find "Luminate AI" extension
3. Copy the Extension ID (e.g., `fddloegfplkfjijkapbacjdhpobnkkpl`)

### Step 2: Configure Supabase Redirect URLs

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Authentication** → **URL Configuration**
4. Under **Redirect URLs**, add:
   ```
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/*
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/sidepanel.html
   http://localhost:1947/*
   http://localhost:3000/*
   ```
5. Click **Save**

### Step 3: Alternative - Use Web Redirect Page

If Chrome extension URLs don't work, create a simple redirect page:

1. Create a web page (e.g., `https://yourdomain.com/auth-callback.html`)
2. Add this page URL to Supabase redirect URLs
3. The page can extract the token and communicate with extension

## How OTP Works Now

1. **User requests OTP** → Extension sends request with `emailRedirectTo`
2. **User receives email** → Clicks magic link
3. **Supabase verifies** → Redirects to configured URL
4. **Extension detects** → `onAuthStateChange` listener fires
5. **User logged in** → Session stored in Chrome storage

## Testing

1. Request new OTP (old links expire)
2. Click link immediately (don't wait)
3. Should redirect to extension or configured URL
4. Extension should detect auth state change

## Troubleshooting

### Issue: Still redirects to localhost:3000
**Solution:** 
- Check Supabase dashboard redirect URLs are saved
- Request a NEW OTP (old links use old redirect)
- Verify extension ID is correct

### Issue: OTP expired error
**Solution:**
- OTP links expire quickly (usually 1 hour)
- Request a fresh OTP
- Click link immediately after receiving

### Issue: Extension doesn't detect login
**Solution:**
- Check `useAuth` hook is mounted
- Verify Chrome storage permissions
- Check browser console for errors

---

**Status:** Code updated, Supabase dashboard configuration required

