# Module Resolution Error Fix

## Error
```
Uncaught Error: Cannot find module 'c81b3d5d6f6cb4e4'
```

## Root Cause
This is a Plasmo/Parcel bundler cache corruption issue. The hash-like module ID suggests the bundler can't resolve a dependency (likely Supabase client).

## Solution

### Option 1: Quick Fix (Recommended)
```bash
cd extension

# Stop dev server (Ctrl+C)

# Clear all caches
rm -rf .plasmo
rm -rf node_modules/.cache
rm -rf .parcel-cache
rm -rf build

# Rebuild
npm run dev
```

### Option 2: Nuclear Option (If Option 1 doesn't work)
```bash
cd extension

# Stop dev server (Ctrl+C)

# Remove everything
rm -rf .plasmo
rm -rf node_modules
rm -rf .parcel-cache
rm -rf build
rm -rf dist

# Reinstall dependencies
npm install

# Rebuild
npm run dev
```

### Option 3: Use Fix Script
```bash
cd extension
./fix-build.sh
npm run dev
```

## Why This Happens

Plasmo uses Parcel bundler which:
1. Creates module hashes for caching
2. Can corrupt cache if interrupted during build
3. Needs cache cleared when dependencies change

## Prevention

- Always stop dev server cleanly (Ctrl+C)
- Clear cache after updating dependencies
- Don't interrupt builds mid-process

## Verification

After rebuild, check:
1. ✅ Extension loads without module errors
2. ✅ Console shows no "Cannot find module" errors
3. ✅ Supabase client initializes correctly

---

**Status:** Cache corruption fix

