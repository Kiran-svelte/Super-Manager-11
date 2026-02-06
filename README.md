# Super Manager - AI Agent System

<div align="center">

**🤖 Transform natural language into executed actions through intelligent conversations.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)

**[Live Demo](https://frontend-snowy-chi-2d9q9syghe.vercel.app)** • **[API](https://super-manager-api.onrender.com)**

</div>

---

## 🎯 What is Super Manager?

Super Manager is an AI-powered assistant that **understands your intent and executes real actions** - not just providing search results.

### The Problem
```
User: "Schedule a meeting with John tomorrow at 3pm"

❌ Traditional AI: "Here are some meeting scheduling tips..."
✅ Super Manager: Creates the meeting, generates link, sends invite to John
```

### How It Works

```
INPUT → AI UNDERSTANDS → PLANS → ASKS FOR MISSING INFO → CONFIRMS → EXECUTES → DONE
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Conversations** | Talk like you would to a human assistant |
| 📅 **Meeting Scheduling** | Create Jitsi meetings with automatic invites |
| 📧 **Email Sending** | Send emails with natural language |
| 💳 **Payment Reminders** | Smart payment tracking and reminders |
| 🎂 **Event Planning** | Multi-stage planning for parties/events |
| 🔄 **Task Confirmation** | Always confirms before executing actions |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vercel)                    │
│                     Clean Chat Interface                      │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI/Render)                   │
│                                                               │
│    ┌────────────────────────────────────────────────────┐   │
│    │                   AI BRAIN                          │   │
│    │               (backend/core/brain.py)               │   │
│    │                                                     │   │
│    │  INPUT → UNDERSTAND → PLAN → CONFIRM → EXECUTE     │   │
│    │                                                     │   │
│    │  • Groq LLM (llama-3.3-70b-versatile)             │   │
│    │  • Task Detection & Planning                       │   │
│    │  • Missing Info Collection                         │   │
│    │  • User Confirmation Flow                          │   │
│    │  • Real Action Execution                           │   │
│    └────────────────────────────────────────────────────┘   │
│                              │                               │
│    ┌────────────────────────┴────────────────────────────┐  │
│    │                    PLUGINS                           │  │
│    │  📧 Email  │  📅 Meeting  │  💳 Payment  │  📱 Notify │  │
│    └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Core Flow

1. **User Input** → Message received via `/api/chat`
2. **AI Analysis** → Groq LLM determines: question or task?
3. **If Question** → Direct answer returned
4. **If Task** → Plan created, missing info requested
5. **Info Collection** → AI asks for required details
6. **Confirmation** → User confirms before execution
7. **Execution** → Real action performed (meeting/email/etc)
8. **Result** → Success message with details

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### Backend Setup

```bash
# Clone and setup
git clone https://github.com/Kiran-svelte/Super-Manager-11.git
cd Super-Manager-11

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Run
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Reference

### Main Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Schedule a meeting with John tomorrow at 3pm",
  "session_id": "optional-session-id"
}
```

### Response Types

**Answer Response:**
```json
{
  "message": "Hello! How can I help you?",
  "type": "answer",
  "session_id": "abc123"
}
```

**Task - Needs Info:**
```json
{
  "message": "Got it! What's John's email address?",
  "type": "task",
  "status": "need_info",
  "need": ["email address"],
  "session_id": "abc123"
}
```

**Task - Confirm:**
```json
{
  "message": "Ready to schedule meeting with John at 3pm tomorrow. Proceed?",
  "type": "task",
  "status": "confirm",
  "summary": "Meeting: John @ 3pm tomorrow",
  "session_id": "abc123"
}
```

**Task - Done:**
```json
{
  "message": "✅ Meeting created! Link: https://meet.jit.si/xxx",
  "type": "task",
  "status": "done",
  "result": {
    "success": true,
    "link": "https://meet.jit.si/xxx"
  },
  "session_id": "abc123"
}
```

---

## 🌐 Deployment

### Backend (Render)
- Auto-deploys from `main` branch
- URL: `https://super-manager-api.onrender.com`

### Frontend (Vercel)
- Auto-deploys from `main` branch
- URL: `https://frontend-snowy-chi-2d9q9syghe.vercel.app`

---

## 📁 Project Structure

```
Super-Manager-11/
├── backend/
│   ├── core/
│   │   ├── brain.py          # 🧠 Main AI logic
│   │   ├── plugins.py        # Plugin system
│   │   └── ...
│   ├── routes/
│   │   ├── api.py            # /api/chat endpoint
│   │   └── ...
│   └── main.py               # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Chat interface
│   │   └── App.css           # Styles
│   └── package.json
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

```env
# Required
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Optional
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=app_specific_password
```

---

## 🤝 Example Conversations

### Meeting Scheduling
```
You: Schedule a meeting with John tomorrow at 3pm
AI: Got it! What's the meeting about and John's email?
You: Project review, john@example.com
AI: Ready to schedule "Project Review" with John at 3pm tomorrow. Proceed?
You: yes
AI: ✅ Meeting created! Link: https://meet.jit.si/supermanager-xxx
    Invite sent to: john@example.com
```

### Email Sending
```
You: Send an email to sarah@company.com about the deadline extension
AI: What should the email say?
You: Hi Sarah, the deadline has been extended to next Friday
AI: Ready to send email to sarah@company.com. Proceed?
You: yes
AI: ✅ Email sent to sarah@company.com!
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ❤️ by the Super Manager Team
</div>
