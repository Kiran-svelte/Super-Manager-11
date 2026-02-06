"""
Super Manager - Main FastAPI Application
A next-generation AI agent system for intent-to-action execution

Features:
- Multi-provider AI routing (Ollama, OpenAI, Groq, Zuki)
- Dynamic workflow planning
- Real-time WebSocket updates
- Plugin architecture for extensibility
- Enterprise-grade performance optimizations
- Security hardening
- Structured logging
"""
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys
import time
from dotenv import load_dotenv

# Load environment early
load_dotenv()

# Import and setup structured logging FIRST
from .core.logging_config import (
    setup_logging, LogConfig, get_logger, 
    perf_logger, audit_logger, LogContext, timed
)

# Configure logging based on environment
log_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "").lower() == "json",
    log_file=os.getenv("LOG_FILE")
)
setup_logging(log_config)
logger = get_logger(__name__)

# Import performance and security modules
from .core.performance import (
    ai_circuit_breaker, db_circuit_breaker, email_circuit_breaker,
    response_cache, api_rate_limiter, health_monitor,
    RequestTracer
)
from .core.security import setup_security_middleware

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

# Initialize request tracer
request_tracer = RequestTracer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown"""
    startup_start = time.time()
    logger.info("=" * 60)
    logger.info("  SUPER MANAGER - Starting up...")
    logger.info("=" * 60)
    
    # Register health monitor components
    health_monitor.register_component("database")
    health_monitor.register_component("ai_router")
    health_monitor.register_component("websocket")
    
    # Initialize database
    try:
        await init_db()
        health_monitor.update_health("database", True)
        logger.info("[DB] ✅ Database initialized")
    except Exception as e:
        health_monitor.update_health("database", False, str(e))
        logger.warning(f"[DB] ⚠️ Database initialization warning: {e}")
        logger.info("[DB] System will run in memory-only mode")
    
    # Initialize AI Router (with all providers)
    try:
        ai_router = get_ai_router()
        await ai_router.initialize()
        app.state.ai_router = ai_router
        available = ai_router.get_available_providers()
        health_monitor.update_health("ai_router", True, metadata={"providers": available})
        logger.info(f"[AI] ✅ AI Router initialized. Available: {available}")
    except Exception as e:
        health_monitor.update_health("ai_router", False, str(e))
        logger.warning(f"[AI] ⚠️ AI Router warning: {e}")
    
    # Initialize Agent Manager
    app.state.agent_manager = AgentManager()
    logger.info("[AGENT] ✅ Agent Manager initialized")
    
    # Initialize WebSocket Connection Manager
    app.state.ws_manager = get_connection_manager()
    health_monitor.update_health("websocket", True)
    logger.info("[WS] ✅ WebSocket Manager initialized")
    
    # Store performance utilities in app state
    app.state.request_tracer = request_tracer
    app.state.health_monitor = health_monitor
    
    startup_duration = (time.time() - startup_start) * 1000
    perf_logger.log_duration("startup", startup_duration)
    
    logger.info("=" * 60)
    logger.info(f"  SUPER MANAGER - Ready in {startup_duration:.0f}ms!")
    logger.info("=" * 60)
    
    yield
    
    # Cleanup
    logger.info("[SHUTDOWN] Cleaning up resources...")
    audit_logger.log_security_event("shutdown", "low", "Application shutting down")

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
    
    ### Security Features
    - Rate limiting (1000 requests/minute)
    - Input validation and sanitization
    - Security headers (CSP, HSTS, X-Frame-Options)
    - Request ID tracking
    
    ### Performance Features
    - Circuit breaker for external services
    - Response caching (5 minute TTL)
    - Request tracing with percentiles (p50, p90, p95, p99)
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup security middleware (headers, rate limiting, logging)
setup_security_middleware(app)

# Performance tracking middleware
@app.middleware("http")
async def performance_tracking_middleware(request: Request, call_next):
    """Track request performance metrics"""
    start_time = time.time()
    operation = f"{request.method} {request.url.path}"
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    request_tracer.record_duration(operation, duration_ms)
    
    # Add performance header
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    return response

# Global exception handler
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        error_msg = f"[CRITICAL] Uncaught exception: {e}\n{traceback.format_exc()}"
        logger.error(error_msg, exc_info=True)
        audit_logger.log_security_event(
            "error", "high", 
            f"Unhandled exception: {type(e).__name__}",
            path=str(request.url.path)
        )
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
    tracer = getattr(app.state, 'request_tracer', None)
    monitor = getattr(app.state, 'health_monitor', None)
    
    # Get circuit breaker states
    circuit_status = {
        "ai": ai_circuit_breaker.state.name if ai_circuit_breaker else "unknown",
        "database": db_circuit_breaker.state.name if db_circuit_breaker else "unknown",
        "email": email_circuit_breaker.state.name if email_circuit_breaker else "unknown"
    }
    
    # Get performance metrics
    perf_metrics = tracer.get_stats() if tracer else {}
    
    # Get cache stats
    cache_stats = response_cache.get_stats() if response_cache else {}
    
    # Check overall health
    component_health = monitor.get_overall_health() if monitor else {}
    all_healthy = component_health.get("healthy", False) if isinstance(component_health, dict) else True
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "ai_providers": ai_router.get_available_providers() if ai_router else [],
        "websocket_connections": app.state.ws_manager.get_stats() if hasattr(app.state, 'ws_manager') else {},
        "circuit_breakers": circuit_status,
        "performance": perf_metrics,
        "cache": cache_stats,
        "components": component_health
    }

@app.get("/api/status")
async def system_status():
    """Detailed system status"""
    ai_router = getattr(app.state, 'ai_router', None)
    monitor = getattr(app.state, 'health_monitor', None)
    
    return {
        "status": "operational",
        "version": "2.0.0",
        "ai": ai_router.get_status() if ai_router else {"error": "AI Router not initialized"},
        "features": {
            "dynamic_workflows": True,
            "real_time_updates": True,
            "multi_provider_ai": True,
            "plugin_system": True,
            "circuit_breakers": True,
            "response_caching": True,
            "rate_limiting": True,
            "security_headers": True,
            "structured_logging": True
        },
        "health": monitor.get_overall_health() if monitor else {}
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get detailed performance metrics"""
    tracer = getattr(app.state, 'request_tracer', None)
    
    metrics = {
        "cache": response_cache.get_stats() if response_cache else {},
        "rate_limiter": api_rate_limiter.get_stats() if api_rate_limiter else {},
        "circuit_breakers": {
            "ai": {
                "state": ai_circuit_breaker.state.name,
                "failures": ai_circuit_breaker._failure_count
            } if ai_circuit_breaker else {},
            "database": {
                "state": db_circuit_breaker.state.name,
                "failures": db_circuit_breaker._failure_count
            } if db_circuit_breaker else {},
            "email": {
                "state": email_circuit_breaker.state.name,
                "failures": email_circuit_breaker._failure_count
            } if email_circuit_breaker else {}
        },
        "request_traces": tracer.get_stats() if tracer else {}
    }
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
