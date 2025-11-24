# Module Resolution Error Fix - Complete Guide

## Error
```
Uncaught Error: Cannot find module 'c81b3d5d6f6cb4e4'
```

## Root Cause
Plasmo/Parcel bundler cache corruption. The hash-like module ID (`c81b3d5d6f6cb4e4`) indicates the bundler's internal module map is corrupted.

## ✅ Caches Cleared
I've already cleared all caches for you:
- ✅ `.plasmo` directory removed
- ✅ `node_modules/.cache` removed  
- ✅ `.parcel-cache` removed
- ✅ `build` directory removed
- ✅ `dist` directory removed

## 🔄 Next Steps - Rebuild

### Step 1: Ensure Dev Server is Stopped
```bash
# Check if plasmo is running
ps aux | grep "plasmo dev"

# If running, stop it (Ctrl+C in terminal or):
pkill -f "plasmo dev"
```

### Step 2: Rebuild Extension
```bash
cd extension
npm run dev
```

### Step 3: Reload Extension in Chrome
1. Go to `chrome://extensions/`
2. Find "Luminate AI" extension
3. Click **Reload** button (circular arrow icon)
4. Or remove and re-add the extension

## 🔍 If Error Persists

### Option 1: Nuclear Clean (Recommended)
```bash
cd extension

# Stop dev server
pkill -f "plasmo dev"

# Remove everything
rm -rf .plasmo
rm -rf node_modules/.cache
rm -rf .parcel-cache
rm -rf build
rm -rf dist
rm -rf node_modules

# Reinstall dependencies
npm install

# Rebuild
npm run dev
```

### Option 2: Use Clean Script
```bash
cd extension
./clean-rebuild.sh
npm run dev
```

## 🐛 Why This Happens

Plasmo uses Parcel bundler which:
1. Creates module hashes for caching (`c81b3d5d6f6cb4e4`)
2. Stores module mappings in cache
3. If cache corrupts, module lookups fail
4. Common causes:
   - Interrupted builds
   - File system issues
   - Dependency changes
   - Hot Module Replacement (HMR) errors

## ✅ Verification

After rebuild, check:
1. ✅ Extension loads without module errors
2. ✅ Console shows no "Cannot find module" errors
3. ✅ Supabase client initializes
4. ✅ Login form displays

## 📝 Prevention

- Always stop dev server cleanly (Ctrl+C)
- Clear cache after dependency updates
- Don't interrupt builds mid-process
- Use `./clean-rebuild.sh` script when issues occur

---

**Status:** Caches cleared, ready for rebuild  
**Next:** Run `npm run dev` in extension directory

