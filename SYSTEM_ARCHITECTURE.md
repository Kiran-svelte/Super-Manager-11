# Super Manager - True AI Agent Architecture

## Vision
A personal AI agent that **becomes an expert** in whatever domain you need, takes **autonomous action**, and **remembers everything** about you.

Not a chatbot. Not a command executor. A **digital human** that works for you.

---

## Core Principles

### 1. Expert Personas
When you say "book me a dress", the AI doesn't just search Amazon. It becomes your **personal fashion designer**:
- Knows your style preferences (stored in Supabase)
- Considers the occasion, weather, your body type
- Makes recommendations like a human stylist would
- Handles the purchase autonomously

When you say "schedule meeting with Kiran", it becomes your **executive assistant**:
- Checks your calendar for conflicts
- Finds Kiran's contact info from your database
- Picks the best meeting time
- Sends invites via email/telegram/sms
- Sets reminders 15 min before
- Follows up if Kiran hasn't responded

### 2. Autonomous Execution
The AI should **do things**, not just talk about them:
- ❌ "I can help you schedule a meeting. What time?"
- ✅ "I've scheduled you with Kiran tomorrow at 3pm. Sent invite to his email and Telegram. I'll remind you 15 minutes before."

### 3. Multi-Modal Memory
- **Short-term**: Current conversation context
- **Long-term**: User preferences, contact book, past interactions
- **Domain**: Fashion preferences, meeting patterns, travel habits

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React Chat UI → WebSocket/REST → FastAPI Backend            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     AI ORCHESTRATOR                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Intent    │→ │   Expert    │→ │  Action             │  │
│  │  Detector   │  │  Selector   │  │  Executor           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │               │                    │               │
│         ▼               ▼                    ▼               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              MULTI-MODEL AI ENGINE                       ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        ││
│  │  │  Groq   │ │ OpenAI  │ │ Claude  │ │ Gemini  │        ││
│  │  │ LLaMA3  │ │ GPT-4   │ │ 3.5     │ │ Pro     │        ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PLUGIN SYSTEM                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Gmail   │ │ Calendar │ │   Zoom   │ │ Telegram │       │
│  │  Plugin  │ │  Plugin  │ │  Plugin  │ │  Plugin  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Twilio  │ │ Shopping │ │ Payments │ │  Search  │       │
│  │ SMS/Call │ │  Plugin  │ │ UPI/Card │ │  Plugin  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      SUPABASE                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Users   │ │ Contacts │ │ Meetings │ │  Prefs   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Messages │ │  Tasks   │ │  Memory  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Expert Personas

### 1. Executive Assistant (Meetings)
**Triggers**: "schedule meeting", "call with", "meet", "sync up"
**Capabilities**:
- Check calendar availability
- Find contact info from user's contact book
- Schedule at optimal time
- Create Zoom/Meet links
- Send invites via email + telegram + SMS
- Set reminders
- Follow up on pending responses

### 2. Fashion Designer (Shopping/Clothing)
**Triggers**: "buy dress", "outfit for", "what to wear"
**Capabilities**:
- Access user's style profile (colors, sizes, brands)
- Consider occasion, weather, budget
- Search across stores (Myntra, Amazon, Ajio)
- Make curated recommendations
- Handle purchases with saved payment methods

### 3. Travel Agent
**Triggers**: "book flight", "plan trip", "travel to"
**Capabilities**:
- Know travel preferences (window seat, veg food)
- Search flights, hotels, cabs
- Optimize for price/convenience
- Handle bookings
- Create complete itinerary

### 4. Personal Secretary
**Triggers**: "remind me", "don't forget", "follow up"
**Capabilities**:
- Set smart reminders (context-aware timing)
- Send reminders via preferred channel
- Track pending items
- Auto-follow up

### 5. Research Assistant
**Triggers**: "find out", "search", "what is", "how to"
**Capabilities**:
- Deep web search
- Summarize findings
- Cite sources
- Follow-up questions

---

## Database Schema (Supabase)

### users
```sql
id UUID PRIMARY KEY
email TEXT UNIQUE
phone TEXT
telegram_id TEXT
name TEXT
created_at TIMESTAMP
```

### contacts
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id)
name TEXT
email TEXT
phone TEXT
telegram_id TEXT
relationship TEXT (colleague, friend, family)
notes TEXT
```

### preferences
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id)
category TEXT (fashion, travel, meetings, food)
key TEXT
value JSONB
```

### conversations
```sql
id UUID PRIMARY KEY
user_id UUID
session_id TEXT
created_at TIMESTAMP
summary TEXT
```

### messages
```sql
id UUID PRIMARY KEY
conversation_id UUID REFERENCES conversations(id)
role TEXT (user, assistant, system)
content TEXT
metadata JSONB
created_at TIMESTAMP
```

### tasks
```sql
id UUID PRIMARY KEY
user_id UUID
type TEXT
status TEXT (pending, in_progress, completed, failed)
details JSONB
result JSONB
created_at TIMESTAMP
completed_at TIMESTAMP
```

### meetings
```sql
id UUID PRIMARY KEY
user_id UUID
title TEXT
scheduled_at TIMESTAMP
participants JSONB[]
platform TEXT (zoom, meet, jitsi)
meeting_link TEXT
status TEXT (scheduled, in_progress, completed, cancelled)
reminders_sent BOOLEAN DEFAULT FALSE
```

### reminders
```sql
id UUID PRIMARY KEY
user_id UUID
task_id UUID
trigger_at TIMESTAMP
channel TEXT (email, telegram, sms)
message TEXT
sent BOOLEAN DEFAULT FALSE
```

---

## API Design

### POST /api/chat
Main endpoint. Handles everything.
```json
{
  "message": "Schedule a meeting with Kiran tomorrow",
  "user_id": "uuid",
  "session_id": "optional"
}
```

Response:
```json
{
  "response": "Done! I've scheduled you with Kiran tomorrow at 3pm...",
  "actions_taken": [
    {"type": "calendar_create", "details": {...}},
    {"type": "email_send", "details": {...}},
    {"type": "telegram_send", "details": {...}},
    {"type": "reminder_set", "details": {...}}
  ],
  "session_id": "xxx"
}
```

### GET /api/user/{user_id}/meetings
Get user's scheduled meetings

### GET /api/user/{user_id}/contacts
Get user's contact book

### POST /api/user/{user_id}/preferences
Update preferences

---

## Implementation Order

1. **Database Setup** - Supabase tables, RLS policies
2. **Core Agent** - Multi-model AI with tool calling
3. **Plugin System** - Clean interface for integrations
4. **Gmail Plugin** - OAuth, send emails, read inbox
5. **Calendar Plugin** - Create events, check availability
6. **Zoom Plugin** - Create meetings, get links
7. **Telegram Plugin** - Send messages via bot
8. **Twilio Plugin** - SMS and voice calls
9. **Expert Personas** - Domain-specific prompts and logic
10. **Frontend Updates** - Show actions taken, not just text

---

## Required Credentials

### Gmail/Calendar (Google Cloud Console)
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REFRESH_TOKEN

### Zoom (Zoom Marketplace)
- ZOOM_CLIENT_ID
- ZOOM_CLIENT_SECRET
- ZOOM_ACCOUNT_ID

### Telegram (BotFather)
- TELEGRAM_BOT_TOKEN

### Twilio
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

### Supabase
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_KEY

### AI Models
- GROQ_API_KEY
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_AI_KEY
