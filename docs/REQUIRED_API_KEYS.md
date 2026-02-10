# Required API Keys Configuration

For Super Manager to work with REAL functionality, you need to configure these environment variables:

## Core AI (Required - at least one)
```bash
GROQ_API_KEY=gsk_xxx            # Free tier: https://console.groq.com
OPENAI_API_KEY=sk-xxx           # OpenAI API: https://platform.openai.com
```

## Image Generation (Required for logo/image creation)
```bash
TOGETHER_API_KEY=xxx            # Free tier: https://api.together.xyz (uses FLUX model)
# OR
STABILITY_API_KEY=xxx           # Stability AI: https://stability.ai
# OR 
REPLICATE_API_KEY=xxx           # Replicate: https://replicate.com
```

## Email Sending
```bash
SENDGRID_API_KEY=xxx            # SendGrid: https://sendgrid.com (free tier: 100 emails/day)
# OR
SMTP_EMAIL=xxx@gmail.com        # Gmail SMTP
SMTP_PASSWORD=xxx               # App password (not regular password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Payments
```bash
RAZORPAY_KEY_ID=xxx             # Razorpay: https://razorpay.com
RAZORPAY_KEY_SECRET=xxx
# OR
STRIPE_SECRET_KEY=xxx           # Stripe: https://stripe.com
```

## Calendar/Meetings
```bash
ZOOM_API_KEY=xxx                # Zoom: https://marketplace.zoom.us
ZOOM_API_SECRET=xxx
GOOGLE_CLIENT_ID=xxx            # Google Calendar
GOOGLE_CLIENT_SECRET=xxx
```

## Database
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

---

## Quick Start (Minimal Setup)

For basic functionality, you need:
1. **GROQ_API_KEY** - For AI chat (free)
2. **TOGETHER_API_KEY** - For image generation (free tier)

Everything else will show helpful fallbacks/instructions when API keys aren't configured.

---

## How to Set in Render

1. Go to your Render dashboard
2. Select your service
3. Click "Environment"
4. Add each key-value pair
5. Click "Save Changes" (auto-redeploys)

## How to Set Locally

Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
# ... etc
```
