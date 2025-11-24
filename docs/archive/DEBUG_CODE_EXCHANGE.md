# Debug: Code Exchange Not Working

## Current State
- Magic link redirects correctly: `chrome-extension://.../sidepanel.html?code=cab5b655-1e6a-435a-9ee4-51fb6007bd48`
- Console shows: `❌ No session found`
- Code exchange not executing

## Enhanced Debugging

### Added Console Logs
- Shows if code is detected in URL
- Shows code exchange progress
- Shows success/failure with details
- Alert on errors for visibility

### Fixed useEffect Dependency
- Removed `exchangingCode` from dependency array (was causing re-render loop)
- Added timeout to run exchange after DOM ready

## Rebuild and Test

```bash
cd extension
npm run dev
```

After rebuild:
1. Reload extension
2. Request NEW OTP
3. Click magic link
4. Watch console for:
   ```
   🔍 Checking for auth code in URL: { hasCode: true, code: "cab5b655-1..." }
   🔐 Found auth code in URL, exchanging for session...
   ✅ Code exchanged successfully!
   ✅ User: your@email.com
   ```

If you see an alert popup with an error, share the error message.

## Common Issues

### Code not detected
- Check URL has `?code=` parameter
- Check console for "Checking for auth code" message

### Code exchange fails
- Check error message in console/alert
- Code may have expired (5 min limit)
- Request fresh OTP

### Still no session
- Check `detectSessionInUrl: true` in supabase.ts
- Check Chrome storage permissions
- Check Supabase Site URL configuration

---

**Next:** Rebuild and watch console closely

