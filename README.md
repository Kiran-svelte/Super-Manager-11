# Super Manager - AI Agent System

**Transform natural language into executed actions through intelligent conversations.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)

---

## What is Super Manager?

Super Manager is an AI-powered assistant that **understands your intent and executes real actions** - not just providing search results or tips.

```
User: "Schedule a meeting with John tomorrow at 3pm"

Traditional AI: "Here are some meeting scheduling tips..."
Super Manager:  Creates the meeting, generates link, sends invite to John
```

## Features

- **Natural Conversations** - Talk like you would to a human assistant
- **Meeting Scheduling** - Create Jitsi/Zoom meetings with automatic invites
- **Email Sending** - Gmail OAuth 2.0 + SMTP fallback
- **Web Search & Browsing** - Real-time web search and page browsing
- **Image Generation** - Pollinations AI (free, no API key)
- **Task Confirmation** - Always confirms before executing sensitive actions
- **Multi-Provider AI** - Groq (free), OpenAI, Ollama (local)
- **Real-time Updates** - WebSocket-based live progress
- **Telegram Integration** - Bot notifications

## Architecture

```
Frontend (React/Vite)  --->  Backend (FastAPI)  --->  Supabase (PostgreSQL)
     Vercel                     Render                   Free tier
       |                          |
       |--- WebSocket ------------|
                                  |
                          AI Brain (ReAct Agent)
                          |    |    |    |
                        Groq  Tools  Plugins  Memory
```

### Core Flow

1. **User Input** - Message via `/api/chat`
2. **AI Analysis** - Groq LLM: question or task?
3. **If Question** - Direct answer
4. **If Task** - Plan, collect missing info, confirm, execute
5. **Result** - Action performed with proof

## Quick Start

### Backend

```bash
git clone <repo-url>
cd super-manager

python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your GROQ_API_KEY (free at console.groq.com)

python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
# Core services (backend + redis + frontend)
docker compose up -d

# With local LLM (Ollama)
docker compose --profile local-llm up -d

# With monitoring (Prometheus + Grafana)
docker compose --profile monitoring up -d
```

## API

### Main Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Schedule a meeting with John tomorrow at 3pm",
  "session_id": "optional",
  "user_id": "optional"
}
```

### Other Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/status` | GET | System status |
| `/api/metrics` | GET | Performance metrics |
| `/ws/{user_id}` | WS | Real-time updates |
| `/api/stream/*` | POST | Streaming responses |
| `/api/docs` | GET | Interactive API docs |

## Project Structure

```
super-manager/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Environment config
│   ├── database_supabase.py    # Supabase PostgreSQL
│   ├── core/
│   │   ├── brain.py            # AI brain (ReAct agent)
│   │   ├── engine.py           # Task execution engine
│   │   ├── tools/              # 12+ tools (search, email, etc.)
│   │   ├── ai_providers/       # Groq, OpenAI, Ollama routing
│   │   ├── realtime/           # WebSocket manager
│   │   └── ...
│   ├── routes/
│   │   ├── api.py              # /api/chat (main endpoint)
│   │   ├── streaming.py        # Streaming responses
│   │   └── ...
│   └── agent/                  # Agent system (scheduler, orchestrator)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Chat interface
│   │   ├── components/         # UI components
│   │   └── App.css
│   ├── package.json
│   └── vite.config.js
├── infrastructure/
│   ├── nginx.conf              # Reverse proxy
│   └── prometheus.yml          # Metrics collection
├── tests/                      # Test suite
├── .github/workflows/          # CI/CD pipeline
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml          # Full stack
├── render.yaml                 # Render deployment
├── requirements.txt
└── .env.example
```

## Configuration

Required environment variables (see `.env.example`):

```env
GROQ_API_KEY=your_groq_key          # Free at console.groq.com
SUPABASE_URL=your_supabase_url      # Free at supabase.com
SUPABASE_KEY=your_supabase_key
SECRET_KEY=generate_random_string
```

## Deployment

- **Backend**: Render (free tier) - auto-deploys from `main`
- **Frontend**: Vercel (free tier) - auto-deploys from `main`
- **Database**: Supabase (free tier) - PostgreSQL
- **AI**: Groq (free tier) - llama-3.3-70b-versatile

## License

MIT
