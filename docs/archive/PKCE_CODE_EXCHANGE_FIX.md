# PKCE Code Exchange Fix - Complete Solution

## Current Issue
Magic link redirects to extension with `code` parameter:
```
chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/sidepanel.html?code=4908bfa8-4175-44e8-99f3-1d4679146a7d
```

The `code` needs to be exchanged for a session.

## Root Cause
Supabase PKCE flow returns an **auth code** (not a token) that must be exchanged for a session using `exchangeCodeForSession()`.

## ✅ Fixes Applied

### 1. Enabled Auto Code Detection
Updated `supabase.ts`:
- Changed `detectSessionInUrl: true` (was `false`)
- This allows Supabase client to auto-detect and exchange codes

### 2. Added Manual Code Exchange Handler
Updated `sidepanel.tsx`:
- Extracts `code` parameter from URL
- Calls `exchangeCodeForSession(code)` 
- Cleans up URL after exchange
- Shows loading state during exchange

### 3. Enhanced Logging
- Console logs show code exchange progress
- Error messages if exchange fails

## 🔧 Supabase Dashboard Configuration

### Update Site URL
1. Go to **Authentication** → **URL Configuration**
2. Set **Site URL** to:
   ```
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl
   ```
   (Without the `/*` wildcard - Site URL doesn't accept wildcards)

### Keep Redirect URLs
Your redirect URLs are correct:
```
chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/*
chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/sidepanel.html
http://localhost:1947/*
http://localhost:3000/*
```

## 🔄 How It Works Now

1. **User requests OTP** → Extension sends request
2. **User clicks magic link** → Supabase verifies
3. **Supabase redirects** → `chrome-extension://.../sidepanel.html?code=...`
4. **Extension detects code** → Extracts from URL
5. **Code exchange** → Calls `exchangeCodeForSession(code)`
6. **Session created** → Stored in Chrome storage
7. **Auth state updates** → User logged in automatically
8. **URL cleaned** → Code parameter removed

## 🧪 Testing

1. **Rebuild extension** (code changed):
   ```bash
   cd extension
   npm run dev
   ```

2. **Reload extension** in Chrome (`chrome://extensions/`)

3. **Request NEW OTP** (old links won't work)

4. **Click magic link** from email

5. **Watch console** for:
   - `🔐 Found auth code in URL, exchanging for session...`
   - `✅ Code exchanged successfully! Session: [email]`
   - `🔔 Auth state changed: SIGNED_IN [email]`

6. **Verify login** - Should see welcome message with your email

## Troubleshooting

### Code exchange fails
- **Check:** Console for error messages
- **Solution:** Ensure Supabase Site URL is set correctly (no wildcards)

### Still seeing code in URL
- **Check:** Code exchange completed successfully
- **Solution:** URL should auto-clean, but you can manually reload

### Auth state not updating
- **Check:** `useAuth` hook is listening
- **Solution:** Check console for auth state change events

### Code expired
- **Solution:** Request a fresh OTP (codes expire in 5 minutes)

## Verification Checklist

- [ ] Extension rebuilt with new code
- [ ] Extension reloaded in Chrome
- [ ] Supabase Site URL updated (no wildcards)
- [ ] Redirect URLs still configured
- [ ] Fresh OTP requested
- [ ] Magic link clicked
- [ ] Code exchange completed (check console)
- [ ] User logged in successfully

---

**Status:** ✅ Code exchange implemented  
**Next:** Rebuild → Reload → Test with fresh OTP

