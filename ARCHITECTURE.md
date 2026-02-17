# Super Manager v6 - Architecture Document

**Single Source of Truth** - Last Updated: 2026-02-17

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
5. [Database Architecture](#database-architecture)
6. [Cloud Infrastructure](#cloud-infrastructure)
7. [Security Model](#security-model)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Container Architecture](#container-architecture)
10. [CDN Strategy](#cdn-strategy)
11. [Monitoring & Logging](#monitoring--logging)
12. [Backup & Recovery](#backup--recovery)
13. [User Roles & Flows](#user-roles--flows)
14. [Privacy Considerations](#privacy-considerations)
15. [v6 ToolRegistry Pattern](#v6-toolregistry-pattern)
16. [New Modules (v6)](#new-modules-v6)
17. [API Endpoint Inventory](#api-endpoint-inventory)
18. [Edge Cases](#edge-cases)

---

## System Overview

Super Manager is an AI-powered assistant that executes real actions through natural language conversations. The v6 architecture introduces a unified **ToolRegistry** adapter pattern that extends the existing AdaptiveAgent v5 system with 6 new capabilities without breaking the agent loop.

### Technology Stack

**Frontend:**
- React 18+ with Vite
- WebSocket for real-time updates
- Web Crypto API for client-side encryption
- Deployed on Vercel (free tier)

**Backend:**
- FastAPI 0.104+
- Python 3.11+
- Async/await throughout
- Deployed on Render (free tier)

**Database:**
- Supabase PostgreSQL (free tier)
- In-memory session store for fast access
- Redis for caching (optional)

**AI:**
- Groq API (free tier) - llama-3.3-70b-versatile
- OpenAI (optional)
- Ollama (local, optional)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                           │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐              │
│  │  App.jsx   │  │ HumanFallback│  │ TeachingMode  │              │
│  │  (Chat UI) │  │   Component  │  │   Component   │              │
│  └─────┬──────┘  └──────┬───────┘  └───────┬───────┘              │
│        │                 │                   │                      │
│  ┌─────▼─────────────────▼───────────────────▼──────┐              │
│  │         SecureVault (Client-Side Encryption)     │              │
│  │              AES-256-GCM via Web Crypto           │              │
│  └──────────────────────┬────────────────────────────┘              │
└─────────────────────────┼──────────────────────────────────────────┘
                          │ HTTPS / WSS
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│                         BACKEND (Render)                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                       │  │
│  │                    (backend/main.py)                         │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                          │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │                     AI Brain v5                              │  │
│  │                  (backend/core/brain.py)                     │  │
│  │  ┌──────────────────────────────────────────────────┐        │  │
│  │  │         AdaptiveAgent v5 + v6 Extensions         │        │  │
│  │  │       (backend/core/adaptive_agent.py)           │        │  │
│  │  │                                                   │        │  │
│  │  │  THINK → GENERATE → CLASSIFY → EXECUTE → OBSERVE │        │  │
│  │  └──────────────────┬───────────────────────────────┘        │  │
│  │                     │                                          │  │
│  │  ┌──────────────────▼───────────────────────────────┐        │  │
│  │  │            ToolRegistry (v6 NEW)                 │        │  │
│  │  │        (backend/core/tool_registry.py)           │        │  │
│  │  │                                                   │        │  │
│  │  │  • Unified tool interface                        │        │  │
│  │  │  • Dynamic tool registration                     │        │  │
│  │  │  • Risk classification                           │        │  │
│  │  │  • Source tagging (primitive/mcp/stealth/etc)    │        │  │
│  │  └──────────┬────────────────────────────────────┬──┘        │  │
│  │             │                                     │           │  │
│  │  ┌──────────▼──────────┐           ┌─────────────▼───────┐  │  │
│  │  │  6 Core Primitives  │           │   v6 New Tools      │  │  │
│  │  │  (primitives.py)    │           │                     │  │  │
│  │  │                     │           │  • payment_links    │  │  │
│  │  │  • web_search       │           │  • stealth_browser  │  │  │
│  │  │  • browse_page      │           │  • human_fallback   │  │  │
│  │  │  • scrape_data      │           │  • mcp_client       │  │  │
│  │  │  • generate_image   │           │  • teaching_mode    │  │  │
│  │  │  • fill_form        │           │  • workflow_*       │  │  │
│  │  │  • run_python       │           │  • mcp__*__*        │  │  │
│  │  └─────────────────────┘           └─────────────────────┘  │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │          Sandbox Executor                              │  │  │
│  │  │        (backend/core/sandbox.py)                       │  │  │
│  │  │                                                         │  │  │
│  │  │  • RiskClassifier: safe/risky/blocked                  │  │  │
│  │  │  • Restricted globals (no file/network)                │  │  │
│  │  │  • 30-second timeout enforcement                       │  │  │
│  │  │  • Consults ToolRegistry for dynamic tools             │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Routes (backend/routes/)                  │  │
│  │                                                               │  │
│  │  • api.py - Main chat endpoint + fallback-complete          │  │
│  │  • streaming.py - SSE streaming                             │  │
│  │  • tasks.py, agent.py, memory.py, plugins.py               │  │
│  │  • NEW: MCP endpoints (GET/POST /api/mcp/servers)           │  │
│  │  • NEW: Teaching endpoints (POST /api/teach/*)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│                    DATABASE (Supabase)                             │
│                                                                     │
│  • PostgreSQL (free tier)                                          │
│  • Session storage                                                 │
│  • User data & preferences                                         │
│  • Feedback history                                                │
│  • Strategy cache                                                  │
│  • Workflow definitions                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Components

**Core:**
- `App.jsx` - Main chat interface, message history, input handling
- `useStreamingChat.js` - Custom hook for SSE streaming

**v6 New Components:**
- `HumanFallback.jsx` - Manual task completion interface
- `TeachingMode.jsx` - Workflow recording UI
- `SecureInput.jsx` - Encrypted credential input overlay

**v6 New Utilities:**
- `secureVault.js` - Client-side encryption (AES-256-GCM)
- `useActionRecorder.js` - Browser action capture for teaching mode

### State Management

- React useState/useEffect hooks
- No Redux (keeping it simple)
- WebSocket connection managed in useStreamingChat

### Communication

**REST API:**
- `POST /api/chat` - Send user messages
- `POST /api/chat/fallback-complete` - Resume after human fallback
- `GET /api/mcp/servers` - List MCP servers
- `POST /api/mcp/servers` - Add MCP server
- `POST /api/teach/start` - Start workflow recording
- `GET /api/teach/workflows` - List saved workflows

**WebSocket:**
- `/ws/{user_id}` - Real-time agent events
- Event types: thinking, action, code_exec, action_result, answer, ask, confirm_needed, human_fallback, step_progress, error

---

## Backend Architecture

### Core Flow

1. **User Input** → `POST /api/chat`
2. **AI Brain** → `brain.py` routes to AdaptiveAgent
3. **AdaptiveAgent Loop:**
   - THINK: Call Groq LLM
   - GENERATE: Parse XML tags (think/action/code/ask/answer)
   - CLASSIFY: RiskClassifier determines safe/risky/blocked
   - EXECUTE: SandboxExecutor runs code or calls primitives via ToolRegistry
   - OBSERVE: Results fed back to LLM
   - ADAPT: If error, LLM tries alternative approach
4. **Result** → Streamed back as SSE events

### Key Modules

**backend/core/brain.py**
- Session management (in-memory + Supabase)
- Confirmation flow (yes/no handling)
- Feedback system (red/green ratings)
- Strategy caching

**backend/core/adaptive_agent.py**
- Main AI agent loop
- System prompt building (now uses ToolRegistry.get_prompt_section())
- LLM communication (Groq API)
- Event streaming

**backend/core/sandbox.py**
- RiskClassifier: Static analysis of code for forbidden patterns
- SandboxExecutor: Restricted Python execution
- Now consults ToolRegistry for dynamically registered tools

**backend/core/primitives.py**
- 6 core primitives (unchanged)
- PRIMITIVES dict (unchanged)
- get_primitives_prompt() function (unchanged)

**backend/core/tool_registry.py** *(v6 NEW)*
- ToolDef dataclass: name, description, parameters, risk_level, source, handler
- ToolRegistry class: register, unregister, get, list_tools, get_prompt_section, execute
- Auto-registers all 6 primitives on init
- Adapter pattern: wraps existing primitives without modifying them

### Tool Sources

1. **primitive** - Core 6 primitives from primitives.py
2. **mcp** - Tools from MCP servers (naming: mcp__{server}__{tool})
3. **stealth** - Stealth browser tools
4. **payment** - Payment link generation tools
5. **workflow** - User-taught workflows (naming: workflow__{name})
6. **fallback** - Human fallback trigger

---

## Database Architecture

### Schema (Supabase PostgreSQL)

**sessions**
- id (uuid, primary key)
- user_id (text)
- created_at (timestamp)
- updated_at (timestamp)
- messages (jsonb)
- user_data (jsonb)
- pending_confirmation (jsonb, nullable)

**feedback**
- id (uuid, primary key)
- user_id (text)
- session_id (text)
- message_id (text)
- rating (text) - "positive" or "negative"
- context (jsonb)
- created_at (timestamp)

**strategies**
- id (uuid, primary key)
- task_type (text)
- keywords (text[])
- steps (jsonb)
- success_count (integer)
- created_at (timestamp)

**workflows** *(v6 NEW)*
- id (uuid, primary key)
- user_id (text)
- name (text)
- description (text)
- steps (jsonb) - Array of WorkflowStep
- parameters (text[]) - Variable placeholders
- created_at (timestamp)

**mcp_servers** *(v6 NEW)*
- id (uuid, primary key)
- user_id (text)
- name (text)
- config (jsonb) - MCPServerConfig
- enabled (boolean)
- created_at (timestamp)

### In-Memory Cache

- Session store for fast access (backend/core/session_store.py)
- Strategy cache (backend/core/strategy_store.py)
- Cleared on restart, synced with Supabase periodically

---

## Cloud Infrastructure

### Hosting

**Frontend: Vercel**
- Auto-deploy from `main` branch
- Custom domain support
- Edge caching for static assets
- Environment variables: `VITE_API_URL`, `VITE_WS_URL`

**Backend: Render**
- Auto-deploy from `main` branch
- Free tier (750 hours/month)
- Environment variables:
  - GROQ_API_KEY (required)
  - SUPABASE_URL, SUPABASE_KEY
  - SECRET_KEY
  - STRIPE_SECRET_KEY (optional)
  - RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (optional)
  - TELEGRAM_BOT_TOKEN (optional)

**Database: Supabase**
- Free tier (500 MB database, 1 GB file storage)
- PostgreSQL 15
- Built-in Auth (not currently used)
- REST API + real-time subscriptions (not currently used)

### Networking

- HTTPS enforced on all connections
- CORS enabled for frontend origin
- WebSocket over WSS (secure)
- No direct database access from frontend

---

## Security Model

### Sandbox Execution

**Static Analysis (RiskClassifier):**
- Forbidden patterns: import os, subprocess, eval, exec, open, requests, etc.
- Risk levels: safe, risky, blocked
- Consults ToolRegistry for dynamically registered tools

**Runtime Restrictions:**
- No file system access
- No network access (except through primitives)
- 30-second timeout
- Restricted builtins (no eval, exec, compile, __import__)
- Only safe modules: json, re, math, datetime, urlparse

**User Confirmation:**
- Risky primitives (fill_form, run_python) always require confirmation
- Risky MCP tools (write operations) require confirmation
- User can say "yes", "no", or ask questions

### Risk Classification for Tools

**SAFE (auto-execute):**
- Read-only operations (web_search, browse_page, scrape_data, generate_image)
- MCP list/get/search operations
- Stealth browse/screenshot

**RISKY (confirmation required):**
- Write operations (fill_form, run_python)
- MCP create/update/delete/send operations
- Stealth form filling
- Payment link generation

**BLOCKED:**
- Unknown primitives
- Code with forbidden patterns
- MCP exec/run/install operations

### Input Validation

- URL validation (http/https only)
- UPI format validation (regex)
- Email format validation
- JSON schema validation for API requests
- XSS protection (sanitize HTML)

### Rate Limiting

- Per-user rate limits (environment-configurable)
- Groq API rate limit handling (retry on 429)
- WebSocket connection limits

---

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/`)

**ci.yml** - Continuous Integration
```yaml
triggers:
  - push to main
  - pull requests

steps:
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies (pip install -r requirements.txt)
  4. Run linters (flake8, black --check)
  5. Run tests (pytest tests/ -v)
  6. Build Docker image
  7. Push to registry (if main branch)
```

**deploy.yml** - Continuous Deployment
```yaml
triggers:
  - push to main (after CI passes)

steps:
  1. Deploy backend to Render (auto)
  2. Deploy frontend to Vercel (auto)
  3. Run smoke tests against production
  4. Notify on Telegram (optional)
```

### Testing Strategy

**Unit Tests:**
- Core modules (primitives, sandbox, adaptive_agent)
- New modules (tool_registry, payment_links, stealth_browser, etc.)
- Test doubles for external APIs

**Integration Tests:**
- Full agent flow (user message → answer)
- WebSocket streaming
- Database operations

**Smoke Tests:**
- Health endpoint
- Basic API functionality
- Import validation

---

## Container Architecture

### Docker

**Dockerfile** (multi-stage build)
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend ./backend
COPY start.py .
CMD ["python", "start.py"]
```

**docker-compose.yml**
```yaml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      VITE_API_URL: http://localhost:8000

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  # Optional: Local LLM
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    profiles: [local-llm]

  # Optional: Monitoring
  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]
    volumes: ["./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml"]
    profiles: [monitoring]

  grafana:
    image: grafana/grafana
    ports: ["3001:3000"]
    profiles: [monitoring]
```

---

## CDN Strategy

### Static Assets

**Vercel Edge Network:**
- Automatic CDN for frontend static files
- Gzip/Brotli compression
- Edge caching with cache-control headers

**Image URLs:**
- Pollinations AI (https://image.pollinations.ai) - External CDN
- QR codes (https://api.qrserver.com) - External service

### Caching Headers

- HTML: no-cache (always revalidate)
- JS/CSS: immutable, 1 year
- Images: max-age=86400 (1 day)
- API responses: no-cache

---

## Monitoring & Logging

### Metrics (Prometheus)

**System Metrics:**
- CPU usage (psutil)
- Memory usage (psutil)
- Disk I/O (psutil)
- Network I/O (psutil)

**Application Metrics:**
- Request count (by endpoint)
- Response time (p50, p95, p99)
- Error rate
- Active WebSocket connections
- Groq API calls (count, latency)
- Sandbox execution time

**Business Metrics:**
- Messages processed
- Agent steps per request
- Confirmation rate (yes/no)
- Feedback rating (positive/negative)

### Logging

**Python logging module:**
- DEBUG: Detailed diagnostic info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

**Log Destinations:**
- stdout/stderr (captured by Render)
- Optional: Sentry for error tracking
- Optional: CloudWatch/Datadog

**Log Format:**
```
[%(asctime)s] %(levelname)s [%(name)s] %(message)s
```

### Grafana Dashboards

- System health overview
- API performance
- Agent execution metrics
- Error rate trends

---

## Backup & Recovery

### Database Backups

**Supabase Automatic Backups:**
- Daily backups (retained for 7 days on free tier)
- Point-in-time recovery (PITR) available on paid tier

**Manual Exports:**
- Weekly manual exports to S3/Backblaze B2
- SQL dump via pg_dump

### Strategy Cache

- Periodically synced to Supabase
- Can be rebuilt from database on restart

### Disaster Recovery

1. **Backend Down:**
   - Redeploy on Render
   - Sessions in Supabase persist
   - In-memory cache rebuilt

2. **Database Down:**
   - Agent continues with in-memory sessions
   - No persistent history
   - Restore from backup when DB recovers

3. **Total Failure:**
   - Restore from latest backup
   - Replay recent transactions (if logging enabled)
   - Notify users of potential data loss

---

## User Roles & Flows

### Anonymous User

**Can:**
- Use chat interface (limited session)
- Get answers to questions
- Search web, browse pages
- Generate images

**Cannot:**
- Save conversation history (persists for session only)
- Access email/calendar integrations
- Use payment features
- Save workflows

**Flow:**
1. Visit site
2. Type message in chat
3. Agent responds with answer or action
4. Session expires after 30 minutes of inactivity

### Authenticated User

**Can:**
- All anonymous features
- Save conversation history
- Access email/calendar integrations (with OAuth)
- Generate payment links
- Teach and save workflows
- Connect MCP servers
- Use secure vault for credentials

**Flow:**
1. Log in (OAuth or email/password)
2. Full access to all features
3. Persistent session across devices
4. Encrypted credential storage (client-side)

### Admin

**Can:**
- All authenticated features
- View system metrics
- Manage MCP server configs
- View feedback data
- Trigger backups

**Flow:**
1. Log in with admin role
2. Access admin dashboard
3. Monitor system health
4. Manage configurations

---

## Privacy Considerations

### Client-Side Vault

**SecureVault (v6):**
- Master key derived from user passphrase (PBKDF2, 100k iterations)
- AES-256-GCM encryption via Web Crypto API
- Keys never leave the browser
- Encrypted data stored in localStorage
- Used for: API keys, passwords, tokens, UPI IDs

**Security:**
- Master key never sent to server
- Encrypted blobs are opaque to server
- User responsible for passphrase
- No key recovery if passphrase lost

### Data Collection

**Collected:**
- Chat messages (for AI processing)
- Feedback ratings (for improvement)
- Usage metrics (anonymized)
- Error logs (no PII)

**Not Collected:**
- Passwords or API keys (stay in SecureVault)
- Payment details (handled by UPI/Stripe/Razorpay)
- Personal emails (OAuth refresh tokens stored encrypted)

### Compliance

- GDPR: Right to access, delete, export data
- CCPA: Opt-out of data sale (we don't sell data)
- Data retention: 90 days for messages, 1 year for feedback

---

## v6 ToolRegistry Pattern

### Design

The ToolRegistry is an **adapter pattern** that wraps existing primitives without modifying them. It provides:

1. **Unified Interface:** All tools (primitives, MCP, stealth, workflows) accessible via single registry
2. **Dynamic Registration:** Tools can be added/removed at runtime
3. **Risk Classification:** Centralized risk checking (safe/risky/blocked)
4. **Source Tagging:** Track where tools come from (primitive/mcp/stealth/payment/workflow)
5. **Backward Compatibility:** Existing primitives.py untouched

### ToolDef Structure

```python
@dataclass
class ToolDef:
    name: str                    # e.g. "web_search", "mcp__github__create_issue"
    description: str
    parameters: Dict[str, Any]   # JSON Schema for params
    risk_level: str              # "safe", "risky", "blocked"
    source: str                  # "primitive", "mcp", "stealth", "payment", "workflow"
    handler: Callable            # async function to call
```

### Initialization

On startup, ToolRegistry:
1. Registers all 6 primitives from PRIMITIVES dict
2. Registers payment tools (if env vars present)
3. Registers stealth browser tools
4. Registers human_fallback tool
5. Connects to MCP servers (if configured)
6. Loads saved workflows from database

### Execution Flow

```python
# Agent calls ToolRegistry
result = await registry.execute(name="web_search", params={"query": "test"}, context={})

# ToolRegistry routes to handler
tool = registry.get(name="web_search")
if tool:
    return await tool.handler(**params)
else:
    # Fall back to sandbox.execute_action() for primitives
    return await sandbox.execute_action(name, params, context)
```

---

## New Modules (v6)

### 1. ToolRegistry (backend/core/tool_registry.py)

**Purpose:** Unified tool management system

**Classes:**
- ToolDef: Dataclass for tool definition
- ToolRegistry: Tool CRUD + execution router

**Methods:**
- register(tool: ToolDef) - Add new tool
- unregister(name: str) - Remove tool
- get(name: str) -> Optional[ToolDef] - Get tool by name
- list_tools(source: str = None) -> List[ToolDef] - List all tools
- get_prompt_section() -> str - Generate tool docs for system prompt
- execute(name: str, params: Dict, context: Dict) -> PrimitiveResult - Execute tool

**Integration:**
- Called by adaptive_agent.py to build system prompt
- Called by sandbox.py for risk classification
- Auto-registers primitives on init

### 2. Payment Links (backend/core/payment_links.py)

**Purpose:** 3-tier payment link generation

**Tiers:**
1. UPI Deep Links (FREE) - INR payments via UPI
2. Stripe Payment Links (optional) - International payments
3. Razorpay (existing) - Fallback for India

**Functions:**
- generate_upi_link(amount, vpa, note) -> Dict
- generate_stripe_link(amount, currency, description) -> Dict (if STRIPE_SECRET_KEY)
- generate_razorpay_link(amount, currency, description) -> Dict (if RAZORPAY_KEY_ID)
- generate_payment_link(amount, currency, payee, description) -> PrimitiveResult (main)

**QR Code:**
- URL: https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={upi_link}

**Registration:**
- Tool: generate_payment_link (risk: risky)

### 3. Stealth Browser (backend/core/stealth_browser.py)

**Purpose:** Anti-detection browser automation

**Classes:**
- StealthBrowser: Browser lifecycle + stealth features

**Methods:**
- launch() -> BrowserContext - Launch with anti-detect
- navigate(url: str) -> str - Visit page, return text
- fill_form(url: str, fields: Dict, submit: bool) -> PrimitiveResult - Fill form
- screenshot() -> bytes - Take screenshot
- detect_captcha(page) -> bool - Detect CAPTCHA challenges
- close() - Cleanup

**Launch Priority:**
1. Camoufox (AsyncCamoufox) - Best anti-detect
2. playwright-stealth - Stealth plugin for Playwright
3. Plain Playwright - Fallback

**CAPTCHA Handling:**
- Detect patterns: reCAPTCHA iframe, hCaptcha div, Cloudflare challenge, Turnstile
- If detected: trigger human_fallback instead of solving
- Log encounter

**Registration:**
- stealth_browse(url) - SAFE
- stealth_fill_form(url, fields, submit) - RISKY
- stealth_screenshot(url) - SAFE

### 4. Human Fallback (backend/core/human_fallback.py)

**Purpose:** Pause agent, let user complete manual steps

**Classes:**
- FallbackContext: Context for fallback request

**Functions:**
- trigger_fallback(context: FallbackContext) -> PrimitiveResult

**FallbackContext Fields:**
- reason: "captcha_detected", "login_required", "complex_form"
- task_description: What the agent was trying to do
- completed_steps: What's already done
- remaining_steps: What needs manual completion
- prefilled_data: Form data to pre-fill
- screenshot_url: Optional screenshot for reference
- resume_data: Data to resume agent after completion

**Frontend Component (HumanFallback.jsx):**
- Renders "Manual Steps Required" panel
- Shows reason, completed steps, remaining steps (checkboxes)
- Pre-filled data display
- "I've completed these steps" button → POST /api/chat/fallback-complete

**Integration:**
- adaptive_agent.py: Add human_fallback event type
- brain.py: Handle human_fallback events
- api.py: Add POST /api/chat/fallback-complete endpoint

**Registration:**
- human_fallback(reason, remaining_steps, prefilled_data) - SAFE

### 5. MCP Client (backend/core/mcp_client.py)

**Purpose:** Connect to MCP (Model Context Protocol) servers

**Classes:**
- MCPClientManager: Manage multiple MCP connections

**Methods:**
- connect_server(name: str, config: MCPServerConfig) - Connect to server
- disconnect_server(name: str) - Disconnect
- discover_tools(server_name: str) -> List[ToolDef] - List server tools
- call_tool(server_name: str, tool_name: str, args: Dict) -> Any - Execute tool
- get_connected_servers() -> List[str] - List active connections

**Tool Naming:** mcp__{server}__{tool}
- Example: mcp__github__create_issue

**Risk Classification:**
- Read-only (list, get, search) → safe
- Write (create, update, delete, send) → risky
- System (exec, run, install) → blocked

**Config File (backend/mcp_servers.json):**
```json
{
  "servers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "from_env"
      }
    }
  }
}
```

**Integration:**
- brain.py: Initialize MCPClientManager on startup (lazy)
- api.py: GET /api/mcp/servers, POST /api/mcp/servers

**Dependencies:**
- mcp[cli]>=1.0.0

### 6. Teaching Mode (backend/core/teaching_mode.py)

**Purpose:** Record user actions, create reusable workflows

**Classes:**
- WorkflowStep: Single action in workflow
- WorkflowDef: Complete workflow definition
- TeachingMode: Recording + replay logic

**Methods:**
- start_recording(session_id: str) -> Dict - Begin recording
- stop_recording(session_id: str, actions: List[Dict]) -> Dict - Stop, save actions
- analyze_recording(actions: List[Dict]) -> WorkflowDef - Extract workflow
- save_workflow(name: str, workflow: WorkflowDef) - Persist workflow
- replay_workflow(name: str, params: Dict) -> PrimitiveResult - Execute workflow

**WorkflowStep:**
- action: "navigate", "click", "fill", "wait", "screenshot"
- selector: CSS selector (if applicable)
- value: Value to fill (if applicable)
- wait_ms: Wait duration

**WorkflowDef:**
- name: Workflow name
- description: What it does
- steps: List[WorkflowStep]
- parameters: Variable placeholders (e.g., {{email}}, {{name}})

**Frontend:**
- TeachingMode.jsx: Recording indicator, action log, done button
- useActionRecorder.js: Inject JS to capture user actions in iframe

**Registration:**
- workflow__{name} - Risk based on workflow steps

**API Endpoints:**
- POST /api/teach/start
- POST /api/teach/record
- GET /api/teach/workflows

### 7. Secure Vault (frontend/src/utils/secureVault.js)

**Purpose:** Client-side credential encryption

**Classes:**
- SecureVault: Encryption + localStorage

**Methods:**
- constructor(masterKey) - Derive key from passphrase (PBKDF2)
- encrypt(data) -> ciphertext - AES-256-GCM encryption
- decrypt(ciphertext) -> data - Decryption
- store(key, value) - Encrypt + save to localStorage
- retrieve(key) -> value - Decrypt from localStorage
- listKeys() -> List[str] - List stored keys
- clear() - Delete all stored data

**Key Derivation:**
- Algorithm: PBKDF2
- Iterations: 100,000
- Hash: SHA-256
- Salt: Random 16 bytes (stored with key)

**Encryption:**
- Algorithm: AES-256-GCM
- IV: Random 12 bytes (stored with ciphertext)
- Tag: 128 bits

**Storage Format:**
```json
{
  "salt": "base64...",
  "iv": "base64...",
  "ciphertext": "base64...",
  "tag": "base64..."
}
```

**Frontend Component (SecureInput.jsx):**
- Encrypted input overlay
- Appears when agent asks for credentials
- User enters value → encrypted → sent to agent
- Agent never sees plaintext

**Integration:**
- App.jsx: Initialize SecureVault with user passphrase
- Import HumanFallback, TeachingMode, SecureInput components

---

## API Endpoint Inventory

### Existing Endpoints

**Core:**
- GET / - Welcome message
- GET /api/health - Health check
- GET /api/status - System status
- GET /api/metrics - Performance metrics
- GET /api/docs - API documentation (Swagger)

**Chat:**
- POST /api/chat - Main chat endpoint
- GET /api/chat/history - Get conversation history
- POST /api/chat/feedback - Submit feedback (red/green)
- POST /api/chat/confirm - Confirm pending action (yes/no)

**Streaming:**
- POST /api/stream/chat - SSE streaming chat
- GET /api/stream/status - Stream status

**Tasks:**
- GET /api/tasks - List tasks
- POST /api/tasks - Create task
- GET /api/tasks/{id} - Get task details
- PUT /api/tasks/{id} - Update task
- DELETE /api/tasks/{id} - Delete task

**Agent:**
- POST /api/agent/execute - Execute agent command
- GET /api/agent/status - Agent status

**Memory:**
- GET /api/memory - Get user memory
- POST /api/memory - Store memory
- DELETE /api/memory/{key} - Delete memory

**Plugins:**
- GET /api/plugins - List plugins
- POST /api/plugins/{name}/enable - Enable plugin
- POST /api/plugins/{name}/disable - Disable plugin

**WebSocket:**
- WS /ws/{user_id} - Real-time updates

### v6 New Endpoints

**MCP:**
- GET /api/mcp/servers - List connected MCP servers
- POST /api/mcp/servers - Connect to MCP server
- DELETE /api/mcp/servers/{name} - Disconnect MCP server
- GET /api/mcp/servers/{name}/tools - List tools from server

**Teaching:**
- POST /api/teach/start - Start workflow recording
- POST /api/teach/stop - Stop recording
- POST /api/teach/record - Record action
- GET /api/teach/workflows - List saved workflows
- POST /api/teach/workflows/{name}/replay - Replay workflow
- DELETE /api/teach/workflows/{name} - Delete workflow

**Human Fallback:**
- POST /api/chat/fallback-complete - Resume after manual steps

---

## Edge Cases

### Agent Execution

**Max Steps Reached:**
- After 15 steps, agent stops
- Returns summary of progress so far
- User can ask to continue

**Timeout:**
- Sandbox execution: 30 seconds per step
- LLM call: 30 seconds
- If timeout, return partial results + error

**Rate Limit (Groq):**
- Retry once after 2-second delay
- If still fails, return error to user

**Invalid JSON:**
- If LLM outputs malformed JSON in <action> or <ask>
- Agent treats as error, retries with corrected format

**Missing Primitive:**
- If LLM calls unknown primitive
- Error: "Unknown primitive: {name}. Available: {list}"
- Agent retries with correct primitive

### Primitives

**web_search:**
- No results: Return "No results found for '{query}'"
- DuckDuckGo down: Return error, suggest manual search

**browse_page:**
- Page not found (404): Return "Page not found: {url}"
- Timeout: Return "Failed to load page (timeout)"
- JavaScript error: Fall back to httpx

**scrape_data:**
- CAPTCHA: Trigger human_fallback
- Cloudflare challenge: Trigger stealth_browser or human_fallback

**generate_image:**
- Pollinations down: Return error
- Invalid prompt: Return "Image generation failed"

**fill_form:**
- Form not found: Return "Form not found on {url}"
- Selector not found: Return "Field {selector} not found"
- Submit button not found: Return "Submit button not found"

**run_python:**
- Forbidden import: Blocked by RiskClassifier
- Syntax error: Return error with line number
- Runtime error: Return error + partial output

### Payment Links

**UPI:**
- Invalid UPI ID format: Return error
- Amount <= 0: Return error
- QR code service down: Return UPI link only (no QR)

**Stripe:**
- STRIPE_SECRET_KEY not set: Skip Stripe, try Razorpay
- Stripe API error: Return error message

**Razorpay:**
- Keys not set: Return UPI-only link
- API error: Return error message

### Stealth Browser

**Camoufox not installed:**
- Fall back to playwright-stealth
- Log warning

**playwright-stealth not installed:**
- Fall back to plain Playwright
- Log warning

**Playwright not installed:**
- Return error: "Playwright not installed"

**CAPTCHA detected:**
- Trigger human_fallback with screenshot
- Resume after user completes manually

### Human Fallback

**User never completes:**
- Session expires after 30 minutes
- User can restart task

**User completes wrong steps:**
- Agent validates completion
- If invalid, ask user to retry

**Screenshot unavailable:**
- Fallback UI shows text instructions only

### MCP Client

**Server not responding:**
- Disconnect after 10 seconds
- Return error: "MCP server {name} not responding"

**Tool not found:**
- Return error: "Tool {tool} not found on server {server}"

**Server crashed:**
- Auto-reconnect on next tool call
- Log error

### Teaching Mode

**Recording never stopped:**
- Auto-stop after 10 minutes
- Save partial workflow

**Empty workflow:**
- Return error: "No actions recorded"

**Replay fails:**
- Return error with step that failed
- User can modify workflow

### Secure Vault

**Wrong passphrase:**
- Decryption fails
- User must enter correct passphrase

**localStorage full:**
- Return error: "Storage quota exceeded"
- User must delete old keys

**Browser doesn't support Web Crypto:**
- Return error: "Secure vault not supported in this browser"
- Fallback to plaintext warning

### Database

**Supabase down:**
- Agent continues with in-memory sessions
- No persistent history
- Log error

**Connection lost mid-request:**
- Retry once
- If fails, return error

**Schema migration:**
- Graceful migration with backward compatibility
- Old sessions continue working

---

## Future Enhancements

### Planned Features

1. **Voice Input/Output** - Speech-to-text and text-to-speech
2. **Multi-Agent Collaboration** - Multiple agents working together
3. **Custom Tool Marketplace** - User-shared workflows and tools
4. **Mobile App** - Native iOS/Android apps
5. **Plugin Ecosystem** - Third-party integrations
6. **Advanced Analytics** - User behavior insights
7. **A/B Testing** - Test different prompts and strategies
8. **Webhooks** - Notify external systems on events
9. **Scheduled Tasks** - Cron-like task execution
10. **RAG Integration** - Document-based knowledge retrieval

### Scalability Considerations

**Current Limits (Free Tier):**
- Render: 512 MB RAM, 0.1 CPU
- Supabase: 500 MB database, 50k rows
- Groq: Rate limited (requests per minute)

**Scaling Strategy:**
- Horizontal scaling: Multiple backend instances behind load balancer
- Database: Upgrade to Supabase Pro or self-hosted PostgreSQL
- Caching: Redis for session store and strategy cache
- Queue: Celery for background tasks
- CDN: CloudFront or Cloudflare for assets

---

## Conclusion

Super Manager v6 introduces a powerful, extensible architecture that maintains backward compatibility while adding 6 new capabilities. The ToolRegistry adapter pattern allows seamless integration of new tools without modifying existing code. The system is production-ready, secure, and scalable.

**Key Achievements:**
- ✅ No breaking changes to existing system
- ✅ Unified tool management via ToolRegistry
- ✅ Enhanced payment capabilities (3-tier)
- ✅ Anti-detection browser automation
- ✅ Human-in-the-loop fallback system
- ✅ MCP server integration
- ✅ User-taught workflows
- ✅ Client-side encryption for credentials

**Next Steps:**
- Deploy v6 to staging environment
- Run integration tests
- Gather user feedback
- Iterate and improve

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-17  
**Maintainer:** Super Manager Team
