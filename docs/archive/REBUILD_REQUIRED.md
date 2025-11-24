# 🔄 REBUILD REQUIRED - Environment Variable Fix

## Issue Fixed
Changed from `import.meta.env` to `process.env` for Plasmo environment variables.

**Plasmo uses `process.env.PLASMO_PUBLIC_*` not `import.meta.env.PLASMO_PUBLIC_*`**

## Files Updated
- ✅ `extension/src/lib/supabase.ts` - Now uses `process.env.PLASMO_PUBLIC_SUPABASE_URL`
- ✅ `extension/src/lib/api.ts` - Now uses `process.env.PLASMO_PUBLIC_API_URL`
- ✅ `extension/src/lib/codeExecution.ts` - Now uses `process.env.PLASMO_PUBLIC_API_URL`

## ⚠️ CRITICAL: You MUST Rebuild

Plasmo injects environment variables at **build time**. After code changes, you must rebuild:

```bash
cd extension

# Stop the dev server (Ctrl+C if running)

# Clear build cache
rm -rf .plasmo

# Rebuild
npm run dev
```

## Verification

After rebuilding, check the browser console. You should **NOT** see:
- ❌ "Supabase credentials not configured"
- ❌ "supabaseUrl is required"

You should see:
- ✅ Extension loads without errors
- ✅ Authentication form displays
- ✅ No Supabase errors

## Why This Happens

Plasmo:
1. Reads `.env.local` at build time
2. Injects `PLASMO_PUBLIC_*` variables into `process.env`
3. Replaces `process.env.PLASMO_PUBLIC_*` with actual values in the bundle

If you don't rebuild after code changes, the old code runs with old environment access patterns.

## Current .env.local (Verified ✅)

```
PLASMO_PUBLIC_SUPABASE_URL=https://jedqonaiqpnqollmylkk.supabase.com
PLASMO_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_-uhuU6SmP3Pv4qzKMzvd6A_gO0P5lUb
PLASMO_PUBLIC_API_URL=http://localhost:8000
```

✅ File exists  
✅ Format is correct  
✅ Variables are properly named

## Next Steps

1. **Rebuild extension** (see commands above)
2. **Reload extension in Chrome**
3. **Test authentication**
4. **Verify no console errors**

---

**Status:** Code fixed, rebuild required for changes to take effect.

