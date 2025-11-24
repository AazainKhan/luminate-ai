# Environment Variable Fix - Plasmo Extension

## Issue
`import.meta.env` is undefined at runtime, causing:
```
Uncaught TypeError: Cannot read properties of undefined (reading 'PLASMO_PUBLIC_SUPABASE_URL')
```

## Root Cause
Plasmo injects `PLASMO_PUBLIC_*` environment variables at **build time**, not runtime. If the extension was built before `.env.local` was created or updated, the variables won't be available.

## Solution Applied
Added safe access pattern with try-catch blocks and fallbacks:

```typescript
function getEnvVar(key: string, defaultValue: string = ""): string {
  try {
    if (typeof import.meta !== "undefined" && import.meta.env && import.meta.env[key]) {
      return import.meta.env[key] as string
    }
  } catch (e) {}
  
  try {
    if (typeof process !== "undefined" && process.env && process.env[key]) {
      return process.env[key] as string
    }
  } catch (e) {}
  
  return defaultValue
}
```

## Files Updated
1. `extension/src/lib/supabase.ts` - Added safe getEnvVar function
2. `extension/src/lib/api.ts` - Added safe getEnvVar function  
3. `extension/src/lib/codeExecution.ts` - Added safe getEnvVar function

## Critical: Rebuild Required

**You MUST rebuild the extension** for environment variables to be injected:

```bash
cd extension

# Stop the current dev server (Ctrl+C)

# Delete the build cache
rm -rf .plasmo

# Restart dev server
npm run dev
```

## Verification Steps

1. **Check .env.local exists:**
   ```bash
   cat extension/.env.local
   ```
   Should show:
   ```
   PLASMO_PUBLIC_SUPABASE_URL=...
   PLASMO_PUBLIC_SUPABASE_ANON_KEY=...
   PLASMO_PUBLIC_API_URL=http://localhost:8000
   ```

2. **Rebuild extension:**
   ```bash
   cd extension
   rm -rf .plasmo
   npm run dev
   ```

3. **Reload extension in Chrome:**
   - Go to `chrome://extensions/`
   - Click reload on your extension
   - Check console for errors

4. **Verify variables are loaded:**
   - Open extension side panel
   - Check browser console
   - Should NOT see "Supabase credentials not configured" warning

## Why This Happens

Plasmo uses Vite under the hood, which:
- Reads `.env.local` at **build time**
- Injects `PLASMO_PUBLIC_*` variables into the bundle
- Replaces `import.meta.env.PLASMO_PUBLIC_*` with actual values

If you:
- Created `.env.local` after building
- Changed `.env.local` after building
- Loaded an old build

Then the variables won't be available until you rebuild.

## Alternative: Hardcode for Development

If rebuild doesn't work, you can temporarily hardcode values:

```typescript
const supabaseUrl = "https://jedqonaiqpnqollmylkk.supabase.com"
const supabaseAnonKey = "sb_publishable_-uhuU6SmP3Pv4qzKMzvd6A_gO0P5lUb"
```

**⚠️ Never commit hardcoded values to git!**

## Status
✅ Code updated with safe access pattern
⚠️ **REQUIRES REBUILD** to take effect

