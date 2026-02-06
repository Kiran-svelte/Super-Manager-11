"""
WEB AUTOMATION MODULE
=====================
When APIs aren't available, we automate the web directly using Playwright.

This can:
- Send emails via Gmail
- Send WhatsApp messages
- Fill forms
- Click buttons
- Extract data
- Automate any website

Requirements: pip install playwright && playwright install
"""
import os
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Try to import playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[WEB AUTOMATION] Playwright not installed. Run: pip install playwright && playwright install")


@dataclass
class AutomationStep:
    """A single automation step"""
    action: str  # click, type, navigate, wait, extract, screenshot
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: int = 30000


class WebAutomation:
    """Automate any website"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def start(self, headless: bool = True):
        """Start the browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
    
    async def stop(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
    
    async def execute(self, url: str, actions: List[Dict]) -> Dict[str, Any]:
        """Execute a series of actions on a webpage"""
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "error": "Playwright not installed. Run: pip install playwright && playwright install"}
        
        try:
            await self.start(headless=True)
            
            # Navigate to URL
            await self.page.goto(url, timeout=60000)
            
            results = []
            
            for action_data in actions:
                action = action_data.get("action")
                selector = action_data.get("selector")
                value = action_data.get("value")
                
                if action == "click":
                    await self.page.click(selector)
                    results.append(f"Clicked: {selector}")
                
                elif action == "type":
                    await self.page.fill(selector, value)
                    results.append(f"Typed in: {selector}")
                
                elif action == "wait":
                    await self.page.wait_for_selector(selector)
                    results.append(f"Found: {selector}")
                
                elif action == "extract":
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        results.append({"extracted": text})
                
                elif action == "screenshot":
                    path = value or "screenshot.png"
                    await self.page.screenshot(path=path)
                    results.append(f"Screenshot saved: {path}")
                
                elif action == "wait_time":
                    await asyncio.sleep(int(value or 1))
                
                elif action == "press":
                    await self.page.keyboard.press(value)
                    results.append(f"Pressed: {value}")
            
            await self.stop()
            
            return {
                "success": True,
                "details": "Automation completed",
                "results": results
            }
            
        except Exception as e:
            await self.stop()
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # SPECIFIC AUTOMATIONS
    # =========================================================================
    
    async def send_gmail(self, to: str, subject: str, body: str, credentials: Dict) -> Dict:
        """Send email via Gmail web interface"""
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            return {"success": False, "error": "Gmail credentials required (email, password)"}
        
        try:
            await self.start(headless=False)  # Visible for debugging
            
            # Go to Gmail
            await self.page.goto("https://mail.google.com")
            
            # Login if needed
            if "accounts.google.com" in self.page.url:
                await self.page.fill('input[type="email"]', email)
                await self.page.click('button:has-text("Next")')
                await self.page.wait_for_selector('input[type="password"]')
                await self.page.fill('input[type="password"]', password)
                await self.page.click('button:has-text("Next")')
                await self.page.wait_for_load_state("networkidle")
            
            # Compose new email
            await self.page.click('div[gh="cm"]')  # Compose button
            await self.page.wait_for_selector('input[name="to"]')
            
            # Fill email details
            await self.page.fill('input[name="to"]', to)
            await self.page.fill('input[name="subjectbox"]', subject)
            await self.page.fill('div[aria-label="Message Body"]', body)
            
            # Send
            await self.page.click('div[aria-label="Send"]')
            await asyncio.sleep(2)
            
            await self.stop()
            return {"success": True, "details": f"Email sent to {to} via Gmail"}
            
        except Exception as e:
            await self.stop()
            return {"success": False, "error": f"Gmail automation failed: {e}"}
    
    async def send_whatsapp_web(self, phone: str, message: str) -> Dict:
        """Send WhatsApp message via WhatsApp Web"""
        try:
            await self.start(headless=False)
            
            # Go to WhatsApp Web with phone number
            url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
            await self.page.goto(url)
            
            # Wait for QR code scan or already logged in
            print("[WHATSAPP] Please scan QR code if prompted...")
            await self.page.wait_for_selector('div[data-testid="send"]', timeout=120000)
            
            # Click send button
            await self.page.click('div[data-testid="send"]')
            await asyncio.sleep(2)
            
            await self.stop()
            return {"success": True, "details": f"WhatsApp message sent to {phone}"}
            
        except Exception as e:
            await self.stop()
            return {"success": False, "error": f"WhatsApp automation failed: {e}"}
    
    async def google_search(self, query: str) -> Dict:
        """Search Google and extract results"""
        try:
            await self.start(headless=True)
            
            await self.page.goto(f"https://www.google.com/search?q={query}")
            await self.page.wait_for_selector('div#search')
            
            # Extract first few results
            results = []
            items = await self.page.query_selector_all('div.g')
            
            for i, item in enumerate(items[:5]):
                try:
                    title_el = await item.query_selector('h3')
                    link_el = await item.query_selector('a')
                    snippet_el = await item.query_selector('div[data-content-feature="1"]')
                    
                    if title_el and link_el:
                        title = await title_el.text_content()
                        link = await link_el.get_attribute('href')
                        snippet = await snippet_el.text_content() if snippet_el else ""
                        
                        results.append({
                            "title": title,
                            "url": link,
                            "snippet": snippet[:200]
                        })
                except:
                    continue
            
            await self.stop()
            return {"success": True, "results": results}
            
        except Exception as e:
            await self.stop()
            return {"success": False, "error": str(e)}
    
    async def fill_form(self, url: str, form_data: Dict) -> Dict:
        """Fill and submit a form"""
        try:
            await self.start(headless=True)
            await self.page.goto(url)
            
            for selector, value in form_data.items():
                try:
                    await self.page.fill(selector, value)
                except:
                    # Try as a click if fill doesn't work
                    await self.page.click(selector)
            
            await self.stop()
            return {"success": True, "details": "Form filled"}
            
        except Exception as e:
            await self.stop()
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, url: str, path: str = "screenshot.png") -> Dict:
        """Take a screenshot of a webpage"""
        try:
            await self.start(headless=True)
            await self.page.goto(url)
            await self.page.screenshot(path=path, full_page=True)
            await self.stop()
            return {"success": True, "path": path}
        except Exception as e:
            await self.stop()
            return {"success": False, "error": str(e)}


# ============================================================================
# UPI PAYMENT AUTOMATION (PhonePe, GPay, Paytm Web)
# ============================================================================

class PaymentAutomation(WebAutomation):
    """Automate payment flows"""
    
    async def generate_upi_qr(self, upi_id: str, amount: float, name: str = "") -> Dict:
        """Generate UPI QR code for payment"""
        # UPI deep link
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        
        # Generate QR code image using an API
        qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={upi_url}"
        
        return {
            "success": True,
            "upi_url": upi_url,
            "qr_code": qr_api,
            "details": f"Scan QR code or click link to pay ₹{amount} to {upi_id}"
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_web_automation() -> WebAutomation:
    return WebAutomation()

def get_payment_automation() -> PaymentAutomation:
    return PaymentAutomation()

async def install_playwright():
    """Install playwright browsers"""
    import subprocess
    subprocess.run(["playwright", "install", "chromium"])
