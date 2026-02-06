# Gmail OAuth 2.0 Email Integration

## Overview

Super Manager AI now includes a **production-grade Gmail OAuth 2.0 email plugin** that provides secure, reliable email sending capabilities.

## Features

### 🔐 Security
- **OAuth 2.0 Authentication** - More secure than app passwords
- **Automatic Token Refresh** - Never expires unexpectedly
- **No hardcoded credentials** - All secrets via environment variables

### 🚀 Reliability
- **Multi-strategy fallback**: OAuth → SMTP → Simulation
- **Retry logic with exponential backoff** (up to 3 retries)
- **Rate limiting** to prevent account suspension (20/min, 500/day)

### 📧 Beautiful Emails
- **Professional HTML templates** with gradient headers
- **Mobile-responsive design**
- **Plain text fallbacks** for all emails
- **Meeting link buttons** with styled CTAs

### 📊 Monitoring
- **Health check endpoint** (`action: health`)
- **Sent email history** tracking
- **Detailed logging** and error reporting

---

## Quick Setup

### 1. Set Up Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Application type: **Desktop app**
6. Copy the **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# Gmail OAuth Configuration
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_USER=your_email@gmail.com
GMAIL_REFRESH_TOKEN=  # Will be filled in step 3
```

### 3. Get Refresh Token

Run the setup script:

```bash
python scripts/get_gmail_refresh_token.py
```

This will:
1. Open a browser for Google authorization
2. Ask you to sign in with your Gmail account
3. Display the refresh token to copy

Add the refresh token to your `.env`:

```env
GMAIL_REFRESH_TOKEN=your_refresh_token_here
```

### 4. Test the Integration

```bash
python tests/test_gmail_oauth.py
```

You should see:
```
🎯 Results: 4/4 tests passed
🎉 All tests passed! Email plugin is ready.
```

---

## API Usage

### Send Email

```python
from backend.core.gmail_oauth_plugin import GmailOAuthPlugin

plugin = GmailOAuthPlugin()

result = await plugin.execute({
    "action": "send_email",
    "parameters": {
        "to": "recipient@example.com",
        "subject": "Meeting Invitation",
        "topic": "Project Kickoff",
        "participants": "John, Jane, Bob",
        "meeting_link": "https://meet.jit.si/my-meeting",
        "message": "Custom message here"  # Optional
    }
}, {})
```

### Check Health

```python
result = await plugin.execute({"action": "health"}, {})
print(result)
# {
#     "status": "completed",
#     "result": "Email service is healthy",
#     "health": {
#         "oauth_configured": true,
#         "oauth_credentials_valid": true,
#         "smtp_configured": false,
#         ...
#     }
# }
```

### List Sent Emails

```python
result = await plugin.execute({"action": "read"}, {})
print(result['emails'])
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GMAIL_CLIENT_ID` | Yes | OAuth Client ID from Google Cloud |
| `GMAIL_CLIENT_SECRET` | Yes | OAuth Client Secret |
| `GMAIL_REFRESH_TOKEN` | Yes | Refresh token from setup script |
| `GMAIL_USER` | Yes | Your Gmail address |
| `SMTP_PASSWORD` | No | Fallback: Gmail App Password |
| `EMAIL_RATE_LIMIT_MINUTE` | No | Max emails/minute (default: 20) |
| `EMAIL_RATE_LIMIT_DAY` | No | Max emails/day (default: 500) |

---

## Fallback Behavior

The plugin tries sending emails in this order:

1. **Gmail OAuth API** - Primary method, most reliable
2. **SMTP with App Password** - If OAuth fails
3. **Simulation** - If both fail, logs the email for debugging

This ensures the application never crashes due to email issues while allowing proper testing.

---

## Security Notes

⚠️ **Important Security Practices**:

1. **Never commit** `.env` files with real credentials
2. **Keep refresh tokens secret** - they grant access to send emails
3. **Use environment variables** in production (not hardcoded values)
4. **Rotate tokens** if you suspect compromise

The refresh token:
- Allows sending emails as your Gmail account
- Does NOT allow reading emails (we only request `gmail.send` scope)
- Can be revoked at [Google Account Permissions](https://myaccount.google.com/permissions)

---

## Troubleshooting

### "OAuth not configured"
- Ensure `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `GMAIL_REFRESH_TOKEN` are set
- Run `python scripts/get_gmail_refresh_token.py` to get a new token

### "Invalid grant" error
- The refresh token may have expired
- Revoke access at [Google Permissions](https://myaccount.google.com/permissions)
- Run the setup script again

### "Rate limit exceeded"
- Wait a few minutes before sending more emails
- Adjust `EMAIL_RATE_LIMIT_MINUTE` if needed

### "SMTP authentication failed"
- Check `SMTP_PASSWORD` is a valid Gmail App Password
- Enable 2FA on your Google account to use App Passwords

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   GmailOAuthPlugin                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ OAuth 2.0    │→ │ SMTP         │→ │ Simulation   │      │
│  │ Gmail API    │  │ Fallback     │  │ Fallback     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Rate         │  │ Retry Logic  │  │ Email        │      │
│  │ Limiter      │  │ (Exp Backoff)│  │ Templates    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Added

- `backend/core/gmail_oauth_plugin.py` - Main plugin implementation
- `scripts/get_gmail_refresh_token.py` - OAuth token setup script
- `tests/test_gmail_oauth.py` - Comprehensive test suite
- Updated `requirements.txt` with Google API dependencies
- Updated `.env.example` with configuration template

---

## Credits

Built with ❤️ for Super Manager AI
