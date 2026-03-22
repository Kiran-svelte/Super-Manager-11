"""
Fallback Router - Integration Manager Component
=================================================
Routes tasks to alternative execution methods when primary API is unavailable.

Per README (line 282-289):
| Situation     | Primary | Fallback 1 | Fallback 2 | Last Resort |
|---------------|---------|-----------|-----------|-------------|
| No Calendar   | Google Calendar API | Browser automation | Ask user manually | Provide instructions |
| No Email API  | Gmail OAuth | SMTP direct send | Browser automation | Draft for user |
| No Payment API| Razorpay/Stripe | Generate payment link | Browser checkout | Share payment details |

Author: Super Manager AI
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)


class ExecutionMethod(Enum):
    """Available execution methods in priority order"""
    API = "api"                     # Direct API call (fastest, most reliable)
    BROWSER_AUTOMATION = "browser"  # Playwright browser automation
    USER_INPUT = "user_input"       # Ask user to provide input
    PARTIAL_ASSIST = "partial"      # Provide partial help + instructions


@dataclass
class FallbackOption:
    """A single fallback option"""
    method: ExecutionMethod
    label: str
    description: str
    confidence: float  # 0.0 to 1.0 - how likely this will work
    requires_user_action: bool = False


@dataclass
class FallbackRoute:
    """Complete fallback route for a capability"""
    capability: str
    primary: FallbackOption
    fallbacks: List[FallbackOption]
    current_method: Optional[ExecutionMethod] = None
    
    def get_available_options(self, api_connected: bool = False) -> List[FallbackOption]:
        """Get available options based on current state"""
        options = []
        
        if api_connected:
            options.append(self.primary)
        
        options.extend(self.fallbacks)
        return options
    
    def get_best_option(self, api_connected: bool = False) -> FallbackOption:
        """Get the best available option"""
        options = self.get_available_options(api_connected)
        if options:
            return max(options, key=lambda x: x.confidence)
        return self.fallbacks[-1]  # Last resort


class FallbackRouter:
    """
    Routes capabilities to best available execution method.
    
    Usage:
        router = FallbackRouter()
        route = router.get_route("create_meeting")
        
        if not zoom_connected:
            options = route.get_available_options(api_connected=False)
            # Show options to user
    """
    
    def __init__(self):
        self._routes: Dict[str, FallbackRoute] = {}
        self._init_default_routes()
    
    def _init_default_routes(self):
        """Initialize default fallback routes"""
        
        # Meeting creation
        self._routes["create_meeting"] = FallbackRoute(
            capability="create_meeting",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="Zoom Meeting",
                description="Create via Zoom API (requires Zoom connection)",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.API,
                    label="Google Meet",
                    description="Create via Google Calendar API (requires Google connection)",
                    confidence=0.9,
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.API,
                    label="Jitsi Meet (Free)",
                    description="Instant free meeting link, no connection needed",
                    confidence=0.95,  # High because always works
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.BROWSER_AUTOMATION,
                    label="Browser Automation",
                    description="Open Zoom/Meet in browser and create meeting",
                    confidence=0.6,
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.USER_INPUT,
                    label="Manual Creation",
                    description="I'll guide you to create it yourself",
                    confidence=0.3,
                    requires_user_action=True,
                ),
            ]
        )
        
        # Email sending
        self._routes["send_email"] = FallbackRoute(
            capability="send_email",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="Gmail API",
                description="Send via Gmail OAuth (requires Gmail connection)",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.API,
                    label="SMTP Direct",
                    description="Send via SMTP (if configured)",
                    confidence=0.9,
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.BROWSER_AUTOMATION,
                    label="Browser Compose",
                    description="Open Gmail in browser with pre-filled email",
                    confidence=0.7,
                    requires_user_action=True,
                ),
                FallbackOption(
                    method=ExecutionMethod.PARTIAL_ASSIST,
                    label="Draft Email",
                    description="I'll draft the email, you send it",
                    confidence=0.5,
                    requires_user_action=True,
                ),
            ]
        )
        
        # Calendar events
        self._routes["create_calendar_event"] = FallbackRoute(
            capability="create_calendar_event",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="Google Calendar",
                description="Create via Google Calendar API",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.BROWSER_AUTOMATION,
                    label="Browser Calendar",
                    description="Open Google Calendar in browser",
                    confidence=0.7,
                    requires_user_action=True,
                ),
                FallbackOption(
                    method=ExecutionMethod.PARTIAL_ASSIST,
                    label="ICS File",
                    description="Generate calendar file to import",
                    confidence=0.6,
                    requires_user_action=True,
                ),
            ]
        )
        
        # Payment
        self._routes["create_payment"] = FallbackRoute(
            capability="create_payment",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="Razorpay",
                description="Create payment link via Razorpay API",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.API,
                    label="Stripe",
                    description="Create payment link via Stripe API",
                    confidence=0.9,
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.BROWSER_AUTOMATION,
                    label="Browser Checkout",
                    description="Open payment page in browser",
                    confidence=0.6,
                    requires_user_action=True,
                ),
                FallbackOption(
                    method=ExecutionMethod.PARTIAL_ASSIST,
                    label="Payment Details",
                    description="Provide bank/UPI details for manual transfer",
                    confidence=0.4,
                    requires_user_action=True,
                ),
            ]
        )
        
        # Web search (always works)
        self._routes["web_search"] = FallbackRoute(
            capability="web_search",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="DuckDuckGo Search",
                description="Search via DuckDuckGo (no API key needed)",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.BROWSER_AUTOMATION,
                    label="Browser Search",
                    description="Open search in browser",
                    confidence=0.8,
                    requires_user_action=False,
                ),
            ]
        )
        
        # Image generation
        self._routes["generate_image"] = FallbackRoute(
            capability="generate_image",
            primary=FallbackOption(
                method=ExecutionMethod.API,
                label="Pollinations AI",
                description="Generate via Pollinations (free, no API key)",
                confidence=1.0,
                requires_user_action=False,
            ),
            fallbacks=[
                FallbackOption(
                    method=ExecutionMethod.API,
                    label="DALL-E",
                    description="Generate via OpenAI DALL-E (if configured)",
                    confidence=0.9,
                    requires_user_action=False,
                ),
                FallbackOption(
                    method=ExecutionMethod.PARTIAL_ASSIST,
                    label="Describe for User",
                    description="Provide detailed prompt for manual generation",
                    confidence=0.3,
                    requires_user_action=True,
                ),
            ]
        )
    
    def get_route(self, capability: str) -> Optional[FallbackRoute]:
        """Get fallback route for a capability"""
        return self._routes.get(capability)
    
    def register_route(self, capability: str, route: FallbackRoute):
        """Register a custom fallback route"""
        self._routes[capability] = route
        logger.info(f"[FALLBACK_ROUTER] Registered route for: {capability}")
    
    def get_all_capabilities(self) -> List[str]:
        """Get all registered capabilities"""
        return list(self._routes.keys())
    
    def get_options_for_capability(
        self,
        capability: str,
        connected_services: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available options for a capability based on connected services.
        
        Args:
            capability: The capability name (e.g., "create_meeting")
            connected_services: List of connected service names (e.g., ["zoom", "gmail"])
            
        Returns:
            List of option dicts suitable for frontend display
        """
        route = self.get_route(capability)
        if not route:
            return []
        
        connected_services = connected_services or []
        
        options = []
        
        # Check if primary is available
        primary_available = self._is_primary_available(capability, connected_services)
        
        if primary_available:
            options.append({
                "method": route.primary.method.value,
                "label": route.primary.label,
                "description": route.primary.description,
                "confidence": route.primary.confidence,
                "requires_user_action": route.primary.requires_user_action,
                "is_primary": True,
                "recommended": True,
            })
        
        # Add fallbacks
        for fallback in route.fallbacks:
            options.append({
                "method": fallback.method.value,
                "label": fallback.label,
                "description": fallback.description,
                "confidence": fallback.confidence,
                "requires_user_action": fallback.requires_user_action,
                "is_primary": False,
                "recommended": not primary_available and fallback == route.fallbacks[0],
            })
        
        return options
    
    def _is_primary_available(self, capability: str, connected_services: List[str]) -> bool:
        """Check if primary method is available"""
        # Map capabilities to required services
        service_requirements = {
            "create_meeting": ["zoom", "google_calendar"],
            "send_email": ["gmail"],
            "create_calendar_event": ["google_calendar"],
            "create_payment": ["razorpay", "stripe"],
            "web_search": [],  # Always available
            "generate_image": [],  # Always available
        }
        
        required = service_requirements.get(capability, [])
        
        if not required:
            return True
        
        return any(service in connected_services for service in required)


# Global fallback router instance
_fallback_router: Optional[FallbackRouter] = None


def get_fallback_router() -> FallbackRouter:
    """Get the global fallback router instance"""
    global _fallback_router
    if _fallback_router is None:
        _fallback_router = FallbackRouter()
    return _fallback_router
