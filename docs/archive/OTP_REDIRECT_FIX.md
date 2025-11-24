# OTP Redirect Fix - Complete Guide

## Current Issue
- Magic link redirects to `http://localhost:3000` (doesn't exist)
- Shows "otp_expired" error
- Extension can't detect authentication

## Root Cause
Supabase needs redirect URLs to be **whitelisted in the dashboard**. Chrome extension URLs require special configuration.

## ✅ Solution: Configure Supabase Dashboard

### Step 1: Get Your Extension ID

1. Open Chrome → `chrome://extensions/`
2. Find "Luminate AI" extension
3. Enable "Developer mode" (if not already)
4. Copy the **Extension ID** (e.g., `fddloegfplkfjijkapbacjdhpobnkkpl`)

### Step 2: Configure Supabase Redirect URLs

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `jedqonaiqpnqollmylkk`
3. Navigate to: **Authentication** → **URL Configuration**
4. Scroll to **Redirect URLs** section
5. Add these URLs (one per line):
   ```
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/*
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/sidepanel.html
   http://localhost:1947/*
   http://localhost:3000/*
   ```
6. Click **Save**

**Important:** Replace `fddloegfplkfjijkapbacjdhpobnkkpl` with your actual extension ID if different!

### Step 3: Request New OTP

**Critical:** Old OTP links use the old redirect URL. You MUST request a fresh OTP after configuring Supabase.

1. Go back to extension
2. Enter your email again
3. Click "Send Magic Link"
4. Check email for NEW link
5. Click link immediately (they expire quickly)

### Step 4: Test Flow

1. Click magic link in email
2. Should redirect to extension (or configured URL)
3. Extension should detect auth state change
4. User should be logged in automatically

## How It Works

1. **Extension sends OTP request** with `emailRedirectTo: chrome-extension://[id]/sidepanel.html`
2. **Supabase sends email** with magic link
3. **User clicks link** → Supabase verifies token
4. **Supabase redirects** to whitelisted URL (extension)
5. **Extension detects** → `onAuthStateChange` listener fires
6. **Session stored** → User logged in

## Troubleshooting

### Issue: Still redirects to localhost:3000
**Solutions:**
- ✅ Verify redirect URLs are saved in Supabase dashboard
- ✅ Request a **NEW** OTP (old links use old redirect)
- ✅ Check extension ID is correct
- ✅ Wait a few seconds after saving Supabase config

### Issue: OTP expired error
**Solutions:**
- OTP links expire in ~1 hour
- Request a fresh OTP
- Click link immediately after receiving email
- Don't use old email links

### Issue: Extension doesn't detect login
**Solutions:**
- Check browser console for errors
- Verify `useAuth` hook is mounted
- Check Chrome storage permissions
- Reload extension after clicking magic link

### Issue: "Access Denied" error
**Solutions:**
- Redirect URL not whitelisted in Supabase
- Extension ID mismatch
- Request new OTP after fixing config

## Alternative: Manual Token Entry (If Redirect Fails)

If redirect URLs don't work, we can implement manual token entry:
1. User receives email with token
2. User copies token
3. Extension has input field for token
4. Extension verifies token with Supabase

**This requires code changes** - let me know if needed.

## Verification Checklist

- [ ] Extension ID copied correctly
- [ ] Supabase redirect URLs configured
- [ ] Redirect URLs saved in Supabase
- [ ] New OTP requested (not using old link)
- [ ] Magic link clicked immediately
- [ ] Extension detects auth state change
- [ ] User logged in successfully

---

**Status:** Code updated, Supabase dashboard configuration required  
**Next:** Configure Supabase dashboard, then request new OTP

