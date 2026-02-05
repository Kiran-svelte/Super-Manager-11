"""
Plugins API Routes
"""
from fastapi import APIRouter
from typing import List, Dict

from ..core.plugins import PluginManager

router = APIRouter()

@router.get("/")
async def get_plugins():
    """Get all available plugins"""
    plugin_manager = PluginManager()
    plugins = plugin_manager.get_all_plugins()
    
    return {
        "plugins": [
            {
                "name": plugin.name,
                "description": plugin.description,
                "capabilities": plugin.get_capabilities(),
                "enabled": plugin.enabled
            }
            for plugin in plugins.values()
        ]
    }

@router.get("/capabilities")
async def get_capabilities():
    """Get all available capabilities"""
    plugin_manager = PluginManager()
    return {
        "capabilities": plugin_manager.get_available_capabilities()
    }

