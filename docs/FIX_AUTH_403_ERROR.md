# Fix: "Token has expired or is invalid" 403 Error

## The Problem
Users get a **403 error** when entering OTP codes with message: "Token has expired or is invalid"

Console shows:
```
jedqonaiqpnqollmylkk.supabase.co/auth/v1/verify:1  Failed to load resource: the server responded with a status of 403 ()
```

## Root Cause

**Email confirmations are DISABLED** in your Supabase settings. When disabled:
- `signInWithOtp()` sends **magic links** (not OTP codes)
- Your frontend tries to verify with `verifyOtp()` using a 6-digit code
- Supabase expects a magic link click, not a code entry
- Result: **403 Forbidden**

This affects both new AND existing users.

## The Fix (2 Steps)

### Step 1: Enable Email Confirmations ⚠️ CRITICAL

1. Go to: https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/auth/providers
2. Click "Email" provider
3. **Turn ON "Confirm email"** toggle
4. Save changes

**Without this, OTP codes will NEVER work!**

### Step 2: Update Email Template

1. Go to: https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/auth/templates
2. Select "Magic Link" template
3. Replace content with:

```html
<h2>Your Login Code</h2>

<p>Please enter this 6-digit code to sign in:</p>

<h1 style="font-size: 32px; font-weight: bold; text-align: center; margin: 20px 0;">
  {{ .Token }}
</h1>

<p>This code will expire in 60 seconds.</p>

<p>If you didn't request this code, you can safely ignore this email.</p>
```

4. Save

## Why This Happens

From Supabase documentation:
> "When email confirmations are disabled, signInWithOtp sends a magic link regardless of the template content."

Your code is correct - Supabase settings were misconfigured.

## Testing

After making both changes:

1. Try logging in with: `student@my.centennialcollege.ca`
2. You should receive a **6-digit code** in email
3. Enter the code in the extension
4. Login should succeed ✅

## Verification Checklist

- [ ] Email confirmations are **enabled** in Supabase
- [ ] Magic Link template shows `{{ .Token }}` (not `{{ .ConfirmationURL }}`)
- [ ] Tested with a new login attempt
- [ ] Received 6-digit code (not clickable link)
- [ ] Code verification works without 403 error

## If Still Not Working

1. **Wait 5-10 minutes** for Supabase to update email templates
2. **Try a different email** to bypass any caching
3. **Check rate limits**: Only 1 OTP per 60 seconds per email
4. **Verify SMTP is configured** in Auth → Email Auth settings

## Summary

**Problem**: Email confirmations disabled → magic links sent → OTP verification fails
**Solution**: Enable confirmations + update template → OTP codes sent → verification works

Both changes are required. Email confirmations must be enabled first!
