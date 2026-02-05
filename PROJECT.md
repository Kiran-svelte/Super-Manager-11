# 🚀 Super Manager - AI Action Execution System

> **Transform natural language into executed actions**
> 
> Most AI assistants just talk. Super Manager **does**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [AI Providers](#ai-providers)
- [Workflows](#workflows)
- [Plugins](#plugins)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Development](#development)

---

## 🎯 Overview

Super Manager is an intelligent AI assistant that bridges the gap between **user intent** and **task execution**. Instead of just providing information, it:

1. **Understands** your natural language request
2. **Plans** a multi-step workflow dynamically
3. **Executes** real actions (send emails, create meetings, make bookings)
4. **Reports** progress in real-time via WebSocket

### Example Flow

```
User: "Plan a surprise birthday party for my wife next Saturday 
       in Goa, invite our 10 friends, budget around 50k"

Super Manager:
├─ [Parse] Extract: wife, Saturday, Goa, 10 friends, ₹50k
├─ [Plan] AI creates workflow: venue → catering → invites → surprises
├─ [Ask] "Which area in Goa - North (beaches) or South (quiet)?"
├─ [Search] Find venues matching budget
├─ [Present] "Here are 4 options, select one..."
├─ [Confirm] "Ready to book Beach Resort at ₹35k and send invites?"
├─ [Execute] 
│   ├─ Book venue ✅
│   ├─ Send 10 email invites ✅ (8 delivered, 2 need alternate)
│   └─ Send Telegram reminder ✅
└─ [Complete] "Party planned! Booking confirmed, invites sent."
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   Chat   │  │ Options  │  │ Confirm  │  │ Real-time Status │ │
│  │  Input   │  │ Selector │  │  Modal   │  │   (WebSocket)    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼──────────────────┼──────────┘
        │             │             │                  │
        └─────────────┴─────────────┴──────────────────┘
                              │ HTTP/WS
┌─────────────────────────────┼───────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │                      API Gateway                          │   │
│  │  /api/agent/* │ /api/task/* │ /api/plugins/* │ /ws/*     │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │                    AI ROUTER                              │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │ Ollama  │→ │  Groq   │→ │  Zuki   │→ │ OpenAI  │      │   │
│  │  │ (local) │  │ (fast)  │  │ (free)  │  │ (paid)  │      │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              DYNAMIC WORKFLOW ENGINE                      │   │
│  │  [Intent Parser] → [Workflow Planner] → [Stage Executor] │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │                    PLUGIN SYSTEM                          │   │
│  │  ┌────────┐ ┌───────┐ ┌─────────┐ ┌──────────┐ ┌───────┐ │   │
│  │  │Telegram│ │ Email │ │ Meeting │ │ Calendar │ │Search │ │   │
│  │  └────────┘ └───────┘ └─────────┘ └──────────┘ └───────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Supabase   │  │    Redis    │  │   File Storage (Local)  │  │
│  │ PostgreSQL  │  │   (Cache)   │  │    Sessions / Uploads   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Natural Language Understanding** | Parse complex requests into structured intents |
| **Dynamic Workflow Planning** | AI creates custom workflows per request (not templates) |
| **Multi-Provider AI** | Automatic fallback: Ollama → Groq → Zuki → OpenAI |
| **Real-time Updates** | WebSocket notifications for task progress |
| **Plugin Architecture** | Extensible system for adding new capabilities |
| **Self-Healing AI** | Automatic error recovery and provider switching |

### Supported Actions

| Category | Actions |
|----------|---------|
| **Communication** | Send emails, Telegram messages, notifications |
| **Meetings** | Create Jitsi/Google Meet links, schedule calls |
| **Calendar** | Check availability, create events, reminders |
| **Search** | Web search, find places, search hotels/flights |
| **Booking** | Hotel reservations, restaurant bookings |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, for full stack)
- Ollama (optional, for local AI)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and start
git clone <repo-url>
cd super-manager
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
# Grafana:  http://localhost:3001
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3: With Ollama (Free Local AI)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start Super Manager (it will auto-detect Ollama)
docker compose up -d
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# AI Providers (in priority order)
OLLAMA_BASE_URL=http://localhost:11434  # Free, local
GROQ_API_KEY=gsk_...                     # Free tier, fast
ZUKI_API_KEY=...                         # Free alternative
OPENAI_API_KEY=sk-...                    # Paid fallback

# Plugins
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
SMTP_EMAIL=your@email.com
SMTP_PASSWORD=app-password
```

### AI Provider Priority

The system tries providers in this order (configurable):

1. **Ollama** (Local) - Free, private, no API limits
2. **Groq** - Fast inference, generous free tier
3. **Zukijourney** - Free OpenAI-compatible API
4. **OpenAI** - Highest quality, paid

---

## 🤖 AI Providers

### Ollama (Recommended for Development)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Models we support
ollama pull llama3.2      # General purpose (default)
ollama pull codellama     # Code tasks
ollama pull llava         # Vision tasks
ollama pull nomic-embed-text  # Embeddings
```

### Groq (Fast & Free)

1. Get API key: https://console.groq.com
2. Set `GROQ_API_KEY` in `.env`
3. Models: `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`

### OpenAI (Quality Fallback)

1. Get API key: https://platform.openai.com
2. Set `OPENAI_API_KEY` in `.env`
3. Models: `gpt-4o-mini` (default), `gpt-4o`, `o1-mini`

---

## 🔄 Workflows

### How Dynamic Workflows Work

Unlike traditional chatbots with hardcoded flows, Super Manager uses AI to **plan workflows dynamically**:

```python
# Traditional approach (hardcoded)
if intent == "birthday_party":
    stages = [destination, hotel, activities, confirm]  # Always same

# Super Manager approach (dynamic)
workflow = ai.plan_workflow(
    user_request="Birthday party in Goa for 10 people",
    available_plugins=["email", "telegram", "meeting", "search"],
    user_preferences=get_user_history()
)
# AI might create: [clarify_date, search_venues, select_venue, 
#                   parallel(send_invites, book_venue), confirm]
```

### Workflow Stages

| Stage Type | Description |
|------------|-------------|
| `clarification` | Ask for missing information |
| `selection` | Present options for single choice |
| `multi_select` | Present options for multiple choices |
| `confirmation` | Confirm before executing actions |
| `execution` | Execute a plugin action |
| `parallel` | Execute multiple actions simultaneously |
| `conditional` | Branch based on conditions |

---

## 🔌 Plugins

### Available Plugins

| Plugin | Actions | Status |
|--------|---------|--------|
| **Telegram** | `send_message`, `send_notification` | ✅ Active |
| **Email** | `send_email`, `send_invitation` | ✅ Active |
| **Meeting** | `create_meeting` (Jitsi, Google Meet) | ✅ Active |
| **Calendar** | `schedule_event`, `check_availability` | ✅ Active |
| **Search** | `search_web`, `find_places` | 🔄 Partial |

### Creating a Custom Plugin

```python
# backend/core/my_plugin.py
from .plugins import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_plugin", "My custom plugin")
    
    async def execute(self, step: Dict, state: Dict) -> Dict:
        action = step.get("action")
        params = step.get("parameters", {})
        
        if action == "my_action":
            result = await self._do_something(params)
            return {"status": "completed", "result": result}
        
        return {"status": "failed", "error": "Unknown action"}
    
    def get_capabilities(self) -> List[str]:
        return ["my_action", "another_action"]
```

---

## 📡 API Reference

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/process` | POST | Process user message |
| `/api/agent/select` | POST | Handle option selection |
| `/api/agent/confirm` | POST | Confirm pending actions |
| `/api/task/{id}` | GET | Get task status |
| `/api/plugins/` | GET | List available plugins |
| `/ws/{user_id}` | WS | Real-time updates |

### WebSocket Events

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws/user123');

// Events you'll receive
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'task_created':
            // New task started
            break;
        case 'task_progress':
            // Progress update: data.data.progress (0-100)
            break;
        case 'stage_completed':
            // Workflow stage finished
            break;
        case 'task_completed':
            // Task finished successfully
            break;
        case 'ai_streaming':
            // Streaming AI response chunk
            break;
    }
};
```

---

## 🐳 Deployment

### Docker Compose (Production)

```bash
# Build and start all services
docker compose -f docker-compose.yml up -d

# Services:
# - backend:   Port 8000
# - frontend:  Port 3000 (nginx)
# - ollama:    Port 11434
# - redis:     Port 6379
# - prometheus: Port 9090
# - grafana:   Port 3001
```

### Cloud Deployment

The project includes:
- `Dockerfile` - Multi-stage optimized build
- `docker-compose.yml` - Full stack configuration
- `.github/workflows/ci.yml` - CI/CD pipeline
- `infrastructure/nginx.conf` - Production nginx config

### Recommended Architecture

```
                    ┌─────────────────┐
                    │   Cloudflare    │
                    │   (CDN + WAF)   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐          ┌────┴────┐          ┌────┴────┐
   │ Backend │          │ Backend │          │ Backend │
   │   #1    │          │   #2    │          │   #3    │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
         │Supabase │   │  Redis  │   │ Ollama  │
         │   DB    │   │ Cluster │   │ (GPU)   │
         └─────────┘   └─────────┘   └─────────┘
```

---

## 🛠️ Development

### Project Structure

```
super-manager/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── database_supabase.py # Supabase integration
│   ├── core/
│   │   ├── agent.py         # Main agent logic
│   │   ├── ai_providers/    # Multi-provider AI
│   │   │   ├── router.py    # Smart routing
│   │   │   ├── ollama_provider.py
│   │   │   ├── openai_provider.py
│   │   │   └── ...
│   │   ├── workflow/        # Dynamic workflows
│   │   │   └── dynamic_planner.py
│   │   ├── realtime/        # WebSocket
│   │   │   └── websocket_manager.py
│   │   └── plugins/         # Action plugins
│   │       ├── telegram_plugin.py
│   │       ├── real_email_plugin.py
│   │       └── ...
│   └── routes/              # API endpoints
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   └── ...
│   └── package.json
├── infrastructure/
│   ├── nginx.conf
│   ├── prometheus.yml
│   └── ...
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Running Tests

```bash
# Backend tests
pytest tests/ -v --cov=backend

# Lint
black backend --check
flake8 backend
```

---

## 📊 Monitoring

### Grafana Dashboards

Access Grafana at `http://localhost:3001` (admin/admin):

- **API Performance** - Request latency, error rates
- **AI Provider Stats** - Provider usage, fallback rates
- **Task Metrics** - Tasks created/completed, avg time

### Health Check

```bash
curl http://localhost:8000/api/health
# {"status":"healthy","ai_providers":["ollama","groq"],...}

curl http://localhost:8000/api/status
# Detailed system status
```

---

## 🔐 Security

### Best Practices

1. **Never commit `.env`** - Use `.env.example` as template
2. **Use Supabase RLS** - Row Level Security enabled by default
3. **Rate limiting** - Configured in nginx and FastAPI
4. **HTTPS in production** - SSL certificates via Let's Encrypt

### API Authentication (Future)

```python
# Coming soon: JWT-based auth
Authorization: Bearer <jwt_token>
```

---

## 📝 Changelog

### v2.0.0 (Current)
- ✨ Multi-provider AI routing (Ollama, Groq, Zuki, OpenAI)
- ✨ Dynamic workflow planning with AI
- ✨ WebSocket real-time updates
- ✨ Supabase PostgreSQL integration
- ✨ Docker Compose full stack
- ✨ CI/CD pipeline with GitHub Actions

### v1.0.0 (Legacy)
- Initial release with Firebase backend
- Hardcoded workflow templates
- OpenAI + Groq fallback

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

**Built with ❤️ for the future of AI assistants**
