"""
OAuth API Routes
==================
Endpoints for OAuth 2.0 flows:
- Initiate OAuth for various services
- Handle OAuth callbacks
- Manage user tokens
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oauth", tags=["OAuth"])

# Import OAuth manager
try:
    from ..core.oauth_manager import get_oauth_manager, OAuthService
    OAUTH_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import OAuth manager: {e}")
    OAUTH_AVAILABLE = False
    get_oauth_manager = None
    OAuthService = None


# =============================================================================
# Request/Response Models
# =============================================================================

class OAuthInitRequest(BaseModel):
    """Request to initiate OAuth flow"""
    user_id: str = Field(..., description="User identifier")
    service: str = Field(..., description="Service name (gmail, zoom, etc.)")
    extra_scopes: Optional[List[str]] = Field(default=None, description="Additional OAuth scopes")


class OAuthStatusResponse(BaseModel):
    """OAuth status response"""
    service: str
    connected: bool
    email: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status")
async def get_oauth_status():
    """Get OAuth module status"""
    return {
        "available": OAUTH_AVAILABLE,
        "supported_services": [s.value for s in OAuthService] if OAuthService else [],
    }


@router.post("/initiate")
async def initiate_oauth(request_data: OAuthInitRequest, request: Request):
    """
    Initiate OAuth flow for a service.
    
    Returns the authorization URL that the user should be redirected to.
    """
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth not available")
    
    try:
        service = OAuthService(request_data.service)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported service: {request_data.service}. Supported: {[s.value for s in OAuthService]}"
        )
    
    manager = get_oauth_manager()
    
    # Calculate redirect_uri dynamically based on the Host
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/callback"
    if service == OAuthService.ZOOM:
        redirect_uri = f"{base_url}/api/oauth/callback/zoom"
        
    try:
        auth_url, state = manager.get_authorization_url(
            user_id=request_data.user_id,
            service=service,
            extra_scopes=request_data.extra_scopes,
            override_redirect_uri=redirect_uri
        )
        
        return {
            "status": "ok",
            "authorization_url": auth_url,
            "state": state,
            "service": service.value,
            "instructions": "Redirect user to authorization_url to complete OAuth flow",
        }
        
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/authorize/{service}")
async def authorize_service(
    service: str,
    request: Request,
    user_id: str = Query(..., description="User identifier")
):
    """
    Start OAuth flow and redirect to provider.
    
    This is a convenience endpoint that initiates OAuth and redirects directly.
    """
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth not available")
    
    try:
        oauth_service = OAuthService(service)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported service: {service}")
    
    manager = get_oauth_manager()
    
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/callback"
    if oauth_service == OAuthService.ZOOM:
        redirect_uri = f"{base_url}/api/oauth/callback/zoom"
        
    auth_url, state = manager.get_authorization_url(user_id, oauth_service, override_redirect_uri=redirect_uri)
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(None, description="Authorization code"),
    state: str = Query(None, description="OAuth state"),
    error: str = Query(None, description="Error code"),
    error_description: str = Query(None, description="Error description"),
):
    """
    OAuth callback endpoint.
    
    This receives the authorization code from the OAuth provider
    and exchanges it for access/refresh tokens.
    """
    if not OAUTH_AVAILABLE:
        return HTMLResponse(content=_error_html("OAuth not available"), status_code=503)
    
    if error:
        return HTMLResponse(
            content=_error_html(f"OAuth Error: {error} - {error_description}"),
            status_code=400
        )
    
    if not code or not state:
        return HTMLResponse(
            content=_error_html("Missing authorization code or state"),
            status_code=400
        )
    
    manager = get_oauth_manager()
    
    try:
        token = await manager.exchange_code(state, code)
        
        if token:
            return HTMLResponse(content=_success_html(
                service=token.service,
                email=token.user_email,
            ))
        else:
            return HTMLResponse(
                content=_error_html("Failed to exchange authorization code"),
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(
            content=_error_html(f"Callback error: {str(e)}"),
            status_code=500
        )


@router.get("/callback/zoom")
async def zoom_oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """Zoom-specific OAuth callback"""
    return await oauth_callback(code=code, state=state, error=error)


@router.get("/token/{service}")
async def get_oauth_token_status(
    service: str,
    user_id: str = Query(..., description="User identifier")
) -> OAuthStatusResponse:
    """
    Check OAuth token status for a service.
    """
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth not available")
    
    try:
        oauth_service = OAuthService(service)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported service: {service}")
    
    manager = get_oauth_manager()
    token = await manager.get_valid_token(user_id, oauth_service)
    
    if token:
        return OAuthStatusResponse(
            service=service,
            connected=True,
            email=token.user_email,
            scopes=token.scopes,
            expires_at=token.expires_at.isoformat() if token.expires_at else None,
        )
    else:
        return OAuthStatusResponse(
            service=service,
            connected=False,
        )


@router.get("/tokens")
async def get_all_oauth_tokens(user_id: str = Query(...)):
    """Get status of all OAuth connections for a user"""
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth not available")
    
    manager = get_oauth_manager()
    results = {}
    
    for service in OAuthService:
        token = await manager.get_valid_token(user_id, service)
        results[service.value] = {
            "connected": token is not None,
            "email": token.user_email if token else None,
        }
    
    return {
        "user_id": user_id,
        "connections": results,
    }


@router.delete("/token/{service}")
async def revoke_oauth_token(
    service: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Revoke OAuth token for a service.
    """
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="OAuth not available")
    
    try:
        oauth_service = OAuthService(service)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported service: {service}")
    
    manager = get_oauth_manager()
    success = await manager.revoke_token(user_id, oauth_service)
    
    return {
        "status": "ok" if success else "failed",
        "service": service,
        "revoked": success,
    }


@router.get("/setup-guide")
async def oauth_setup_guide():
    """
    OAuth setup guide - shows instructions for configuring OAuth.
    Visit this in a browser for step-by-step guidance.
    """
    return HTMLResponse(content=_setup_guide_html())


# =============================================================================
# HTML Templates
# =============================================================================

def _setup_guide_html() -> str:
    """Generate setup guide HTML"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Super Manager - OAuth Setup Guide</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f8fafc;
            color: #1e293b;
        }
        h1 { color: #667eea; margin-bottom: 10px; }
        h2 { color: #334155; margin-top: 30px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .step {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .step-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            margin-right: 10px;
            font-weight: bold;
        }
        code {
            background: #1e293b;
            color: #22d3ee;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        pre {
            background: #1e293b;
            color: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 10px 5px 10px 0;
            font-weight: 500;
        }
        .btn:hover { opacity: 0.9; }
        .warning {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
        }
        .success {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <h1>🔐 Super Manager OAuth Setup</h1>
    <p>Follow these steps to enable email sending and other OAuth-powered features.</p>
    
    <h2>Quick Setup (Recommended)</h2>
    <div class="step">
        <span class="step-number">1</span>
        <strong>Add Redirect URI to Google Cloud Console</strong>
        <p>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a> and add this redirect URI to your OAuth 2.0 Client:</p>
        <pre>http://localhost:10000/api/oauth/callback</pre>
    </div>
    
    <div class="step">
        <span class="step-number">2</span>
        <strong>Authorize Gmail</strong>
        <p>Click the button below to authorize Super Manager to send emails on your behalf:</p>
        <a href="/api/oauth/authorize/gmail?user_id=default" class="btn">🔗 Authorize Gmail</a>
    </div>
    
    <div class="step">
        <span class="step-number">3</span>
        <strong>Test Email</strong>
        <p>After authorization, test sending an email:</p>
        <pre>POST /api/automation/quick/email?user_id=default&to=you@example.com&subject=Test&body=Hello</pre>
    </div>
    
    <h2>Alternative: App Password (SMTP)</h2>
    <div class="step">
        <span class="step-number">1</span>
        <strong>Enable 2-Factor Authentication</strong>
        <p>Go to <a href="https://myaccount.google.com/security" target="_blank">Google Account Security</a> and enable 2-Step Verification.</p>
    </div>
    
    <div class="step">
        <span class="step-number">2</span>
        <strong>Create App Password</strong>
        <p>Visit <a href="https://myaccount.google.com/apppasswords" target="_blank">App Passwords</a> and create a new app password for "Mail".</p>
    </div>
    
    <div class="step">
        <span class="step-number">3</span>
        <strong>Add to .env</strong>
        <p>Add the app password to your <code>backend/.env</code> file:</p>
        <pre>SMTP_PASSWORD=your-16-char-app-password
SMTP_EMAIL=your-gmail@gmail.com</pre>
    </div>
    
    <div class="warning">
        <strong>⚠️ Refresh Token Expiration</strong>
        <p>If your OAuth app is in "Testing" mode in Google Cloud Console, refresh tokens expire after 7 days. To avoid this:</p>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/apis/credentials/consent" target="_blank">OAuth Consent Screen</a></li>
            <li>Click "Publish App" to move to production</li>
            <li>Or add your email as a test user</li>
        </ol>
    </div>
    
    <div class="success">
        <strong>✅ Current Status</strong>
        <p>Check your current OAuth status: <a href="/api/oauth/token/gmail?user_id=default">/api/oauth/token/gmail?user_id=default</a></p>
        <p>Full system status: <a href="/api/status">/api/status</a></p>
    </div>
</body>
</html>
"""

def _success_html(service: str, email: str = None) -> str:
    """Generate success page HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OAuth Connected</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .card {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #10b981;
            margin: 0 0 10px;
        }}
        p {{
            color: #64748b;
            margin: 0;
        }}
        .email {{
            margin-top: 15px;
            padding: 10px;
            background: #f1f5f9;
            border-radius: 8px;
            font-family: monospace;
        }}
        .close-btn {{
            margin-top: 20px;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✅</div>
        <h1>Connected!</h1>
        <p>{service.title()} has been successfully connected.</p>
        {f'<div class="email">{email}</div>' if email else ''}
        <button class="close-btn" onclick="window.close()">Close this window</button>
    </div>
    <script>
        // Try to close automatically after 3 seconds
        setTimeout(() => {{
            window.close();
        }}, 3000);
    </script>
</body>
</html>
"""


def _error_html(error_message: str) -> str:
    """Generate error page HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OAuth Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }}
        .card {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #ef4444;
            margin: 0 0 10px;
        }}
        p {{
            color: #64748b;
            margin: 0;
        }}
        .error {{
            margin-top: 15px;
            padding: 15px;
            background: #fef2f2;
            border-radius: 8px;
            color: #b91c1c;
            font-size: 14px;
            text-align: left;
        }}
        .close-btn {{
            margin-top: 20px;
            padding: 12px 30px;
            background: #64748b;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">❌</div>
        <h1>Connection Failed</h1>
        <p>Something went wrong during the OAuth process.</p>
        <div class="error">{error_message}</div>
        <button class="close-btn" onclick="window.close()">Close</button>
    </div>
</body>
</html>
"""
