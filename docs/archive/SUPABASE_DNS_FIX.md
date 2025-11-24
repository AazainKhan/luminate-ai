# Supabase DNS Resolution Error Fix

## Error
```
ERR_NAME_NOT_RESOLVED
Could not resolve host: jedqonaiqpnqollmylkk.supabase.com
```

## Root Cause
The Supabase project URL cannot be resolved. This means either:
1. The Supabase project doesn't exist
2. The project URL is incorrect
3. The project was deleted or paused

## Solution

### Step 1: Verify Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Check if your project exists
3. If project doesn't exist, create a new one
4. Copy the correct project URL

### Step 2: Update .env.local

Update `extension/.env.local` with the correct Supabase URL:

```bash
cd extension

# Edit .env.local
# Replace with your actual Supabase project URL
PLASMO_PUBLIC_SUPABASE_URL=https://[your-project-ref].supabase.co
PLASMO_PUBLIC_SUPABASE_ANON_KEY=[your-anon-key]
PLASMO_PUBLIC_API_URL=http://localhost:8000
```

**Note:** Supabase URLs should end with `.supabase.co` (not `.supabase.com`)

### Step 3: Get Correct Credentials

In Supabase Dashboard:
1. Go to **Settings** → **API**
2. Copy:
   - **Project URL** (should be `https://[ref].supabase.co`)
   - **anon/public key** (under "Project API keys")

### Step 4: Rebuild Extension

```bash
cd extension

# Clear cache
rm -rf .plasmo

# Rebuild
npm run dev
```

## Verify Supabase URL Format

Correct format:
```
https://[project-ref].supabase.co
```

Examples:
- ✅ `https://abcdefghijklmnop.supabase.co`
- ❌ `https://jedqonaiqpnqollmylkk.supabase.com` (wrong domain)

## Test Supabase Connection

After updating, test the connection:

```bash
# Test if Supabase URL resolves
curl -I https://[your-project-ref].supabase.co/auth/v1/health

# Should return HTTP 200 OK
```

## Common Issues

### Issue: Project doesn't exist
**Solution:** Create a new Supabase project and use its URL

### Issue: Wrong domain (.com vs .co)
**Solution:** Supabase uses `.supabase.co` not `.supabase.com`

### Issue: Project paused
**Solution:** Reactivate project in Supabase dashboard

---

**Next Steps:**
1. Verify Supabase project exists
2. Update `.env.local` with correct URL
3. Rebuild extension
4. Test authentication

