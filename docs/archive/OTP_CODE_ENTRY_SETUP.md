# 6-Digit Code Entry Authentication - Setup Guide

## ✅ Solution Implemented

Switched from magic link redirects to **6-digit code entry** - much better for Chrome extensions!

## How It Works

1. **User enters email** → Extension sends OTP request
2. **User receives email** → Gets 6-digit code (e.g., `123456`)
3. **User enters code** → Extension verifies with Supabase
4. **User logged in** → Session created automatically

## Benefits

- ✅ No redirect URL issues
- ✅ No CSP violations
- ✅ No code exchange complexity
- ✅ Works perfectly in Chrome extensions
- ✅ Better UX - user stays in extension

## Supabase Email Template Configuration

**IMPORTANT:** You need to update the Magic Link email template to show the code instead of a link.

### Step 1: Go to Supabase Dashboard

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Authentication** → **Email Templates**
4. Click on **Magic Link** template

### Step 2: Update Template

Replace the template content with:

```html
<h2>Your Verification Code</h2>

<p>Your one-time login code is:</p>

<h1 style="font-size: 32px; letter-spacing: 8px; text-align: center; margin: 20px 0;">
  {{ .Token }}
</h1>

<p>Enter this code in the extension to sign in.</p>

<p style="color: #666; font-size: 12px;">
  This code expires in 1 hour. If you didn't request this code, you can safely ignore this email.
</p>
```

**Key change:** Use `{{ .Token }}` instead of `{{ .ConfirmationURL }}`

### Step 3: Save Template

Click **Save** in the Supabase dashboard.

## Testing

1. **Rebuild extension**:
   ```bash
   cd extension
   npm run dev
   ```

2. **Reload extension** in Chrome

3. **Enter email** and click "Send Verification Code"

4. **Check email** - should see 6-digit code

5. **Enter code** in extension

6. **Should be logged in** automatically!

## Code Features

- ✅ Two-step flow (email → code)
- ✅ Auto-focus on code input
- ✅ Numeric keyboard on mobile
- ✅ 6-digit validation
- ✅ Clear error messages
- ✅ "Use different email" option

## Troubleshooting

### Code not received
- Check spam folder
- Verify email template is saved
- Check Supabase email logs

### "Invalid code" error
- Code expires in 1 hour
- Request a new code
- Make sure you're entering all 6 digits

### Still seeing magic link emails
- Verify email template is updated
- Clear browser cache
- Request new code

---

**Status:** ✅ Code entry flow implemented  
**Next:** Update Supabase email template → Test!

