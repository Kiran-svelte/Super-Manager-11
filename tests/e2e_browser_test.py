import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    print("Starting Playwright Test...")
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print("Navigating to http://localhost:3000")
        try:
            await page.goto("http://localhost:3000", timeout=30000)
            print("Successfully loaded homepage")
        except Exception as e:
            print(f"Failed to load homepage: {e}")
            await browser.close()
            return

        # Screenshot Homepage
        screenshot_dir = r"d:\GOOGLE PROJECT\test_evidence"
        os.makedirs(screenshot_dir, exist_ok=True)
        await page.screenshot(path=os.path.join(screenshot_dir, "homepage.png"))
        print(f"Screenshot saved: {screenshot_dir}\\homepage.png")

        # Verify Title or Content
        content = await page.content()
        if "Super Manager" in content:
            print("Verified: 'Super Manager' text found on page.")
        else:
            print("Warning: 'Super Manager' text NOT found on page.")

        # Find Input and Send Message
        try:
            # Look for textarea or input
            await page.wait_for_selector("textarea", timeout=5000)
            await page.fill("textarea", "Hello, are you online?")
            print("Typed message into chat input.")
            
            # Click Send button (assuming verify by icon or class)
            # Based on code: className="send-btn"
            await page.click(".send-btn")
            print("Clicked Send button.")
            
            # Wait for response (look for "thinking" or new message)
            # Code uses "thinking" class or simplified feedback
            print("Waiting for response...")
            await page.wait_for_timeout(5000) # Wait 5s for AI
            
            # Screenshot Chat
            await page.screenshot(path=os.path.join(screenshot_dir, "chat_interaction.png"))
            print(f"Screenshot saved: {screenshot_dir}\\chat_interaction.png")
            
            # Verify AI Response
            # Look for "message ai" class
            ai_messages = await page.query_selector_all(".message.ai .message-bubble")
            if len(ai_messages) > 0:
                text = await ai_messages[-1].inner_text()
                print(f"AI Responded: {text}")
            else:
                print("No AI response detected yet.")

        except Exception as e:
            print(f"Interaction failed: {e}")
            await page.screenshot(path=os.path.join(screenshot_dir, "error_state.png"))

        await browser.close()
        print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(run())
