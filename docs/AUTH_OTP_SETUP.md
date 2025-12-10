# Authentication OTP Setup Fix

## Problem
Users receive "Token has expired or is invalid" error with 403 status when trying to log in.

## Root Cause
There are TWO issues causing this problem:

### Issue 1: Email Confirmations are Disabled
When email confirmations are **disabled** in Supabase settings, `signInWithOtp()` sends **magic links** instead of OTP codes - even if you update the email template. This is by design.

### Issue 2: Email Template Uses Magic Link Format
By default, `signInWithOtp()` sends **magic links** instead of OTP codes. According to Supabase documentation:

> "Though the method is labelled 'OTP', it sends a Magic Link by default. The two methods differ only in the content of the confirmation email sent to the user."

## Solution

### Step 1: Enable Email Confirmations (CRITICAL)

**You MUST enable email confirmations for OTP codes to work.**

1. **Go to:** https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/auth/providers
2. **Click on "Email" provider**
3. **Enable "Confirm email"** toggle
4. **Save changes**

⚠️ **Important:** Without this, Supabase will send magic links regardless of your email template.

### Step 2: Update Email Template in Supabase Dashboard

You need to modify the **Magic Link** email template to send OTP codes instead of magic links.

#### Steps:

1. **Go to Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard/project/jedqonaiqpnqollmylkk/auth/templates

2. **Edit Magic Link Template**
   - Click on "Authentication" → "Email Templates"
   - Select the **"Magic Link"** template
   - **Replace the template content** with:

```html
<h2>Your Login Code</h2>

<p>Please enter this 6-digit code to sign in:</p>

<h1 style="font-size: 32px; font-weight: bold; text-align: center; margin: 20px 0;">
  {{ .Token }}
</h1>

<p>This code will expire in 60 seconds.</p>

<p>If you didn't request this code, you can safely ignore this email.</p>
```

3. **Update Confirm Signup Template (Optional but Recommended)**
   - Select the **"Confirm signup"** template
   - Replace with the same OTP-based template above
   - This ensures both new and existing users get OTP codes

4. **Save Changes**

### Alternative: Custom Template with Branding

For a more professional look:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
    <h1 style="color: white; margin: 0; font-size: 28px;">Luminate AI</h1>
    <p style="color: white; margin: 10px 0 0 0; font-size: 14px;">Your AI Tutor Companion</p>
  </div>

  <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
    <h2 style="color: #333; margin-top: 0;">Your Login Code</h2>
    
    <p>Welcome! Please enter this 6-digit code to sign in to your account:</p>
    
    <div style="background: white; border: 2px solid #667eea; border-radius: 10px; padding: 20px; text-align: center; margin: 30px 0;">
      <div style="font-size: 40px; font-weight: bold; letter-spacing: 8px; color: #667eea; font-family: 'Courier New', monospace;">
        {{ .Token }}
      </div>
    </div>
    
    <p style="color: #666; font-size: 14px; margin: 20px 0;">
      <strong>⏱️ This code will expire in 60 seconds</strong>
    </p>
    
    <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
      If you didn't request this code, you can safely ignore this email. Someone may have entered your email address by mistake.
    </p>
  </div>
  
</body>
</html>
```

### Verify Frontend is Configured Correctly

Your frontend code is already correct (in `extension/src/components/auth/LoginForm.tsx`):

```typescript
// ✅ Correct - Doesn't set emailRedirectTo
const { error: signInError } = await supabase.auth.signInWithOtp({
  email,
  options: {
    shouldCreateUser: true,
    data: {
      full_name: fullName,
    },
    // ✅ No emailRedirectTo - this is correct for OTP flow
  },
})
```

### Testing

After updating the email template:

1. **Test with a new email:**
   ```bash
   # Use your Centennial email
   student@my.centennialcollege.ca
   ```

2. **Check your email:**
   - You should receive a 6-digit code (e.g., `123456`)
   - NOT a clickable link

3. **Enter the code:**
   - The code entry form should accept the 6-digit code
   - User should be successfully logged in

### Troubleshooting

If you still receive magic links or 403 errors:

1. **Verify email confirmations are enabled:**
   - Go to: Authentication → Providers → Email
   - **"Confirm email" toggle MUST be ON**
   - This is the #1 cause of OTP not working

2. **Check existing users:**
   - Existing users with `email_confirmed_at` already set will work fine
   - New users will need to verify their email with OTP code
   - Both scenarios now use OTP codes (not magic links)

3. **Clear email template cache:**
   - Sometimes Supabase caches the old template
   - Wait 5-10 minutes after saving changes
   - Test with a different email address

4. **Check SMTP settings:**
   - Go to: Authentication → Email Auth → Settings
   - Ensure "Enable email confirmations" is checked
   - Verify OTP expiration is set (default: 60 seconds)

5. **Verify rate limits:**
   - Default: 1 OTP every 60 seconds per email
   - Found in: Authentication → Rate Limits

### Additional Configuration (Optional)

You can also configure OTP settings:

```bash
# Via Supabase CLI (if self-hosted or local dev)
# In config.toml:
[auth.email]
enable_confirmations = true
enable_signup = true

[auth.external.email]
enabled = true

# OTP expiry in seconds (default: 60)
[auth.email]
otp_expiry = 60
```

### Backend Verification

The backend doesn't need changes - it's already set up correctly for OTP verification in `useAuth.ts` and `LoginForm.tsx`.

## Summary

**Key Change:** Update the Magic Link email template to include `{{ .Token }}` instead of `{{ .ConfirmationURL }}`.

This ensures:
- ✅ Users receive a 6-digit OTP code
- ✅ No invalid magic links are sent
- ✅ Works for both new and existing users
- ✅ Frontend code already handles OTP verification correctly

## References

- [Supabase Email OTP Documentation](https://supabase.com/docs/guides/auth/auth-email-passwordless#with-otp)
- [Email Templates Guide](https://supabase.com/docs/guides/auth/auth-email-templates)
