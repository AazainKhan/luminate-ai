# OTP Expired & Extension Blocked - Fix

## Current Errors

1. **OTP expired**: `error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired`
2. **ERR_BLOCKED_BY_CLIENT**: Chrome is blocking the extension's own redirect
3. **WebSocket timeout**: Dev server HMR connection (can ignore)

## Root Causes

### 1. OTP Expired
- You're using an old magic link from before the redirect URL was changed
- OTP links expire quickly (typically 1 hour)
- Old links have the old `redirect_to` parameter

### 2. ERR_BLOCKED_BY_CLIENT
- Chrome extension needs `webRequest` permission for redirects
- Extension needs explicit Supabase host permission

## ✅ Fixes Applied

### 1. Updated Extension Permissions
Added to `package.json`:
- `webRequest` permission (for handling redirects)
- `https://*.supabase.co/*` host permission (explicit Supabase access)

### 2. Added Auth Logging
Enhanced `useAuth` hook with console logs to debug auth flow:
- Shows when session is found/not found
- Logs all auth state changes
- Shows user email and role when authenticated

## 🔄 Next Steps (CRITICAL)

### Step 1: Rebuild Extension
The permissions changed, so you MUST rebuild:

```bash
cd extension

# Stop dev server (Ctrl+C)

# Rebuild with new permissions
npm run dev
```

### Step 2: Reload Extension in Chrome
After rebuild:
1. Go to `chrome://extensions/`
2. Find "Luminate AI"
3. Click **Reload** button
4. Check that new permissions are applied

### Step 3: Request NEW OTP
**IMPORTANT:** Don't use old email links!

1. Open extension sidepanel
2. Enter your email
3. Click "Send Magic Link"
4. Check email for NEW link
5. Click link immediately (don't wait)

### Step 4: Monitor Console
Open Chrome DevTools → Console and watch for:
- `✅ Session found: [email] Role: student`
- `🔔 Auth state changed: SIGNED_IN [email]`

If you see these, authentication worked!

## Troubleshooting

### Still getting "OTP expired"
- **Solution:** You're using an old email link. Request a fresh OTP.

### Still getting "ERR_BLOCKED_BY_CLIENT"
- **Solution:** Reload extension after rebuild to apply new permissions.

### Extension doesn't detect login
- **Solution:** Check console logs for auth state changes. May need to open sidepanel after clicking magic link.

### WebSocket timeout
- **Solution:** Can ignore - this is HMR hot reload, not critical.

## Verification Checklist

- [ ] Extension rebuilt with new permissions
- [ ] Extension reloaded in Chrome (`chrome://extensions/`)
- [ ] Supabase redirect URLs configured (from earlier)
- [ ] Fresh OTP requested (not using old email link)
- [ ] Magic link clicked immediately
- [ ] Console shows auth state changes
- [ ] User logged in successfully

---

**Status:** Code updated with new permissions and logging  
**Next:** Rebuild extension → Reload in Chrome → Request NEW OTP

