"""
Super Manager - Main FastAPI Application
A next-generation AI agent system for intent-to-action execution

Features:
- Multi-provider AI routing (Ollama, OpenAI, Groq, Zuki)
- Dynamic workflow planning
- Real-time WebSocket updates
- Plugin architecture for extensibility
"""
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Import database - use Supabase (production)
from .database_supabase import init_db, get_db
logger.info("[DB] Using Supabase PostgreSQL")

from .routes import agent, plugins, task_agent, tasks, memory
from .core.agent import AgentManager
from .core.ai_providers import get_ai_router
from .core.realtime import get_connection_manager, websocket_endpoint

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown"""
    logger.info("=" * 60)
    logger.info("  SUPER MANAGER - Starting up...")
    logger.info("=" * 60)
    
    # Initialize database
    try:
        await init_db()
        logger.info("[DB] ✅ Database initialized")
    except Exception as e:
        logger.warning(f"[DB] ⚠️ Database initialization warning: {e}")
        logger.info("[DB] System will run in memory-only mode")
    
    # Initialize AI Router (with all providers)
    try:
        ai_router = get_ai_router()
        await ai_router.initialize()
        app.state.ai_router = ai_router
        available = ai_router.get_available_providers()
        logger.info(f"[AI] ✅ AI Router initialized. Available: {available}")
    except Exception as e:
        logger.warning(f"[AI] ⚠️ AI Router warning: {e}")
    
    # Initialize Agent Manager
    app.state.agent_manager = AgentManager()
    logger.info("[AGENT] ✅ Agent Manager initialized")
    
    # Initialize WebSocket Connection Manager
    app.state.ws_manager = get_connection_manager()
    logger.info("[WS] ✅ WebSocket Manager initialized")
    
    logger.info("=" * 60)
    logger.info("  SUPER MANAGER - Ready to serve!")
    logger.info("=" * 60)
    
    yield
    
    # Cleanup
    logger.info("[SHUTDOWN] Cleaning up resources...")

app = FastAPI(
    title="Super Manager API",
    description="""
    ## AI Agent System for Intent-to-Action Execution
    
    Super Manager is an intelligent AI assistant that:
    - Understands natural language requests
    - Plans multi-step workflows dynamically
    - Executes real-world actions (email, meetings, bookings)
    - Provides real-time progress updates
    
    ### AI Providers
    - **Ollama** (Local, Free) - Primary provider for privacy
    - **Groq** (Fast, Free tier) - Secondary fallback
    - **Zuki** (Free API) - Alternative fallback
    - **OpenAI** (Paid) - High-capability fallback
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Global exception handler
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        from datetime import datetime
        error_msg = f"[CRITICAL] Uncaught exception: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "*"),
        "https://frontend-snowy-chi-2d9q9syghe.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(task_agent.router, prefix="/api/task", tags=["task_agent"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])


# =============================================================================
# WebSocket Endpoint for Real-time Updates
# =============================================================================
@app.websocket("/ws/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time task progress updates"""
    await websocket_endpoint(websocket, user_id)


# =============================================================================
# Root & Health Endpoints
# =============================================================================
@app.get("/")
async def root():
    return {
        "message": "Super Manager API",
        "status": "operational",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    ai_router = getattr(app.state, 'ai_router', None)
    
    return {
        "status": "healthy",
        "ai_providers": ai_router.get_available_providers() if ai_router else [],
        "websocket_connections": app.state.ws_manager.get_stats() if hasattr(app.state, 'ws_manager') else {}
    }

@app.get("/api/status")
async def system_status():
    """Detailed system status"""
    ai_router = getattr(app.state, 'ai_router', None)
    
    return {
        "status": "operational",
        "version": "2.0.0",
        "ai": ai_router.get_status() if ai_router else {"error": "AI Router not initialized"},
        "features": {
            "dynamic_workflows": True,
            "real_time_updates": True,
            "multi_provider_ai": True,
            "plugin_system": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
