# Supabase "Failed to fetch" Fix

## Issue
Getting `ERR_NAME_NOT_RESOLVED` when trying to sign in. The Supabase URL appears to be missing the `https://` protocol.

## Root Cause
The environment variable might not be properly injected, or the URL format is incorrect.

## Fixes Applied

### 1. Added Protocol Check
- Automatically adds `https://` if URL is missing protocol
- Ensures Supabase client gets a valid URL

### 2. Improved Error Logging
- Added debug logging to see what env vars are actually loaded
- Shows available environment variables
- Better error messages

### 3. Fixed Redirect URL
- Changed from `window.location.origin` to proper Chrome extension URL
- Uses `chrome-extension://[id]/sidepanel.html` format

## ⚠️ CRITICAL: Rebuild Required

After these changes, you MUST rebuild:

```bash
cd extension

# Stop dev server (Ctrl+C)

# Clear cache and rebuild
rm -rf .plasmo
npm run dev
```

## Verification Steps

1. **Check Console Logs**
   After rebuild, open extension and check console. You should see:
   ```
   🔍 Supabase Config Check: {
     url: "https://jedqonaiqpnqollmylkk.supabase.com...",
     hasKey: "✅",
     urlHasProtocol: "✅"
   }
   ```

2. **Test Authentication**
   - Enter student email
   - Click "Send Magic Link"
   - Should NOT see "Failed to fetch" error

3. **If Still Failing**
   Check console for:
   - What env vars are available
   - What the actual Supabase URL value is
   - Any CORS errors

## Common Issues

### Issue: Still seeing "Failed to fetch"
**Solution:** 
1. Verify `.env.local` has correct values
2. Rebuild extension (clear `.plasmo` folder)
3. Check Supabase project is active
4. Verify network connectivity

### Issue: "Supabase credentials not configured"
**Solution:**
- Check `.env.local` file exists in `extension/` directory
- Verify variable names start with `PLASMO_PUBLIC_`
- Rebuild extension after changing `.env.local`

### Issue: CORS errors
**Solution:**
- Check Supabase project settings
- Verify redirect URLs are whitelisted in Supabase dashboard
- Add `chrome-extension://[your-extension-id]/*` to allowed redirect URLs

## Next Steps

After rebuild:
1. Test authentication flow
2. Verify OTP email is sent
3. Check if magic link works
4. Test student/admin role detection

---

**Status:** Code fixed, rebuild required

