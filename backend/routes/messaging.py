"""
Messaging Webhooks - Telegram & WhatsApp Input Layer
=====================================================
Handles incoming messages from external messaging platforms.
Part of Layer 1: Input Layer in the 10-layer architecture.

Supported Channels:
- Telegram Bot API (webhook)
- WhatsApp Business API via Twilio (webhook)
- Future: Voice input via Whisper API
"""

import os
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["messaging"])

# Environment config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")


# =============================================================================
# Pydantic Models
# =============================================================================

class TelegramMessage(BaseModel):
    """Telegram update structure (simplified)"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


class TwilioWhatsAppMessage(BaseModel):
    """Twilio WhatsApp webhook payload"""
    From: str  # WhatsApp number (e.g., whatsapp:+1234567890)
    To: str
    Body: str
    MessageSid: str
    AccountSid: Optional[str] = None
    NumMedia: Optional[str] = "0"


# =============================================================================
# TELEGRAM WEBHOOK
# =============================================================================

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive incoming Telegram messages.
    Telegram sends updates to this endpoint when users message the bot.
    
    Setup:
    1. Create bot with @BotFather
    2. Set TELEGRAM_BOT_TOKEN in .env
    3. Register webhook: 
       curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.com/webhook/telegram"
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("[Telegram] Bot token not configured")
        return {"ok": True}  # Return 200 to avoid Telegram retries
    
    try:
        payload = await request.json()
        logger.info(f"[Telegram] Received update: {payload.get('update_id')}")
        
        # Extract message
        message = payload.get("message") or payload.get("edited_message")
        callback = payload.get("callback_query")
        
        if message:
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user = message.get("from", {})
            username = user.get("username", user.get("first_name", "User"))
            
            if text:
                # Process message in background
                background_tasks.add_task(
                    process_telegram_message,
                    chat_id=chat_id,
                    text=text,
                    username=username,
                    user_id=str(user.get("id", ""))
                )
                
        elif callback:
            # Handle inline button callbacks
            callback_data = callback.get("data", "")
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            user_id = str(callback.get("from", {}).get("id", ""))
            
            background_tasks.add_task(
                process_telegram_callback,
                chat_id=chat_id,
                callback_data=callback_data,
                user_id=user_id
            )
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"[Telegram] Webhook error: {e}")
        return {"ok": True}  # Always return 200 to prevent retries


async def process_telegram_message(chat_id: int, text: str, username: str, user_id: str):
    """Process incoming Telegram message through the AI agent"""
    try:
        from backend.core.brain import brain
        import httpx
        
        logger.info(f"[Telegram] Processing message from {username}: {text[:50]}...")
        
        # Create session for this user
        session_id = f"telegram_{user_id}"
        
        # Process through AI brain
        response = await brain.process(
            session_id=session_id,
            message=text,
            user_id=f"telegram:{user_id}",
            channel="telegram"
        )
        
        # Send response back to user
        reply_text = response.get("message", "I couldn't process that request.")
        await send_telegram_message(chat_id, reply_text)
        
    except Exception as e:
        logger.error(f"[Telegram] Process error: {e}")
        await send_telegram_message(chat_id, "Sorry, I encountered an error. Please try again.")


async def process_telegram_callback(chat_id: int, callback_data: str, user_id: str):
    """Process Telegram inline button callback"""
    try:
        # Parse callback data (format: action:value)
        parts = callback_data.split(":", 1)
        action = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"[Telegram] Callback from {user_id}: {action}={value}")
        
        # Handle different callback actions
        if action == "confirm":
            await send_telegram_message(chat_id, f"✅ Confirmed: {value}")
        elif action == "cancel":
            await send_telegram_message(chat_id, "❌ Cancelled")
        elif action == "connect":
            # Integration connection request
            await send_telegram_message(
                chat_id, 
                f"🔗 To connect {value}, please visit:\nhttps://your-domain.com/connect/{value}"
            )
        else:
            await send_telegram_message(chat_id, f"Action received: {action}")
            
    except Exception as e:
        logger.error(f"[Telegram] Callback error: {e}")


async def send_telegram_message(chat_id: int, text: str, reply_markup: Dict = None):
    """Send a message to a Telegram chat"""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("[Telegram] Cannot send - no bot token")
        return
        
    try:
        import httpx
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.error(f"[Telegram] Send failed: {resp.text}")
                
    except Exception as e:
        logger.error(f"[Telegram] Send error: {e}")


# =============================================================================
# WHATSAPP WEBHOOK (via Twilio)
# =============================================================================

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive incoming WhatsApp messages via Twilio.
    
    Setup:
    1. Create Twilio account
    2. Set up WhatsApp Sandbox or Business API
    3. Configure webhook URL in Twilio console
    4. Set TWILIO_AUTH_TOKEN and TWILIO_ACCOUNT_SID in .env
    """
    try:
        # Parse form data (Twilio sends as form, not JSON)
        form_data = await request.form()
        
        from_number = form_data.get("From", "")  # whatsapp:+1234567890
        to_number = form_data.get("To", "")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        num_media = int(form_data.get("NumMedia", "0"))
        
        # Extract phone number
        phone = from_number.replace("whatsapp:", "")
        
        logger.info(f"[WhatsApp] Message from {phone}: {body[:50]}...")
        
        if body:
            background_tasks.add_task(
                process_whatsapp_message,
                phone=phone,
                text=body,
                message_sid=message_sid,
                num_media=num_media
            )
        
        # Return TwiML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"[WhatsApp] Webhook error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )


async def process_whatsapp_message(phone: str, text: str, message_sid: str, num_media: int = 0):
    """Process incoming WhatsApp message through the AI agent"""
    try:
        from backend.core.brain import brain
        
        logger.info(f"[WhatsApp] Processing from {phone}: {text[:50]}...")
        
        # Create session for this user
        session_id = f"whatsapp_{phone.replace('+', '')}"
        
        # Process through AI brain
        response = await brain.process(
            session_id=session_id,
            message=text,
            user_id=f"whatsapp:{phone}",
            channel="whatsapp"
        )
        
        # Send response back
        reply_text = response.get("message", "I couldn't process that request.")
        await send_whatsapp_message(phone, reply_text)
        
    except Exception as e:
        logger.error(f"[WhatsApp] Process error: {e}")
        await send_whatsapp_message(phone, "Sorry, I encountered an error. Please try again.")


async def send_whatsapp_message(to_phone: str, text: str):
    """Send a WhatsApp message via Twilio"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    if not all([account_sid, auth_token, from_number]):
        logger.warning("[WhatsApp] Twilio not configured")
        return
        
    try:
        import httpx
        from base64 import b64encode
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        # Ensure proper format
        to_whatsapp = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
        from_whatsapp = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        
        auth = b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                data={
                    "To": to_whatsapp,
                    "From": from_whatsapp,
                    "Body": text
                },
                headers={"Authorization": f"Basic {auth}"},
                timeout=10
            )
            
            if resp.status_code not in [200, 201]:
                logger.error(f"[WhatsApp] Send failed: {resp.text}")
            else:
                logger.info(f"[WhatsApp] Message sent to {to_phone}")
                
    except Exception as e:
        logger.error(f"[WhatsApp] Send error: {e}")


# =============================================================================
# VOICE INPUT (via Whisper API)
# =============================================================================

@router.post("/api/voice/transcribe")
async def transcribe_voice(request: Request):
    """
    Transcribe voice input using OpenAI Whisper API.
    Accepts audio file upload and returns transcribed text.
    
    This enables voice input for the Input Layer.
    """
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if not openai_key:
        raise HTTPException(status_code=503, detail="Voice transcription not configured")
    
    try:
        import httpx
        
        # Get uploaded audio file
        form = await request.form()
        audio_file = form.get("audio")
        
        if not audio_file:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Read file content
        content = await audio_file.read()
        filename = getattr(audio_file, "filename", "audio.webm")
        
        # Call OpenAI Whisper API
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai_key}"},
                files={"file": (filename, content)},
                data={"model": "whisper-1"},
                timeout=60
            )
            
            if resp.status_code != 200:
                logger.error(f"[Voice] Whisper error: {resp.text}")
                raise HTTPException(status_code=500, detail="Transcription failed")
            
            result = resp.json()
            transcribed_text = result.get("text", "")
            
            logger.info(f"[Voice] Transcribed: {transcribed_text[:50]}...")
            
            return {
                "status": "ok",
                "text": transcribed_text,
                "language": result.get("language", "en")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Voice] Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SETUP ENDPOINTS
# =============================================================================

@router.post("/api/telegram/setup")
async def setup_telegram_webhook(webhook_url: str):
    """Register webhook URL with Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN not set")
    
    try:
        import httpx
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"url": webhook_url}, timeout=10)
            result = resp.json()
            
            if result.get("ok"):
                return {"status": "ok", "message": "Telegram webhook registered"}
            else:
                raise HTTPException(status_code=400, detail=result.get("description", "Failed"))
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/messaging/status")
async def messaging_status():
    """Check status of messaging integrations"""
    return {
        "telegram": {
            "configured": bool(TELEGRAM_BOT_TOKEN),
            "token_preview": TELEGRAM_BOT_TOKEN[:10] + "..." if TELEGRAM_BOT_TOKEN else None
        },
        "whatsapp": {
            "configured": bool(TWILIO_AUTH_TOKEN and os.getenv("TWILIO_ACCOUNT_SID")),
            "number": os.getenv("TWILIO_WHATSAPP_NUMBER", "not set")
        },
        "voice": {
            "configured": bool(os.getenv("OPENAI_API_KEY")),
            "model": "whisper-1"
        }
    }


# Import Response for TwiML
from fastapi import Response
