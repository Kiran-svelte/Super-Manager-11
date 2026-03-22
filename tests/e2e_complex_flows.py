import asyncio
import os
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright

async def run():
    print("Starting Comprehensive Agentic UI E2E Automated Test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Auth overrides to skip onboarding
        await page.add_init_script("""
            try {
              localStorage.setItem('onboarding_skipped', 'true');
              localStorage.setItem('super_manager_user_id', 'e2e_user');
            } catch (e) {}
        """)

        base_url = os.environ.get("E2E_BASE_URL", "http://localhost:3003")
        log_dir = r"d:\GOOGLE PROJECT\test_evidence\agentic_flows"
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ts_dir = os.path.join(log_dir, ts)
        os.makedirs(ts_dir, exist_ok=True)

        print(f"Artifacts will be saved to: {ts_dir}")

        transcript_path = os.path.join(ts_dir, "agentic_chat_transcript.jsonl")
        open(transcript_path, "w", encoding="utf-8").close()
        
        def _append(line: str):
            with open(transcript_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        print(f"Navigating to {base_url} ...")
        try:
            await page.goto(base_url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=os.path.join(ts_dir, "00_app_load.png"))
            print("Successfully loaded App UI.")
        except Exception as e:
            print(f"Failed to load UI: {e}")
            await browser.close()
            return

        # 1. UI Navigation Flow: Settings, Integrations, and Tasks Panel
        try:
            print("Testing UI Navigations (Settings & Panels)...")
            # Open Settings Modal
            settings_btn = page.locator(".ai-settings-btn, button:has-text('Settings'), .nav-icon-settings, .settings-icon").first
            
            # Since frontend components have `className="ai-settings-btn"`, let's try to click it
            if await settings_btn.count() > 0:
                await settings_btn.click()
                await asyncio.sleep(1)
                await page.screenshot(path=os.path.join(ts_dir, "01_settings_modal_open.png"))
                
                # Navigate tabs within settings
                tabs = page.locator(".settings-tabs button")
                for i in range(await tabs.count()):
                    tab_name = await tabs.nth(i).inner_text()
                    await tabs.nth(i).click()
                    await asyncio.sleep(0.5)
                    await page.screenshot(path=os.path.join(ts_dir, f"02_settings_tab_{tab_name.replace(' ', '_')}.png"))
                
                # Close settings
                close_btn = page.locator(".close-btn, button:has-text('Close')").first
                if await close_btn.count() > 0:
                    await close_btn.click()
                    await asyncio.sleep(0.5)

            print("Settings flow checked.")

            # Toggle Sidebar/Task Panel if available (e.g., Toggle Tasks or similar class)
            task_toggle_btn = page.locator(".task-panel-toggle, .toggle-sidebar, button:has-text('Tasks')").first
            if await task_toggle_btn.count() > 0:
                await task_toggle_btn.click()
                await asyncio.sleep(1)
                await page.screenshot(path=os.path.join(ts_dir, "03_task_panel_open.png"))
                await task_toggle_btn.click() # toggle close
            print("Task panel flow checked.")
        except Exception as e:
            print(f"UI Navigation testing issue (non-fatal): {e}")

        # 2. Executing 10 Agentic Tasks
        print("\nBeginning 10 Agentic Task Chat Inputs...")
        prompts = [
            {"name": "Create Task 1", "prompt": "Add a task 'Review PRs for backend' to my todo list and mark it High priority."},
            {"name": "List Tasks 1", "prompt": "Can you show me all my pending tasks in my list currently?"},
            {"name": "File System 1", "prompt": "Check my local dev folder using python tools to list all python files near backend/main.py."},
            {"name": "Read Code 1", "prompt": "Read the content of frontend/package.json and list all my frontend dependencies explicitly."},
            {"name": "Research Search 1", "prompt": "Look up how to make a cross-origin fetch request in Vite using web search or your knowledge."},
            {"name": "Draft Email 1", "prompt": "Draft an email to 'team@company.com' about postponing tomorrow's meeting (do not actually send it)."},
            {"name": "System Status 1", "prompt": "Ping google.com using a shell command or python script to ensure you have internet access and report the timing."},
            {"name": "Agent Planning 1", "prompt": "Outline the steps required to implement a new caching layer in Redis for a FastAPI backend."},
            {"name": "Generate Config 1", "prompt": "Generate a sample docker-compose.yml for a Node app with a Postgres DB, put it in a markdown block."},
            {"name": "Reflect Summarize 1", "prompt": "Summarize what functionalities we have just tested today via this chat UI."}
        ]

        try:
            await page.wait_for_selector(".input-wrapper input", timeout=15000)
            ai_locator = page.locator(".message.message-ai .msg-ai-content")
            
            for idx, task in enumerate(prompts, start=1):
                print(f"\nTask {idx}/10: {task['name']}")
                input_field = page.locator(".input-wrapper input")
                await input_field.fill(task['prompt'])
                
                before_count = await ai_locator.count()
                
                # Click send
                send_btn = page.locator(".send-btn")
                await send_btn.click()
                
                print(f"  Sent: '{task['prompt']}'")
                print("  Waiting up to 120s for AI agent execution (handling tool calls and thinking)...")
                
                # Wait for the AI message count to increment
                await page.wait_for_function(
                    "before => document.querySelectorAll('.message.message-ai .msg-ai-content').length > before",
                    arg=before_count,
                    timeout=120000
                )
                
                await asyncio.sleep(2) # Give a moment for any final markdown rendering or typing animation if present
                
                after_count = await ai_locator.count()
                response = await ai_locator.nth(after_count - 1).inner_text()
                
                # We need to ensure we wait for tool-call completion loops, so wait until `.thinking-indicator` or similar is gone
                loading_indicator = page.locator(".thinking, .typing-indicator")
                if await loading_indicator.count() > 0:
                     await loading_indicator.wait_for(state="hidden", timeout=120000)
                     # refetch response text in case it updated
                     response = await ai_locator.nth(after_count - 1).inner_text()
                
                response_len = len(response)
                print(f"  Success: Received response ({response_len} chars).")
                
                # Log transcript
                _append(json.dumps({
                    "task": task["name"],
                    "prompt": task["prompt"],
                    "response": response,
                    "length": response_len
                }, ensure_ascii=False))
                
                # Save screenshot of the specific interaction
                await page.screenshot(path=os.path.join(ts_dir, f"chat_task_{idx:02d}_{task['name'].replace(' ', '_')}.png"))

        except Exception as e:
            print(f"Chat execution failed: {e}")
            await page.screenshot(path=os.path.join(ts_dir, "execution_failure_state.png"))
            
        print(f"\nCompleted Agentic Testing. Full semantic visual proofs logged in: {ts_dir}")
        await browser.close()
        print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(run())