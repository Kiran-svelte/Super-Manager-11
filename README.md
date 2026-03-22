# 🚀 SUPER MANAGER - Enterprise Autonomous AI Agent Platform

<div align="center">

![Version](https://img.shields.io/badge/Version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

**The AI that DOES, not just TELLS.**

*Transform any user intent into executed actions through autonomous intelligent agents.*

</div>

---

## 📋 Table of Contents

1. [Vision & Philosophy](#vision--philosophy)
2. [What Makes Super Manager Different](#what-makes-super-manager-different)
3. [Product Layers](#product-layers)
4. [Complete Processing Pipeline](#complete-processing-pipeline)
5. [Integration Manager](#-integration-manager)
6. [Architecture Overview](#architecture-overview)
7. [Real Task Flows](#-real-task-flows)
8. [User Flow & Journey](#user-flow--journey)
9. [UI & Access Points](#-ui--access-points)
10. [Workflow & State Machine](#workflow--state-machine)
11. [Backend Architecture](#backend-architecture)
12. [AI Architecture & Flow](#ai-architecture--flow)
13. [Security Framework](#security-framework)
14. [Hard Decisions](#1️⃣-hard-decisions)
15. [What Is Forbidden](#2️⃣-what-is-forbidden)
16. [State Machine Rules](#3️⃣-state-machine-rules)
17. [Data Ownership Rules](#4️⃣-data-ownership-rules)
18. [Infrastructure Contract](#5️⃣-infrastructure-contract)
19. [Development Lifecycle](#development-lifecycle)
20. [API Reference](#api-reference)
21. [Database Schema](#database-schema)
22. [Deployment](#deployment)
23. [Enterprise Features](#enterprise-features)
24. [Authentication & Authorization Flow](#authentication--authorization-flow)
25. [Predictive Intelligence](#predictive-intelligence-user-learning)
26. [Complete Data Flow](#complete-data-flow)

---

## Vision & Philosophy

### The Problem with Current AI Assistants

```
User: "Book me a flight to Delhi tomorrow"

ChatGPT/Claude/Gemini: "Here are some steps you can follow:
  1. Go to booking.com
  2. Enter your destination...
  3. Select dates..."

Super Manager: ✅ Searches flights → ✅ Shows options → ✅ Books ticket → ✅ Sends confirmation
```

**Super Manager is not another chatbot.** It's an autonomous AI agent that:
- **EXECUTES** tasks instead of giving instructions
- **LEARNS** your preferences and predicts your needs
- **CONNECTS** to services dynamically via secure Integration Manager
- **CONFIRMS** before taking sensitive actions
- **ADAPTS** to your emotional state and communication style
- **FALLS BACK** intelligently when APIs are unavailable

---

## What Makes Super Manager Different

| Feature | Traditional AI | Super Manager |
|---------|---------------|---------------|
| Task Execution | ❌ Instructions only | ✅ Actually performs tasks |
| Service Access | ❌ Requires user setup | ✅ Dynamic Integration Manager |
| Credential Management | ❌ Manual configuration | ✅ OAuth + encrypted token vault |
| User Learning | ❌ Stateless | ✅ Learns preferences over time |
| Prediction | ❌ None | ✅ Predicts next needs |
| Fallback Strategy | ❌ Fails silently | ✅ API → Browser → User Input |
| Confirmation | ❌ N/A | ✅ Always confirms sensitive actions |
| Progress Tracking | ❌ None | ✅ Real-time deep task visibility |
| Integration Control | ❌ Connect everything upfront | ✅ Ask only when needed |

---

## Product Layers

> Like a great hotel doesn't just serve food — it provides seating, AC, menus, tissues, and jeera water —
> **a great product provides layers of value beyond its core function.**

Super Manager is designed using a **6-Layer Product Framework**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCT LAYER MODEL                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  Layer 6: TRUST         │ Audit logs, encryption, RBAC, compliance, privacy
  ───────────────────────┼───────────────────────────────────────────────────
  Layer 5: DELIGHT       │ AI assistant, smart suggestions, predictive
                         │ intelligence, beautiful UI, micro-animations
  ───────────────────────┼───────────────────────────────────────────────────
  Layer 4: COMFORT       │ Notifications, search, filters, analytics,
                         │ integrations, automation
  ───────────────────────┼───────────────────────────────────────────────────
  Layer 3: USABILITY     │ Dashboards, UI/UX, help messages, onboarding,
                         │ documentation, interactive chat
  ───────────────────────┼───────────────────────────────────────────────────
  Layer 2: INFRASTRUCTURE│ Auth, security, database, performance, backups,
                         │ monitoring, real-time sync
  ───────────────────────┼───────────────────────────────────────────────────
  Layer 1: CORE          │ Understand intent → Plan → Execute → Confirm
                         │ (If this fails, product fails)
```

### Layer-by-Layer Breakdown

| Layer | What It Is | Super Manager Features | Hotel Analogy |
|-------|-----------|----------------------|---------------|
| **1. Core** | The main thing your product does | Intent classification, task planning, autonomous execution, confirmation flow | Serving food |
| **2. Infrastructure** | What must exist for it to work | Supabase auth, AES-256 encryption, PostgreSQL, rate limiting, circuit breakers, WebSocket/SSE | Tables, chairs, AC |
| **3. Usability** | What helps users understand & use it | Chat UI, onboarding wizard, task panel, progress tracking, interactive components | Menu card |
| **4. Comfort** | Not critical but improves experience | Notifications, search, integrations, browser automation, scheduling, email | Tissue paper |
| **5. Delight** | Makes it feel premium | AI memory/predictions, micro-animations, smart suggestions, beautiful glassmorphism UI | Jeera water |
| **6. Trust** | What enterprises require | Audit logs, role permissions, credential encryption, data ownership, sandbox security | Chef certification |

### Design Principle

When building any feature, ask:

```
1. What is the core service?             → AI task execution
2. What must exist for it to work?       → Auth, DB, security, AI providers
3. What makes it easy to use?            → Chat UI, onboarding, task tracking
4. What makes it pleasant?               → Integrations, notifications, automation
5. What makes it trustworthy?            → Encryption, audit logs, confirmation
6. What makes it special?                → Predictive AI, learning, adaptation
```

---

## Complete Processing Pipeline

Super Manager processes every request through a **10-step pipeline**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    10-STEP PROCESSING PIPELINE                               │
└─────────────────────────────────────────────────────────────────────────────┘

User (text / voice / WhatsApp / Telegram)
        │
        ▼
  ┌─────────────────────────────────────┐
  │ 1. INPUT LAYER                      │ ← Receive message from any channel
  │    Web Chat, Telegram, WhatsApp     │ ← Normalize format
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 2. INTENT + CONTEXT ENGINE          │ ← NLU: classify what user wants
  │    Intent classification            │ ← Entity extraction
  │    Memory recall (preferences)      │ ← Context from conversation history
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 3. TASK CLASSIFIER                  │ ← Categorize: shopping, meeting,
  │    Type, complexity, risk level     │   email, search, booking, etc.
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 4. PLANNER                          │ ← Break into multi-step plan
  │    AI-powered step generation       │ ← Dependency ordering
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 5. CAPABILITY ROUTER                │ ← Route to correct execution
  │    API / Tool / Browser / Manual    │   engine based on capabilities
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 6. 🔐 INTEGRATION MANAGER          │ ← Check API availability
  │    (THE BRIDGE LAYER)               │ ← Connect if needed (OAuth)
  │    Credential vault, token refresh  │ ← Validate / refresh tokens
  │    Fallback strategy                │ ← If fails → try browser/manual
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 7. EXECUTION LAYER                  │ ← API calls, browser automation,
  │    API Engine                       │   tool delegation, code execution
  │    Browser Automation Engine        │ ← Sandboxed, timeout-enforced
  │    Tool Delegation Engine           │
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 8. HUMAN-IN-THE-LOOP               │ ← Confirmation for risky actions
  │    Security level classification    │ ← User approves/edits/cancels
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 9. FEEDBACK + MEMORY UPDATE         │ ← Store results, update prefs
  │    Preference confidence update     │ ← Save proof of execution
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │ 10. LEARNING LOOP                   │ ← Cache successful strategies
  │     Adapt for next interaction      │ ← Confidence scoring
  └─────────────────────────────────────┘
```

---

## 🔐 Integration Manager

> **The bridge between AI intelligence and real-world execution.**
> Without it, the assistant stays theoretical. With it, it becomes usable.

The Integration Manager is one of the **most critical layers** in the system. It handles the dynamic connection between Super Manager and external services.

### What It Does

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION MANAGER                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐
  │  1. DETECT NEED     │ ← "Schedule meeting" → needs Calendar API
  │     What API/service│ ← "Send email" → needs Gmail OAuth
  │     is required?    │ ← "Create logo" → needs DALL·E (no OAuth)
  └──────────┬──────────┘
             ▼
  ┌─────────────────────┐
  │  2. CHECK STATUS    │ ← Is this service already connected?
  │     Connected?      │ ← Token valid? Not expired?
  │     Token valid?    │
  └───────┬─────────┬───┘
          │         │
       YES│      NO │
          │         │
          ▼         ▼
  ┌────────────┐ ┌────────────────────────┐
  │ 3a. REUSE  │ │ 3b. CONNECT            │
  │  Silently  │ │  "Connect your calendar │
  │  proceed   │ │   to proceed"           │
  │  (no ask)  │ │  → OAuth login flow     │
  └────────────┘ │  → NOT "paste API key"  │
                 └───────────┬────────────┘
                             ▼
                 ┌────────────────────────┐
                 │ 4. STORE SECURELY      │
                 │  • Token-based (not    │
                 │    raw credentials)    │
                 │  • AES-256 encrypted   │
                 │  • Per-user isolation   │
                 └───────────┬────────────┘
                             ▼
                 ┌────────────────────────┐
                 │ 5. HANDLE FAILURE      │
                 │  • Token expired →     │
                 │    auto-refresh        │
                 │  • Permission revoked →│
                 │    "Reconnect needed"  │
                 │  • Service down →      │
                 │    retry + fallback    │
                 └───────────┬────────────┘
                             ▼
                 ┌────────────────────────┐
                 │ 6. FALLBACK LOGIC      │
                 │  If user refuses or    │
                 │  API unavailable:      │
                 │  → See fallback matrix │
                 └────────────────────────┘
```

### Fallback Matrix

| Situation | Primary | Fallback 1 | Fallback 2 | Last Resort |
|-----------|---------|-----------|-----------|-------------|
| No Calendar API | Google Calendar API | Browser automation (open calendar) | Ask user to do it manually | Provide instructions |
| No Email API | Gmail OAuth | SMTP direct send | Browser automation | Draft for user |
| No Payment API | Razorpay/Stripe API | Generate payment link | Browser checkout | Share payment details |
| Service is down | Primary API | Retry with backoff | Alternative provider | Partial assist + notify |
| User refuses to connect | API route | Browser automation | Ask user for input | Partial task completion |

### Critical Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION RULES (NON-NEGOTIABLE)                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ❌ Rule 1: NEVER over-ask for integrations
     BAD:  "Connect everything before you start"
     GOOD: "Connect your calendar to schedule this meeting"
     → Ask ONLY when a specific task needs it

  ❌ Rule 2: NEVER stop if API is unavailable
     BAD:  "I can't do this without API access"
     GOOD: "Calendar not connected. I'll try browser automation instead."
     → ALWAYS provide a fallback path

  ✅ Rule 3: User controls ALL permissions
     → View connected apps anytime
     → Revoke access with one click
     → See what data each integration accesses

  ✅ Rule 4: Security > Convenience
     → Encrypt all tokens at rest (AES-256-GCM)
     → Never expose raw API keys
     → Auto-refresh tokens silently
     → Auto-revoke on suspicious activity

  ✅ Rule 5: Reuse silently
     → First time: ask user to connect
     → Every time after: use stored token automatically
     → No repeated permission requests
```

### Integration Manager Sub-Components

```
Integration Manager
├── Credential Vault
│   ├── AES-256-GCM encryption
│   ├── Per-user salt (PBKDF2)
│   ├── Token storage (not raw keys)
│   └── Auto-expiry management
│
├── OAuth Connector
│   ├── Google OAuth 2.0 (Calendar, Gmail, Drive)
│   ├── Microsoft OAuth (Outlook, Teams)
│   ├── GitHub OAuth
│   └── Custom OAuth providers
│
├── Token Refresher
│   ├── Auto-refresh before expiry
│   ├── Retry with exponential backoff
│   ├── Alert user if refresh fails
│   └── Graceful degradation
│
└── Fallback Router
    ├── API → Browser Automation → User Input → Partial Assist
    ├── Priority-based routing
    ├── Capability detection
    └── Cost/speed optimization
```

---

## 🔄 Real Task Flows

### 🗓️ Schedule Meeting (with Integration Manager)

```
User: "Schedule a meeting with John tomorrow at 3pm"
         │
         ▼
  1. Intent: schedule_meeting
  2. Needs: Calendar API + Email API
  3. Integration Manager checks:
     ├── Calendar: ❌ Not connected
     │   → "Connect your Google Calendar to schedule meetings"
     │   → User clicks "Connect" → OAuth flow → Token stored
     │
     └── Email: ✅ Already connected (from onboarding)
         → Proceed directly
  4. API used → Meeting created on Google Calendar
  5. Email invite sent to john@example.com
  6. ✅ "Meeting scheduled! Invite sent to John."

  👉 NEXT TIME: No asking. Calendar already connected. Direct execution.
```

### 📧 Send Email (first-time connect)

```
User: "Email the quarterly report to the team"
         │
         ▼
  1. Intent: send_email
  2. Needs: Gmail OAuth
  3. Integration Manager:
     ├── First time? → "Connect your Gmail to send emails"
     │   → OAuth login → Permission granted → Token stored
     └── Already connected? → Proceed silently
  4. Email composed + sent via Gmail API
  5. ✅ "Email sent to 5 team members with quarterly report attached."
```

### 🌐 Register for Event (no API available)

```
User: "Register me for the GameDev Hackathon this weekend"
         │
         ▼
  1. Intent: web_registration
  2. Integration Manager:
     └── No API available for this service
         → Routes to: Browser Automation Engine
  3. Playwright opens registration page
  4. Fills form with user's stored info
  5. ⚠️ Confirmation required before submit
  6. User confirms → Form submitted
  7. ✅ "Registered! Confirmation email incoming."
```

### 🎨 Create Logo (no integration needed)

```
User: "Create a modern logo for my startup 'NexGen AI'"
         │
         ▼
  1. Intent: image_generation
  2. Integration Manager:
     └── No external API needed (uses built-in Pollinations AI)
         → Routes directly to Tool Delegation Engine
  3. Image generated via Pollinations
  4. ✅ "Here's your logo! Want me to try different styles?"
```

---

## 🖥️ UI & Access Points

### How Users Access Everything

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MAIN APPLICATION UI                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          HEADER BAR                                  │    │
│  │  [🚀 Logo]  [🔍 Search]  [🔔 Notifications]  [👤 User Menu]       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌───────────────────────────────────────────────────┐    │
│  │  SIDEBAR     │  │              MAIN CONTENT AREA                    │    │
│  │  (collapsible│  │                                                    │    │
│  │  navigation) │  │  ┌───────────────────────────────────────────┐    │    │
│  │              │  │  │          CHAT INTERFACE                    │    │    │
│  │  💬 Chat     │  │  │                                           │    │    │
│  │  📋 Tasks    │  │  │  [AI Messages + User Messages]            │    │    │
│  │  📜 History  │  │  │  [Interactive Cards / Buttons]            │    │    │
│  │  🧠 Memory   │  │  │  [Confirmation Prompts]                   │    │    │
│  │  🔗 Connect  │  │  │  [Progress Trackers]                      │    │    │
│  │  ⚙️ Settings │  │  │                                           │    │    │
│  │              │  │  │  ┌─────────────────────────────────────┐  │    │    │
│  │              │  │  │  │  [📎 Attach] [Message...] [➤ Send] │  │    │    │
│  │              │  │  │  └─────────────────────────────────────┘  │    │    │
│  │              │  │  └───────────────────────────────────────────┘    │    │
│  │              │  │                                                    │    │
│  │              │  │  ┌───────────────────────────────────────────┐    │    │
│  │              │  │  │      TASK PANEL (slide-in from right)     │    │    │
│  │              │  │  │  Active task progress, substeps, actions  │    │    │
│  │              │  │  └───────────────────────────────────────────┘    │    │
│  └──────────────┘  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔗 Integrations Hub (NEW)

Accessible from sidebar → "Connect":

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INTEGRATIONS HUB                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Connected Services (3)                                                      │
│  ──────────────────────                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ✅ Google Calendar    │ Connected Mar 15 │ [Manage] [Revoke]       │    │
│  │ ✅ Gmail              │ Connected Mar 10 │ [Manage] [Revoke]       │    │
│  │ ✅ Razorpay           │ Connected Mar 12 │ [Manage] [Revoke]       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Available Integrations                                                      │
│  ──────────────────────                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 📅 Google Calendar  │ Schedule meetings, manage events │ [Connect] │    │
│  │ 📧 Gmail / Outlook  │ Send and read emails             │ [Connect] │    │
│  │ 💳 Razorpay/Stripe  │ Create payment links             │ [Connect] │    │
│  │ 📂 Google Drive     │ Access and share files           │ [Connect] │    │
│  │ 💬 Slack            │ Send messages to channels        │ [Connect] │    │
│  │ 🐙 GitHub           │ Manage repos and issues          │ [Connect] │    │
│  │ 📋 Trello/Jira      │ Manage project boards            │ [Connect] │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  🔒 Your tokens are encrypted with AES-256. You can revoke anytime.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Screen Access Map

| Screen | Access Point | What Users See |
|--------|-------------|----------------|
| **Chat** | Sidebar → 💬 Chat | AI conversation, interactive cards, confirmations |
| **Tasks** | Sidebar → 📋 Tasks | Active/completed tasks, progress, substeps |
| **History** | Sidebar → 📜 History | Past conversations, searchable |
| **Memory** | Sidebar → 🧠 Memory | What AI remembers, edit/delete preferences |
| **Integrations** | Sidebar → 🔗 Connect | Connected apps, add/revoke integrations |
| **Settings** | Sidebar → ⚙️ Settings | Profile, AI identity, security, preferences |
| **Notifications** | Header → 🔔 Bell | Task updates, connection alerts, reminders |
| **Search** | Header → 🔍 Search | Search across tasks, conversations, memory |

---

## Complete Feature Matrix

### Core Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| **Natural Language Understanding** | ✅ | Multi-intent classification with entity extraction |
| **Task Planning** | ✅ | AI-powered step-by-step planning |
| **Task Execution** | ✅ | Autonomous action execution |
| **Integration Manager** | ✅ | Dynamic API connectivity with OAuth + fallback |
| **Web Automation** | ✅ | Playwright-based browser automation |
| **Service Signup** | ✅ | AI self-registers for required services |
| **Email Integration** | ✅ | Gmail OAuth + SMTP sending/reading |
| **Meeting Scheduling** | ✅ | Jitsi/Zoom with auto-invites |
| **Payment Links** | ✅ | Razorpay/Stripe integration |
| **Image Generation** | ✅ | Pollinations AI (free) |
| **Web Search** | ✅ | DuckDuckGo scraping |
| **Teaching Mode** | ✅ | Learn workflows from user demonstrations |
| **User Memory** | ✅ | Persistent preferences across sessions |
| **Credential Encryption** | ✅ | AES-256 with PBKDF2 key derivation |
| **Real-time Updates** | ✅ | WebSocket + SSE streaming |
| **Task Tracking** | ✅ | Granular substep progress visibility |

### Communication Channels

| Channel | Status | Notes |
|---------|--------|-------|
| Web Chat | ✅ | Real-time with streaming |
| Telegram | ✅ | Full bot integration |
| WhatsApp | 🔄 | Twilio integration planned |
| Email | ✅ | Send/receive capabilities |
| SMS | 🔄 | Twilio integration planned |
| Voice | 🔄 | Planned |

### AI Providers

| Provider | Status | Model | Notes |
|----------|--------|-------|-------|
| Groq | ✅ | llama-3.3-70b-versatile | Primary (free, fast) |
| OpenAI | ✅ | GPT-4-Turbo | Fallback |
| Anthropic | 🔄 | Claude | Planned |
| Google | ✅ | Gemini | Free tier |
| SambaNova | ✅ | Various | Free tier |
| Ollama | ✅ | Local models | Self-hosted |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   USER LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐ │
│  │  Web Chat   │  │  Telegram   │  │   Mobile    │  │    WhatsApp       │ │
│  │  (React)    │  │    Bot      │  │     App     │  │   (Twilio)        │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼──────────────────┼────────────┘
          │                │                │                  │
          ▼                ▼                ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Application                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│  │  │ Rate Limit  │ │   CORS      │ │  Security   │ │  Request     │  │   │
│  │  │ Middleware  │ │ Middleware  │ │  Headers    │ │  Tracing     │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTELLIGENCE LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                              AI BRAIN                                 │  │
│  │  ┌────────────────┐                                                   │  │
│  │  │ Intent         │    ┌──────────────────────────────────────────┐   │  │
│  │  │ Classifier     ├───►│            Adaptive Agent                │   │  │
│  │  └────────────────┘    │  ┌────────┐ ┌────────┐ ┌──────────────┐ │   │  │
│  │                        │  │ THINK  │►│GENERATE│►│CLASSIFY RISK │ │   │  │
│  │  ┌────────────────┐    │  └────────┘ └────────┘ └──────┬───────┘ │   │  │
│  │  │ Confirmation   │    │                                │        │   │  │
│  │  │ Manager        │◄───│  ┌────────┐ ┌────────┐ ┌──────▼───────┐ │   │  │
│  │  └────────────────┘    │  │ ADAPT  │◄│OBSERVE │◄│  EXECUTE     │ │   │  │
│  │                        │  └────────┘ └────────┘ └──────────────┘ │   │  │
│  │                        └──────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                            TOOL REGISTRY                              │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │  │
│  │  │Primitives│ │  MCP     │ │ Stealth  │ │ Payment  │ │  Taught   │  │  │
│  │  │(6 core)  │ │ Servers  │ │ Browser  │ │  Links   │ │ Workflows │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │     Task       │  │    Substep     │  │  Scheduler   │  │ Detection  │ │
│  │  Orchestrator  │  │    Manager     │  │ (APScheduler)│  │ (Webhooks) │ │
│  └────────────────┘  └────────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🔐 INTEGRATION MANAGER LAYER (NEW)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Credential    │  │     OAuth      │  │    Token     │  │  Fallback  │ │
│  │    Vault       │  │   Connector    │  │  Refresher   │  │   Router   │ │
│  │ (AES-256-GCM)  │  │ (Google/MS/..) │  │ (Auto-renew) │  │(API→Browser│ │
│  │                │  │                │  │              │  │  →Manual)  │ │
│  └────────────────┘  └────────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXECUTION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         SANDBOX EXECUTOR                             │   │
│  │  • Static Risk Analysis (no LLM dependency)                         │   │
│  │  • Forbidden Pattern Detection                                      │   │
│  │  • Timeout Enforcement (30s default)                                │   │
│  │  • Only primitives available inside sandbox                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │    Browser     │  │     Email      │  │   Meeting    │  │  Payment   │ │
│  │  Automation    │  │  (Gmail/SMTP)  │  │ (Jitsi/Zoom) │  │ (Razorpay) │ │
│  │  (Playwright)  │  │               │  │              │  │            │ │
│  └────────────────┘  └────────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              IDENTITY LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      AI IDENTITY MANAGER                             │   │
│  │  • Per-user AI email identity (user's Gmail for AI)                 │   │
│  │  • Service account management (auto-signup for APIs)                │   │
│  │  • Credential encryption (AES-256 + PBKDF2)                        │   │
│  │  • OAuth token management                                           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       Supabase (PostgreSQL)                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│  │  │   users     │ │  contacts   │ │preferences  │ │conversations │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│  │  │  meetings   │ │  reminders  │ │ai_identities│ │ai_service_   │  │   │
│  │  │             │ │             │ │             │ │  accounts    │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │   │
│  │  │orchestrated │ │task_substeps│ │scheduled_   │ │user_         │  │   │
│  │  │  _tasks     │ │             │ │   jobs      │ │integrations  │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌────────────────────────────────────────────┐   │
│  │     Redis (Cache)    │  │           In-Memory Fallback               │   │
│  │  • Session cache     │  │  • Works without external deps            │   │
│  │  • Rate limiting     │  │  • Development/testing mode               │   │
│  └──────────────────────┘  └────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Flow & Journey

### First-Time User Experience

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ONBOARDING FLOW                                   │
└─────────────────────────────────────────────────────────────────────────┘

 1. LANDING                    2. AI IDENTITY SETUP              3. READY
 ┌─────────────────┐          ┌─────────────────────┐          ┌─────────────────┐
 │                 │          │                     │          │                 │
 │  "Welcome to    │   ──►    │  "Give me an email  │   ──►    │  "I'm ready!    │
 │  Super Manager" │          │  I can use to work  │          │  Ask me to do   │
 │                 │          │  autonomously"      │          │  anything."     │
 │  [Get Started]  │          │                     │          │                 │
 │  [Skip]         │          │  Email: [_______]   │          │  [Start Chat]   │
 │                 │          │  App Password: [___]│          │                 │
 └─────────────────┘          └─────────────────────┘          └─────────────────┘
                               │
                               ▼
                              ┌─────────────────────┐
                              │  ENCRYPTION         │
                              │  • PBKDF2 key       │
                              │    derivation       │
                              │  • AES-256-GCM      │
                              │  • Per-user salt    │
                              └─────────────────────┘
```

### Task Execution Flow (User Perspective)

```
USER                                              SUPER MANAGER
──────                                            ────────────────

"Book a shirt        ─────────────────────►      🧠 Intent Classification
 for me"                                          │
                                                  ▼
                                                  📋 Check Memory:
                                                  • Preferred brand?
                                                  • Size? Color?
                                                  • Budget range?
                                                  │
                     ◄─────────────────────       ▼
"What brand do       (If no memory for this)     🤔 "I don't know your
 you prefer?"                                         preferences yet..."
                                                  
"I like Nike,        ─────────────────────►      💾 Save to Memory
 size L, blue"                                    │
                                                  ▼
                                                  🔐 Integration Manager:
                                                  → Check shopping APIs
                                                  → No API needed (web search)
                                                  │
                     ◄─────────────────────       ▼
"I found 3 Nike                                  📊 Search & Compare
 blue L shirts:                                   │
 1. Air Max - ₹2,999                             ▼
 2. Sportswear - ₹1,999                         🎯 Present Options
 3. Dri-FIT - ₹3,499
 
 Which one?"

"Go with #2"         ─────────────────────►      📝 Plan Steps:
                                                  1. Navigate to site
                                                  2. Add to cart
                                                  3. Apply coupons
                                                  4. Checkout
                     ◄─────────────────────       │
"Here's my plan:                                  ▼
 [steps shown]                                   ⚠️ Confirmation Required
 
 Confirm to proceed?"

"Yes, go ahead"      ─────────────────────►      ⚡ Execute Steps
                                                  │
                     ◄─────────────────────       ▼
"✅ Order placed!                                📧 Send Confirmation
 Order #12345                                    📱 Update Task Panel
 Confirmation sent
 to your email"

                                                  💭 NEXT TIME:
                                                  User: "Book a shirt"
                                                  AI: Knows brand, size,
                                                      color, budget.
                                                      Directly shows options.
```

---

## Workflow & State Machine

### Task State Machine

```
                                    ┌───────────────────┐
                                    │                   │
                                    │      PENDING      │◄────────────────────┐
                                    │   (Task Created)  │                     │
                                    │                   │                     │
                                    └─────────┬─────────┘                     │
                                              │                               │
                                              │ User Input Complete           │
                                              ▼                               │
                ┌───────────────────┐  ◄────────────────►  ┌────────────────┐│
                │                   │                       │                ││
                │   WAITING_INPUT   │◄──────────────────────│  IN_PROGRESS   ││
                │ (Missing Info)    │  Needs More Data      │ (Executing)    ││
                │                   │                       │                ││
                └───────────────────┘                       └───────┬────────┘│
                        │                                           │         │
                        │ User Provides Info                        │         │
                        │                                           │         │
                        ▼                                           │         │
                ┌───────────────────┐                               │         │
                │                   │                               │         │
                │   CONFIRMING      │◄──────────────────────────────┘         │
                │ (User Approval)   │                                         │
                │                   │                                         │
                └─────────┬─────────┘                                         │
                          │                                                   │
          ┌───────────────┼───────────────┐                                   │
          │               │               │                                   │
   User: "No"     User: "Yes"     User: "Edit"                                │
          │               │               │                                   │
          ▼               ▼               └───────────────────────────────────┘
┌───────────────┐ ┌───────────────┐
│               │ │               │
│   CANCELLED   │ │  EXECUTING    │
│               │ │               │
└───────────────┘ └───────┬───────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     Step Failed    All Steps OK    Partial Success
          │               │               │
          ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│               │ │               │ │               │
│    FAILED     │ │   COMPLETED   │ │   COMPLETED   │
│               │ │               │ │ (with notes)  │
└───────────────┘ └───────────────┘ └───────────────┘
```

### Substep State Machine

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           SUBSTEP STATES                                  │
└──────────────────────────────────────────────────────────────────────────┘

  PENDING ────► IN_PROGRESS ────► COMPLETED
     │              │                 ▲
     │              │                 │
     │              ▼                 │
     │          ┌───────┐             │
     │          │WAITING│─────────────┘
     │          │(event)│   (Event received)
     │          └───────┘
     │              │
     │              │ (Timeout/Error)
     │              ▼
     │          ┌───────┐
     │          │FAILED │
     │          └───────┘
     │
     │ (Dependencies not met / User skip)
     ▼
  ┌───────┐
  │SKIPPED│
  └───────┘
```

### Confirmation Manager Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONFIRMATION WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  AI Plans Actions
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                   SECURITY LEVEL CLASSIFICATION                  │
  │                                                                   │
  │   LOW              MEDIUM             HIGH            CRITICAL   │
  │   ────              ──────             ────            ────────   │
  │   • reminder       • email           • payment       • bank_xfer │
  │   • note           • meeting         • booking       • identity  │
  │   • search         • message         • purchase      • account   │
  │                                       • subscription    deletion │
  │                                                                   │
  │   Single           Double            Multi-step      External    │
  │   Confirm          Confirm           Verification    Verification│
  └─────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    CONFIRMATION PRESENTATION                     │
  │                                                                   │
  │   "Here's what I'm about to do:"                                 │
  │                                                                   │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │ 1. ✉️  Send email to john@example.com with invite        │   │
  │   │ 2. 📅 Create calendar event "Team Meeting"               │   │
  │   │ 3. 🔔 Set reminder for 10 minutes before                 │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                   │
  │   [✅ Confirm & Execute]  [✏️ Edit Details]  [❌ Cancel]          │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### API Routes Structure

```
/api
├── /chat                      # Main conversational endpoint
│   ├── POST /                 # Send message, get AI response
│   └── POST /action           # Handle button/interactive actions
│
├── /agent                     # Agent management
│   ├── POST /process          # Process user request
│   ├── GET /history/{session} # Get conversation history
│   └── POST /feedback         # Submit feedback on response
│
├── /tasks                     # Task management
│   ├── GET /                  # List user's tasks
│   ├── GET /{task_id}         # Get task details
│   ├── POST /confirm/{id}     # Confirm task execution
│   └── POST /cancel/{id}      # Cancel task
│
├── /identity                  # AI Identity management
│   ├── GET /status/{user_id}  # Check if AI has identity
│   ├── POST /setup            # Setup AI identity
│   └── GET /services/{id}     # List AI's service accounts
│
├── /integrations              # Integration Manager (NEW)
│   ├── GET /                  # List user's connected services
│   ├── POST /connect          # Initiate OAuth flow
│   ├── POST /callback         # OAuth callback handler
│   ├── DELETE /{id}           # Revoke integration
│   └── GET /status/{service}  # Check integration health
│
├── /streaming                 # SSE endpoints
│   └── GET /events/{session}  # Stream real-time events
│
├── /ws                        # WebSocket
│   └── /{session_id}          # Real-time bidirectional
│
└── /health                    # Health checks
    ├── GET /                  # Basic health
    ├── GET /ready             # Readiness probe
    └── GET /metrics           # Prometheus metrics
```

### Module Organization

```
backend/
├── main.py                    # FastAPI app initialization
├── config.py                  # Environment configuration (Pydantic)
├── database_supabase.py       # Supabase client
│
├── agent/                     # Autonomous Agent System
│   ├── core.py               # Main agent brain
│   ├── orchestrator.py       # Task orchestration
│   ├── task_planner.py       # AI task planning
│   ├── executor.py           # Action execution
│   ├── memory.py             # User memory system
│   ├── identity.py           # AI identity management
│   ├── browser_automation.py # Playwright automation
│   ├── service_signup.py     # Service signup automation
│   ├── gmail_reader.py       # Gmail integration
│   └── scheduler.py          # APScheduler for reminders
│
├── core/                      # Core AI & Utilities
│   ├── brain.py              # Unified AI brain
│   ├── adaptive_agent.py     # Code-generating agent
│   ├── sandbox.py            # Safe code execution
│   ├── primitives.py         # Core tool functions
│   ├── tool_registry.py      # Dynamic tool management
│   ├── intent_classifier.py  # Intent classification
│   ├── confirmation_manager.py # Confirmation workflows
│   ├── secure_actions.py     # Action security levels
│   ├── oauth_manager.py      # OAuth flow management
│   ├── teaching_mode.py      # Learn from demonstrations
│   ├── mcp_client.py         # MCP server integration
│   ├── security.py           # Security middleware
│   ├── performance.py        # Circuit breakers, caching
│   └── validation.py         # Input validation
│
└── routes/                    # API Routes
    ├── api.py                # Main chat API
    ├── streaming.py          # SSE streaming
    ├── tasks.py              # Task management
    ├── identity.py           # Identity routes
    ├── integrations.py       # Integration Manager routes (NEW)
    └── plugins.py            # Plugin routes
```

---

## AI Architecture & Flow

### Adaptive Agent Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADAPTIVE AGENT LOOP                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────┐
                    │      User Message       │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │        THINK            │
                    │  • Analyze request      │
                    │  • Check context        │
                    │  • Plan approach        │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │       GENERATE          │
                    │  LLM outputs ONE of:    │
                    │  • <action>             │
                    │  • <code>               │
                    │  • <ask>                │
                    │  • <answer>             │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │  <action>  │    │   <code>   │    │  <answer>  │
       │ Single tool│    │ Multi-step │    │   Final    │
       │   call     │    │   code     │    │  response  │
       └─────┬──────┘    └─────┬──────┘    └────────────┘
             │                 │
             ▼                 ▼
       ┌─────────────────────────────────────┐
       │         CLASSIFY RISK               │
       │  • Static pattern analysis          │
       │  • No LLM dependency                │
       │  • Returns: safe/risky/blocked      │
       └───────────────┬─────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
    ┌──────┐       ┌──────┐       ┌──────┐
    │ SAFE │       │RISKY │       │BLOCKED│
    │      │       │      │       │       │
    │Auto- │       │Needs │       │Reject │
    │exec  │       │Confirm│      │Explain│
    └──┬───┘       └──┬───┘       └───────┘
       │              │
       │              ▼
       │        ┌─────────────┐
       │        │  CONFIRM    │
       │        │  with User  │
       │        └─────┬───────┘
       │              │ (Yes)
       ▼              ▼
    ┌─────────────────────────────────────┐
    │            EXECUTE                   │
    │  • Integration Manager check        │
    │  • Sandboxed execution              │
    │  • Timeout enforcement              │
    │  • Primitive-only access            │
    └───────────────┬─────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │            OBSERVE                   │
    │  • Collect results                  │
    │  • Handle errors                    │
    │  • Update context                   │
    └───────────────┬─────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │             ADAPT                    │
    │  • If error → try alternative       │
    │  • If success → continue/finish     │
    │  • Cache successful strategy        │
    └───────────────┬─────────────────────┘
                    │
                    ▼
              (Loop continues until
               <answer> or max steps)
```

### Tool Primitives

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRIMITIVE TOOLS                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    SAFE (Auto-execute)                    RISKY (Require Confirmation)
    ────────────────────                   ───────────────────────────

    ┌─────────────────────┐                ┌─────────────────────┐
    │     web_search      │                │      fill_form      │
    │ ─────────────────── │                │ ─────────────────── │
    │ query, max_results  │                │ url, fields, submit │
    │ DuckDuckGo scraping │                │ Form automation     │
    └─────────────────────┘                └─────────────────────┘

    ┌─────────────────────┐                ┌─────────────────────┐
    │    browse_page      │                │     run_python      │
    │ ─────────────────── │                │ ─────────────────── │
    │ url                 │                │ code                │
    │ Get page content    │                │ Execute Python code │
    └─────────────────────┘                └─────────────────────┘

    ┌─────────────────────┐
    │    scrape_data      │
    │ ─────────────────── │
    │ url, extract        │
    │ Extract specific    │
    │ data from page      │
    └─────────────────────┘

    ┌─────────────────────┐
    │   generate_image    │
    │ ─────────────────── │
    │ prompt              │
    │ Pollinations AI     │
    └─────────────────────┘


    DYNAMICALLY REGISTERED (via ToolRegistry)
    ──────────────────────────────────────────

    • MCP Tools (from connected MCP servers)
    • Stealth Browser (anti-detection browsing)
    • Payment Links (Razorpay/Stripe generation)
    • Human Fallback (escalate to user)
    • Taught Workflows (user-demonstrated)
    • Integration Manager Tools (OAuth connect, token refresh)
```

---

## Security Framework

### Multi-Layer Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                       │
└─────────────────────────────────────────────────────────────────────────────┘

LAYER 1: NETWORK SECURITY
├── HTTPS enforced (HSTS)
├── CORS with strict origin whitelist
├── Rate limiting (per-IP, per-user)
└── Request size limits

LAYER 2: INPUT VALIDATION
├── Pydantic models for all inputs
├── SQL injection prevention
├── XSS sanitization
└── Path traversal prevention

LAYER 3: AUTHENTICATION & AUTHORIZATION
├── Session-based authentication
├── JWT tokens (24h expiry)
├── Per-user resource isolation
└── Role-based access (future)

LAYER 4: CODE EXECUTION SAFETY
├── Static risk analysis (no LLM dependency)
├── Forbidden pattern detection
├── Sandbox execution (restricted globals)
├── Timeout enforcement (30s)
└── Only primitives available inside sandbox

LAYER 5: DATA PROTECTION
├── Credentials encrypted (AES-256-GCM)
├── PBKDF2 key derivation
├── Per-user encryption salt
├── Sensitive data auto-deletion
└── Audit logging

LAYER 6: ACTION SECURITY
├── Security level classification
├── Multi-step confirmation for sensitive actions
├── Verification codes for HIGH/CRITICAL
└── Complete audit trail

LAYER 7: INTEGRATION SECURITY (NEW)
├── OAuth tokens encrypted at rest
├── Token auto-refresh (no user re-auth)
├── Per-integration permission scoping
├── Auto-revoke on suspicious activity
└── Integration health monitoring
```

### Forbidden Patterns (Blocked Automatically)

```python
FORBIDDEN_PATTERNS = [
    # System access
    r'\bimport\s+os\b',
    r'\bimport\s+sys\b',
    r'\bimport\s+subprocess\b',
    r'\bimport\s+shutil\b',
    
    # Network access (except via primitives)
    r'\bimport\s+socket\b',
    r'\brequests\.',
    r'\burllib\.request\b',
    r'\bhttp\.client\b',
    
    # Code execution
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\b__import__\s*\(',
    r'\bcompile\s*\(',
    
    # Dangerous operations
    r'\bopen\s*\(',
    r'\bos\.system\b',
    r'\bsubprocess\.',
    r'\bpickle\b',
    r'\bctypes\b',
    
    # Introspection attacks
    r'\bglobals\s*\(',
    r'\blocals\s*\(',
    r'\b__class__\b',
    r'\b__subclasses__\b',
]
```

---

## 1️⃣ Hard Decisions

### Decision Record

| Decision | Chosen Option | Alternatives Considered | Rationale |
|----------|---------------|------------------------|-----------| 
| **Primary AI Provider** | Groq (LLaMA 3.3 70B) | OpenAI GPT-4, Anthropic Claude | Free unlimited calls, fastest inference, sufficient quality |
| **Database** | Supabase PostgreSQL | SQLite, MongoDB, Firebase | Free tier, managed, real-time, auth built-in |
| **Code Execution** | Static risk analysis | LLM-based classification | Deterministic, fast, no dependency on AI availability |
| **Agent Architecture** | Adaptive Code Generation | Fixed tool set (LangChain style) | More flexible, handles novel tasks, self-improving |
| **Credential Storage** | Per-user AES-256 encryption | Vault/HSM, plaintext | Balance of security and simplicity |
| **Frontend** | React + Vite | Next.js, Vue, Svelte | Fast dev experience, simple deployment |
| **Deployment** | Render + Vercel | AWS/GCP, Self-hosted | Free tiers, easy CI/CD |
| **Browser Automation** | Playwright | Selenium, Puppeteer | Better stealth, async-native |
| **Real-time** | WebSocket + SSE | Polling, WebSocket only | SSE for progress, WS for bi-directional |
| **Confirmation** | Always required for sensitive | Auto-execute everything | User trust and safety over speed |
| **Integration Style** | OAuth + on-demand | Ask all upfront, raw API keys | Security, UX, and token management |

### Architectural Principles

1. **AI-First, Not AI-Only**: AI makes decisions but humans confirm sensitive actions
2. **Privacy by Design**: Credentials encrypted, sensitive data auto-deleted
3. **Fail-Safe Defaults**: Unknown patterns blocked, unknown tools rejected
4. **Observable**: Every action logged, every step trackable
5. **Adaptive**: System learns from user behavior and preferences
6. **Never Stop**: Always provide fallback when primary method fails

---

## 2️⃣ What Is Forbidden

### Code Execution Prohibitions

```
❌ NEVER ALLOWED (blocked by sandbox)
─────────────────────────────────────
• File system access (read/write/delete files)
• Network access except via primitives
• System command execution
• Dynamic code evaluation (eval, exec)
• Module imports except primitives
• Introspection attacks (__class__, __subclasses__)
• Debugging breakpoints
```

### Data Handling Prohibitions

```
❌ NEVER ALLOWED (policy)
─────────────────────────
• Storing plaintext passwords
• Storing OTPs/verification codes permanently
• Logging sensitive credentials
• Transmitting unencrypted credentials
• Sharing credentials between users
• Accessing other users' data
• Storing raw API keys (tokens only)
```

### Action Prohibitions

```
❌ NEVER ALLOWED (without explicit confirmation)
──────────────────────────────────────────────
• Financial transactions
• Account modifications
• Email sending (production)
• Form submissions
• Service signups
• Booking confirmations
• Any action with real-world consequences
```

---

## 3️⃣ State Machine Rules

### Task State Transitions

```
VALID TRANSITIONS
─────────────────

PENDING
  → IN_PROGRESS    (Start execution)
  → WAITING_INPUT  (Missing required info)
  → CANCELLED      (User cancels)

WAITING_INPUT
  → IN_PROGRESS    (User provides info)
  → CANCELLED      (User cancels / timeout)

IN_PROGRESS
  → WAITING_INPUT  (Needs more info mid-execution)
  → COMPLETED      (All steps successful)
  → FAILED         (Step failed, no recovery)
  → CANCELLED      (User cancels mid-execution)

COMPLETED, FAILED, CANCELLED
  → (terminal states, no transitions)


INVALID TRANSITIONS (enforced)
──────────────────────────────

COMPLETED → anything
FAILED → anything
CANCELLED → anything
FAILED → COMPLETED
anything → PENDING (except new task)
```

### Confirmation State Machine

```
PENDING_ACTION
  → AWAITING_CONFIRMATION  (Show to user)
  
AWAITING_CONFIRMATION
  → VERIFIED               (User confirms)
  → CANCELLED              (User rejects)
  → EXPIRED                (Timeout)

VERIFIED
  → EXECUTING              (Start execution)
  → FAILED                 (Execution failed)

EXECUTING
  → EXECUTED               (Success)
  → FAILED                 (Error)

EXECUTED, FAILED, CANCELLED, EXPIRED
  → (terminal states)
```

### Security Level Rules

```
SECURITY LEVEL REQUIREMENTS
───────────────────────────

LOW (reminder, note, search)
  → Single confirmation: "Proceed? [Yes/No]"
  → Auto-expires: 5 minutes

MEDIUM (email, meeting, message)
  → Double confirmation: Review + Confirm
  → Show detailed summary
  → Auto-expires: 10 minutes

HIGH (payment, booking, purchase)
  → Multi-step verification
  → Show amount and recipient clearly
  → Verification code sent to user
  → Auto-expires: 15 minutes
  → Audit logged

CRITICAL (bank transfer, identity verification)
  → External verification required
  → 2FA mandatory
  → Manual approval process
  → Permanent audit log
  → Auto-expires: 30 minutes
```

---

## 4️⃣ Data Ownership Rules

### User Data Ownership

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA OWNERSHIP MAP                                  │
└─────────────────────────────────────────────────────────────────────────────┘

USER OWNS (full control)
────────────────────────
• User profile (name, email, phone)
• Contacts
• Preferences
• Conversation history
• Task history
• AI identity credentials
• Service account credentials
• Integration tokens (encrypted)
• Connected app list

→ Can export at any time
→ Can delete at any time
→ Encrypted at rest
→ Never shared without consent


PLATFORM OWNS (operational)
───────────────────────────
• Anonymized usage metrics
• Aggregated error logs
• Feature usage statistics
• Performance metrics

→ No user-identifiable data
→ Used for improvement only
→ Not sold to third parties


AI LEARNS (with permission)
───────────────────────────
• User preferences (opt-in)
• Interaction patterns
• Task success patterns
• Communication style

→ Used only for that user
→ Improves personalization
→ Can be reset/deleted
```

### Data Retention Rules

```
RETENTION POLICY
────────────────

Conversations:      90 days active, then archived
Task details:       1 year, then summarized
User preferences:   Until deleted by user
Credentials:        Until deleted or rotated
Integration tokens: Until revoked or expired
Audit logs:         1 year (compliance)
Sensitive data:     Deleted immediately after use
Session data:       24 hours
OTPs:               5 minutes
Verification codes: 15 minutes
```

---

## 5️⃣ Infrastructure Contract

### Availability Guarantees

```
SERVICE LEVEL OBJECTIVES
────────────────────────

COMPONENT               TARGET          MEASUREMENT
─────────────────────────────────────────────────────
API Availability        99.9%           Monthly uptime
Response Time (p95)     < 500ms         Per request
Response Time (p99)     < 2s            Per request
AI Response Time        < 10s           First token
WebSocket Uptime        99.5%           Monthly
Database Uptime         99.99%          Supabase SLA
Integration Health      99%             Per-service
```

### Resource Limits

```
RATE LIMITS (per user)
──────────────────────
API Requests:       100/minute
AI Requests:        20/minute
WebSocket Messages: 60/minute
File Uploads:       10MB/file
Task Queue:         50 concurrent
OAuth Connections:  20 per user

CIRCUIT BREAKERS
────────────────
AI Provider:        5 failures → 30s cooldown
Database:           3 failures → 10s cooldown
Email Service:      5 failures → 60s cooldown
Browser Automation: 3 failures → 30s cooldown
Integration APIs:   3 failures → 60s cooldown + fallback
```

### Scaling Policy

```
HORIZONTAL SCALING
──────────────────

Trigger: CPU > 70% for 5 minutes
Action:  Add worker instance
Max:     10 instances
Min:     2 instances

Trigger: CPU < 30% for 10 minutes
Action:  Remove worker instance
Min:     2 instances

VERTICAL SCALING
────────────────
Memory: 512MB base, 2GB max per container
CPU:    0.5 vCPU base, 2 vCPU max per container
```

### Disaster Recovery

```
BACKUP SCHEDULE
───────────────
Database:     Daily automated (Supabase)
User data:    Real-time sync
Credentials:  Encrypted backup weekly
Configuration: Git-versioned
Integration tokens: Encrypted backup daily

RECOVERY TIME
─────────────
RTO (Recovery Time Objective):     < 1 hour
RPO (Recovery Point Objective):    < 1 hour
```

---

## Development Lifecycle

### Spec Invariants → Tests → Implementation → Red-team → Refactor → Audit

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DEVELOPMENT LIFECYCLE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

1. SPEC INVARIANTS
   ─────────────────
   Define what must ALWAYS be true:
   
   □ "User credentials are NEVER stored in plaintext"
   □ "Sensitive actions ALWAYS require confirmation"
   □ "Sandbox NEVER allows file system access"
   □ "User data is NEVER accessible to other users"
   □ "Integration tokens are ALWAYS encrypted at rest"
   □ "Fallback routes are ALWAYS available"
   
   Document in: /docs/invariants.md

2. WRITE TESTS FIRST
   ──────────────────
   Before implementing any feature:
   
   tests/
   ├── test_security.py      # Security invariant tests
   ├── test_functional.py    # Feature behavior tests
   ├── test_integration.py   # End-to-end flows
   └── test_smoke.py         # Quick sanity checks
   
   Run: pytest tests/ -v

3. GENERATE IMPLEMENTATION
   ────────────────────────
   Implement until all tests pass:
   
   □ Start with failing tests (RED)
   □ Write minimal code to pass (GREEN)
   □ Refactor for quality (REFACTOR)
   
4. RED-TEAM IT
   ────────────
   Attack your own implementation:
   
   □ Attempt SQL injection
   □ Attempt XSS attacks
   □ Attempt sandbox escape
   □ Attempt credential theft
   □ Attempt privilege escalation
   □ Attempt rate limit bypass
   □ Attempt OAuth token theft
   
   Document findings in: /docs/security-audit.md

5. REFACTOR
   ─────────
   Improve without changing behavior:
   
   □ Extract common patterns
   □ Remove duplication
   □ Improve naming
   □ Add documentation
   □ Optimize performance
   
   Ensure: All tests still pass

6. INTEGRATION AUDIT
   ──────────────────
   Before merge to main:
   
   □ Code review by team member
   □ Security review for sensitive code
   □ Performance benchmark comparison
   □ Documentation update
   □ Changelog entry
```

---

## API Reference

### Main Chat Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Schedule a meeting with John tomorrow at 3pm",
  "session_id": "optional-session-id",
  "user_id": "user-unique-id"
}

Response:
{
  "message": "I'll schedule a meeting with John tomorrow at 3pm...",
  "type": "task",
  "status": "confirm",
  "session_id": "sess_abc123",
  "steps": [
    {"step": 1, "action": "create_meeting", "description": "Create meeting link"},
    {"step": 2, "action": "send_email", "description": "Send invite to John"}
  ],
  "ui_components": {
    "type": "confirmation",
    "buttons": [
      {"label": "Confirm", "action": "confirm_yes"},
      {"label": "Cancel", "action": "confirm_no"}
    ]
  },
  "integration_status": {
    "calendar": "connected",
    "email": "connected"
  }
}
```

### Interactive Actions

```http
POST /api/chat/action
Content-Type: application/json

{
  "action": "confirm_yes",
  "button_id": "btn_confirm",
  "metadata": {},
  "session_id": "sess_abc123",
  "user_id": "user-unique-id"
}

Response:
{
  "message": "✅ Meeting scheduled! Invite sent to John.",
  "type": "task",
  "status": "done",
  "result": {
    "meeting_link": "https://meet.jit.si/...",
    "invite_sent": true
  },
  "proof": {
    "type": "meeting",
    "link": "https://meet.jit.si/...",
    "time": "2026-03-01T15:00:00Z"
  }
}
```

### Task Management

```http
GET /api/tasks/?user_id=user-id
Response: { "tasks": [...] }

GET /api/tasks/{task_id}
Response: { "task": {...}, "substeps": [...] }

POST /api/tasks/confirm/{task_id}
Response: { "status": "executing" }

POST /api/tasks/cancel/{task_id}
Response: { "status": "cancelled" }
```

### Identity Management

```http
GET /api/identity/status/{user_id}
Response: { "has_identity": true/false }

POST /api/identity/setup
{
  "user_id": "user-id",
  "email": "ai-agent@gmail.com",
  "password": "app-password"
}
Response: { "success": true, "identity": {...} }
```

### Integration Management (NEW)

```http
GET /api/integrations/
Response: {
  "connected": [
    {"service": "google_calendar", "status": "active", "connected_at": "..."},
    {"service": "gmail", "status": "active", "connected_at": "..."}
  ],
  "available": ["outlook", "slack", "github", "trello"]
}

POST /api/integrations/connect
{
  "service": "google_calendar",
  "scopes": ["calendar.events", "calendar.readonly"]
}
Response: { "oauth_url": "https://accounts.google.com/..." }

DELETE /api/integrations/{integration_id}
Response: { "revoked": true }
```

---

## Database Schema

### Core Tables

```sql
-- Users table
users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  phone VARCHAR(50),
  telegram_id VARCHAR(100),
  timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)

-- AI Identity (one per user)
ai_identities (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  email VARCHAR(255) NOT NULL,
  encrypted_password TEXT,
  status VARCHAR(50) DEFAULT 'pending_setup',
  can_send_email BOOLEAN DEFAULT FALSE,
  can_signup_services BOOLEAN DEFAULT FALSE,
  UNIQUE(user_id)
)

-- Service accounts (AI's API keys)
ai_service_accounts (
  id UUID PRIMARY KEY,
  ai_identity_id UUID REFERENCES ai_identities(id),
  service_name VARCHAR(255) NOT NULL,
  encrypted_api_key TEXT,
  status VARCHAR(50) DEFAULT 'active',
  UNIQUE(ai_identity_id, service_name)
)

-- User Integrations (NEW - Integration Manager)
user_integrations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  service_name VARCHAR(100) NOT NULL,
  provider VARCHAR(100) NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  scopes TEXT[],
  connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_used_at TIMESTAMP WITH TIME ZONE,
  UNIQUE(user_id, service_name)
)

-- Integration Tokens (NEW - encrypted token storage)
integration_tokens (
  id UUID PRIMARY KEY,
  integration_id UUID REFERENCES user_integrations(id),
  encrypted_access_token TEXT NOT NULL,
  encrypted_refresh_token TEXT,
  token_type VARCHAR(50) DEFAULT 'Bearer',
  expires_at TIMESTAMP WITH TIME ZONE,
  refreshed_at TIMESTAMP WITH TIME ZONE,
  encryption_salt TEXT NOT NULL
)

-- Task orchestration
orchestrated_tasks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR(500) NOT NULL,
  task_type VARCHAR(100) NOT NULL,
  progress_percent INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'pending',
  needs_user_input BOOLEAN DEFAULT FALSE
)

-- Task substeps
task_substeps (
  id UUID PRIMARY KEY,
  task_id UUID REFERENCES orchestrated_tasks(id),
  step_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  action_type VARCHAR(100),
  action_params JSONB DEFAULT '{}'
)
```

---

## Deployment

### Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...              # Free at console.groq.com
SUPABASE_URL=https://...          # Supabase project URL
SUPABASE_KEY=eyJ...               # Supabase anon key
ENCRYPTION_SECRET=your-secret-32  # Min 32 chars

# Optional - Fallback AI
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
SAMBANOVA_API_KEY=...

# Optional - Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your@gmail.com
SMTP_PASSWORD=app-password

# Optional - Integrations
TELEGRAM_BOT_TOKEN=...
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...

# Optional - OAuth (Integration Manager)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

### Docker Deployment

```bash
# Build and run
docker compose up -d

# With local LLM (Ollama)
docker compose --profile local-llm up -d

# With monitoring (Prometheus + Grafana)
docker compose --profile monitoring up -d
```

### Cloud Deployment

```bash
# Render (Backend)
# Add render.yaml to repo, connect to Render

# Vercel (Frontend)
cd frontend
vercel deploy

# Railway
railway up
```

---

## Enterprise Features

### Planned Enhancements

| Feature | Status | Priority |
|---------|--------|----------|
| Multi-tenant isolation | 🔄 | High |
| SSO (SAML/OIDC) | 📋 | High |
| Role-based access control | 📋 | High |
| Integration marketplace | 📋 | High |
| Audit log export | 📋 | Medium |
| Custom AI model deployment | 📋 | Medium |
| On-premise deployment | 📋 | Medium |
| Data residency compliance | 📋 | Medium |
| API key management portal | 📋 | Low |
| White-label customization | 📋 | Low |

### Compliance Roadmap

| Compliance | Status | Notes |
|------------|--------|-------|
| GDPR | 🔄 | Data export, deletion implemented |
| SOC 2 | 📋 | Audit controls in place |
| HIPAA | 📋 | Healthcare use cases |
| ISO 27001 | 📋 | Information security |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key (free at console.groq.com)
- Supabase account (free tier works)

### Backend Setup

```bash
# Clone
git clone <repo-url>
cd super-manager

# Virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your keys

# Run
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/api/health

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_id": "test"}'
```

---

## UI Components & Screens (Production Ready)

### UI Component Hierarchy

```
App
├── OnboardingWizard (conditional first-time)
│   ├── Step: Welcome
│   ├── Step: AI Identity Setup
│   ├── Step: Preference Collection
│   └── Step: First Task Tutorial
│
├── Header
│   ├── Logo
│   ├── SearchBar
│   ├── NotificationBell (with badge)
│   └── UserMenu (dropdown)
│
├── Sidebar (collapsible)
│   ├── NavItem: Chat
│   ├── NavItem: Tasks
│   ├── NavItem: History
│   ├── NavItem: Memory
│   ├── NavItem: Integrations (NEW)
│   └── NavItem: Settings
│
├── MainArea
│   ├── ChatInterface
│   │   ├── MessageList
│   │   │   ├── UserMessage
│   │   │   └── AIMessage
│   │   │       ├── TextContent
│   │   │       ├── CodeBlock (syntax highlighted)
│   │   │       ├── UIComponentRenderer
│   │   │       │   ├── ConfirmationCard
│   │   │       │   ├── OptionSelector
│   │   │       │   ├── ProgressTracker
│   │   │       │   ├── IntegrationPrompt (NEW)
│   │   │       │   └── ProofCard
│   │   │       └── FeedbackButtons (👍👎)
│   │   │
│   │   ├── TypingIndicator
│   │   └── InputArea
│   │       ├── TextField
│   │       ├── AttachButton
│   │       └── SendButton
│   │
│   ├── TaskPanel (slide-in)
│   │   ├── TaskHeader
│   │   ├── TaskProgress (circular)
│   │   ├── SubstepList
│   │   │   └── SubstepCard (with status icon)
│   │   └── TaskActions (confirm/cancel)
│   │
│   └── IntegrationsHub (NEW)
│       ├── ConnectedServices
│       ├── AvailableIntegrations
│       └── IntegrationDetail (manage/revoke)
│
├── SettingsModal
│   ├── ProfileSettings
│   ├── AIIdentitySettings
│   ├── IntegrationSettings (NEW)
│   ├── PreferencesSettings
│   └── SecuritySettings
│
└── ToastNotifications
```

---

## Authentication & Authorization Flow

### Auth Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AUTH FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

OPTION 1: Supabase Auth (Recommended for MVP)
─────────────────────────────────────────────

Frontend                     Supabase                    Backend
────────                     ────────                    ───────
    │                            │                           │
    │  1. User enters email      │                           │
    │ ──────────────────────────►│                           │
    │                            │                           │
    │  2. Magic link sent        │                           │
    │ ◄──────────────────────────│                           │
    │                            │                           │
    │  3. User clicks link       │                           │
    │ ──────────────────────────►│                           │
    │                            │                           │
    │  4. JWT returned           │                           │
    │ ◄──────────────────────────│                           │
    │                            │                           │
    │  5. API call with JWT      │                           │
    │ ─────────────────────────────────────────────────────►│
    │                            │                           │
    │                            │  6. Verify JWT            │
    │                            │◄──────────────────────────│
    │                            │                           │
    │                            │  7. User identity         │
    │                            │──────────────────────────►│
    │                            │                           │
    │  8. Response               │                           │
    │ ◄─────────────────────────────────────────────────────│


OPTION 2: OAuth Providers
─────────────────────────

Supported:
• Google (recommended)
• GitHub
• Microsoft
• Apple

Implementation via Supabase Auth or direct OAuth


SESSION MANAGEMENT
──────────────────

• JWT in HTTP-only cookie (web)
• JWT in secure storage (mobile)
• 24-hour expiry
• Refresh token rotation
• Session invalidation on logout

```

---

## Predictive Intelligence (User Learning)

### How Super Manager Learns & Predicts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LEARNING SYSTEM                                          │
└─────────────────────────────────────────────────────────────────────────────┘

DATA COLLECTION (Explicit + Implicit)
─────────────────────────────────────

EXPLICIT (User tells us):
• Onboarding preferences
• Direct preference settings
• Corrections ("No, I meant...")
• Feedback (👍👎)

IMPLICIT (We observe):
• Time of day for requests
• Types of tasks requested
• Confirmation patterns
• Communication style
• Integration usage patterns
• Error recovery preferences


PREFERENCE STORAGE
──────────────────

Database Table: preferences
{
  user_id: UUID,
  category: "fashion" | "travel" | "meetings" | "shopping" | ...,
  key: "preferred_brand" | "size" | "budget_range" | ...,
  value: any,
  confidence: 0.0-1.0,  // How sure we are
  last_updated: timestamp
}

Examples:
• fashion.preferred_brand = "Nike" (confidence: 0.95)
• fashion.size = "L" (confidence: 1.0)
• fashion.color_preference = "blue, black" (confidence: 0.8)
• shopping.budget_range = "1000-5000" (confidence: 0.7)
• meetings.preferred_duration = "30min" (confidence: 0.9)


PREDICTION ENGINE
─────────────────

When user says: "Book me a shirt"

1. Intent Classification → shopping.clothing.shirt

2. Preference Lookup:
   • fashion.preferred_brand → "Nike" (0.95)
   • fashion.size → "L" (1.0)
   • fashion.color_preference → "blue" (0.8)
   • shopping.budget_range → "1000-5000" (0.7)

3. Confidence Check:
   IF all key preferences have confidence > 0.8:
     → Proceed with assumed preferences
     → Show user what we assumed
   ELSE:
     → Ask only for low-confidence items
     → "I remember you like Nike in size L. What color today?"

4. Search with preferences:
   → web_search("Nike blue shirt L ₹1000-₹5000")

5. Present personalized results:
   → "Here are Nike blue L shirts in your budget..."


CONFIDENCE UPDATES
──────────────────

User confirms prediction  → confidence += 0.1 (max 1.0)
User corrects prediction  → confidence = 0.3 (learned wrong)
User provides new data    → confidence = 0.8 (explicit)
No usage for 90 days      → confidence -= 0.1 (decay)
```

---

## Complete Data Flow

### End-to-End Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

USER ACTION: "Schedule a meeting with John tomorrow at 3pm"

┌─────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                                     │
│ ─────────                                                                    │
│ 1. Message typed in ChatInput component                                      │
│ 2. Send button clicked                                                       │
│ 3. fetch('/api/chat', { message, session_id, user_id })                     │
│ 4. Show loading indicator                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ API GATEWAY (FastAPI)                                                        │
│ ─────────────────────                                                        │
│ 1. Rate limit check                                                          │
│ 2. JWT validation                                                            │
│ 3. Request validation (Pydantic)                                             │
│ 4. Input sanitization                                                        │
│ 5. Forward to chat() handler                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ AI BRAIN (brain.py)                                                          │
│ ──────────────────                                                           │
│ 1. Get/create session                                                        │
│ 2. Load user preferences from memory                                         │
│ 3. Build context for AI                                                      │
│ 4. Call AdaptiveAgent.run()                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ADAPTIVE AGENT (adaptive_agent.py)                                           │
│ ─────────────────────────────────                                            │
│ STEP 1: THINK → "User wants meeting. Need calendar + email."                │
│ STEP 2: CHECK PREFERENCES → Duration=30min, platform=Jitsi                  │
│ STEP 3: CHECK INTEGRATIONS (Integration Manager)                             │
│   → Calendar: connected ✅ → proceed                                        │
│   → Email: connected ✅ → proceed                                           │
│ STEP 4: GENERATE → Plan meeting creation + email invite                      │
│ STEP 5: CLASSIFY RISK → MEDIUM (needs confirmation)                         │
│ STEP 6: CONFIRM with user → Show plan                                        │
│ STEP 7: EXECUTE → Create meeting + send invite                               │
│ STEP 8: OBSERVE → Both actions succeeded                                     │
│ STEP 9: ADAPT → Cache successful strategy                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPLETION & LEARNING                                                        │
│ ─────────────────────                                                        │
│ 1. Task marked COMPLETED                                                     │
│ 2. Meeting link + invite proof saved                                         │
│ 3. Update preference confidence                                              │
│ 4. Integration usage tracked                                                 │
│ 5. Update task panel in frontend                                             │
│ 6. Show success message to user                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first
4. Implement feature
5. Run full test suite
6. Submit pull request

---

## 📊 Implementation Status & Gap Analysis

### Layer Status (as of 2026-03-22)

| Layer | Target | Current | Gap | Priority |
|-------|--------|---------|-----|----------|
| 1. Input Layer | 100% | **95%** | ✅ Telegram, WhatsApp, Voice webhooks | ✅ Done |
| 2. Intent Engine | 100% | 85% | Working | ✅ Done |
| 3. Task Classifier | 100% | **95%** | ✅ Categories routed, risk assessed | ✅ Done |
| 4. Planner | 100% | 95% | Working | ✅ Done |
| 5. Capability Router | 100% | 90% | Working | ✅ Done |
| 6. Integration Manager | 100% | **95%** | ✅ Fallback router, error handling | ✅ Done |
| 7. Execution Layer | 100% | 80% | Working | ✅ Done |
| 8. Human-in-Loop | 100% | 90% | Working | ✅ Done |
| 9. Memory | 100% | 85% | Working | ✅ Done |
| 10. Learning Loop | 100% | **90%** | ✅ Confidence scoring, feedback | ✅ Done |

### Working Features ✅

- Web Chat interface
- Web Search (DuckDuckGo)
- Browse/Scrape web pages
- Email sending (Gmail OAuth + SMTP)
- Image generation (Pollinations)
- Meeting creation (Jitsi fallback + Zoom OAuth)
- Multi-step planning
- User memory & preferences
- Confirmation flows
- **Telegram messaging** (`send_telegram` primitive) ← LATEST
- **Integration Manager with fallback routing**
- **Task Classification (category/complexity/risk)**
- **Telegram webhook** (`/webhook/telegram`)
- **WhatsApp via Twilio** (`/webhook/whatsapp`)
- **Voice transcription** (`/api/voice/transcribe`)
- **Learning Loop with confidence scoring**
- **Strategy caching with decay**
- **Feedback → improvement pipeline**

### OAuth Setup ⚠️ Required for Gmail/Google Integrations

To fix the "redirect_uri_mismatch" error:

1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add these **Authorized redirect URIs**:
   ```
   http://localhost:10000/api/oauth/callback
   https://your-production-domain.com/api/oauth/callback
   ```
4. Click **Save**

### Configuration Required (for full functionality)

The following API keys need to be set in `.env`:

```bash
# For Telegram bot
TELEGRAM_BOT_TOKEN=your_bot_token

# For WhatsApp via Twilio  
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# For Zoom meetings
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
ZOOM_ACCOUNT_ID=your_zoom_account_id

# For Voice transcription
OPENAI_API_KEY=your_openai_key  # Uses Whisper API
```

### Recent Improvements (2026-03-22)

1. **Input Layer** (`backend/routes/messaging.py`) ← NEW
   - Telegram webhook handler (`/webhook/telegram`)
   - WhatsApp via Twilio (`/webhook/whatsapp`)
   - Voice transcription via Whisper (`/api/voice/transcribe`)
   - Status check endpoint (`/api/messaging/status`)

2. **Task Classifier** (`backend/core/task_classifier.py`)
   - 15 task categories (SHOPPING, MEETING, EMAIL, etc.)
   - Complexity scoring (SIMPLE, MEDIUM, COMPLEX)
   - Risk levels (NONE → CRITICAL) with auto-confirmation rules
   - Wired into adaptive_agent pipeline

3. **Integration Manager** (`backend/core/integration_manager/fallback_router.py`)
   - Fallback routing: API → Browser → User Input → Partial Assist
   - Never stops on missing API - always provides alternatives
   - Zoom config check before attempting

4. **Learning Loop** (`backend/core/strategy_store.py`)
   - Confidence scoring (0.1 - 1.0)
   - Positive feedback → +15% confidence
   - Negative feedback → -25% confidence
   - Unused decay: -5% per day after 7 days
   - Auto-prune low-confidence strategies
   - `/api/learning/stats` endpoint

5. **Frontend** (`frontend/src/AppClean.jsx`, `styles/clean-theme.css`)
   - Integration prompt UI with connect/fallback buttons
   - Task classification badge
   - Proof badge styling

### Latest Fixes (2026-06-07)

1. **Telegram Messaging** (`backend/core/primitives.py`)
   - Added `send_telegram(message, chat_id, username)` primitive
   - Registered in tool_registry
   - AI can now send Telegram messages directly

2. **Integrations Hub** (`frontend/src/components/IntegrationsHub.jsx/css`)
   - Fixed scrolling issue in side panel
   - Made layout responsive for narrow panels
   - Proper overflow handling

3. **OAuth Documentation**
   - Added clear instructions for fixing redirect_uri_mismatch
   - Users must add URIs to Google Cloud Console

### Known Limitations

1. **Code Generation/App Building**: The AI plans and executes tasks but does NOT generate full applications like GitHub Spark. This would require a major new feature (code gen + sandbox + preview).

2. **Telegram Username Lookup**: When sending to a username (e.g., @witez2112), the user must have messaged the bot first to establish a chat_id. Otherwise, provide the numeric chat_id directly.

---

## License

Proprietary - All rights reserved.

---

<div align="center">

**Built with ❤️ by the Super Manager Team**

*Making AI that actually does things.*

</div>
