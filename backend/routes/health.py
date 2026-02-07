"""
Super Manager - Health & Metrics Routes
=======================================

API endpoints for health checks, metrics, and system status.
"""

from fastapi import APIRouter, Response
from datetime import datetime
import asyncio
from typing import Dict, Any

# Import our modules
from ..core.monitoring import (
    health_checker,
    metrics,
    collect_system_metrics,
    setup_health_checks
)
from ..core.cache import cache
from ..core.errors import error_tracker

router = APIRouter(prefix="/api", tags=["Health & Metrics"])

# Initialize on startup
_startup_time = datetime.utcnow()


@router.on_event("startup")
async def startup_init():
    """Initialize health checks on startup"""
    setup_health_checks()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Checks all registered components and returns aggregated status.
    """
    # Run all health checks
    await health_checker.check_all()
    
    # Get overall status
    status = health_checker.get_overall_status()
    
    # Add additional info
    status["uptime_seconds"] = (datetime.utcnow() - _startup_time).total_seconds()
    status["cache_stats"] = cache.get_stats()
    
    return status


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.
    
    Returns 200 if the service is alive (not deadlocked).
    """
    return {"status": "live"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    
    Returns 200 if the service is ready to accept traffic.
    """
    # Quick check of critical components
    await health_checker.check_all()
    status = health_checker.get_overall_status()
    
    if status["healthy"]:
        return {"status": "ready"}
    else:
        return Response(
            content='{"status": "not ready"}',
            status_code=503,
            media_type="application/json"
        )


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics in JSON format.
    """
    # Collect current system metrics
    system = collect_system_metrics()
    
    # Get all metrics
    all_metrics = metrics.get_all_metrics()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": system,
        **all_metrics
    }


@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """
    Export metrics in Prometheus format.
    
    Returns plain text format compatible with Prometheus scraping.
    """
    # Collect system metrics
    collect_system_metrics()
    
    # Export in Prometheus format
    prometheus_output = metrics.export_prometheus()
    
    return Response(
        content=prometheus_output,
        media_type="text/plain"
    )


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status.
    
    Includes health, metrics, errors, and cache info.
    """
    # Run health checks
    await health_checker.check_all()
    health = health_checker.get_overall_status()
    
    # Get system metrics
    system = collect_system_metrics()
    
    # Get error stats
    errors = error_tracker.get_stats()
    
    # Get cache stats
    cache_stats = cache.get_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - _startup_time).total_seconds(),
        "health": health,
        "system": system,
        "errors": {
            "last_hour": errors.get("errors_last_hour", 0),
            "last_minute": errors.get("errors_last_minute", 0)
        },
        "cache": cache_stats,
        "version": {
            "api": "1.0.0",
            "python": "3.11"
        }
    }


@router.get("/errors/recent")
async def recent_errors() -> Dict[str, Any]:
    """
    Get recent error occurrences.
    
    Useful for debugging and monitoring.
    """
    return {
        "errors": error_tracker.get_recent_errors(limit=50),
        "stats": error_tracker.get_stats()
    }
