# Final Fixes - OTP Redirect & Build Cache

## Issues Fixed

### 1. OTP Redirect URL
- **Problem:** Email redirects to `localhost:3000` instead of extension
- **Solution:** Removed `emailRedirectTo` - extension will detect auth via `onAuthStateChange`
- **How it works:** User clicks email link → Supabase verifies → Extension detects session change

### 2. Build Cache Corruption
- **Problem:** `Cannot find module 'c81b3d5d6f6cb4e4'` errors
- **Solution:** Clear all caches and rebuild

## ⚠️ CRITICAL: Complete Rebuild Required

```bash
cd extension

# Stop dev server (Ctrl+C)

# Nuclear option - clear everything
rm -rf .plasmo
rm -rf node_modules/.cache
rm -rf .parcel-cache
rm -rf build
rm -rf dist

# Rebuild
npm run dev
```

## Supabase Dashboard Configuration

**IMPORTANT:** Configure redirect URLs in Supabase:

1. Go to: **Supabase Dashboard → Authentication → URL Configuration**
2. Add these redirect URLs:
   ```
   chrome-extension://fddloegfplkfjijkapbacjdhpobnkkpl/*
   http://localhost:1947/*
   http://localhost:3000/*
   ```

## How Authentication Works Now

1. **User enters email** → Extension sends OTP request
2. **User receives email** → Clicks verification link
3. **Supabase verifies** → Opens in browser (any URL)
4. **Extension detects** → `onAuthStateChange` listener fires
5. **User logged in** → Session stored in Chrome storage

## Testing After Rebuild

1. **Clear browser cache** (optional but recommended)
2. **Reload extension** in Chrome
3. **Enter email** and request OTP
4. **Click email link** (will open in browser)
5. **Check extension** - should auto-detect login

## If Still Having Issues

### Module Resolution Error
- Clear `.plasmo` folder completely
- Restart dev server
- Reload extension

### OTP Not Working
- Check Supabase dashboard redirect URLs
- Verify email domain is correct
- Check browser console for errors

### Auth State Not Detecting
- Check `useAuth` hook is listening
- Verify Chrome storage permissions
- Check Supabase client initialization

---

**Status:** Code fixed, rebuild + Supabase config needed

