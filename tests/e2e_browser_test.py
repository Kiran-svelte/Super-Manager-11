import asyncio
import json
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright

async def run():
    print("Starting Playwright Test...")
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        # Skip onboarding so the chat UI is visible for automation
        await page.add_init_script(
            """
            try {
              localStorage.setItem('onboarding_skipped', 'true');
              localStorage.setItem('super_manager_user_id', 'e2e_user');
            } catch (e) {}
            """
        )

        base_url = os.environ.get("E2E_BASE_URL", "http://localhost:3003")
        print(f"Navigating to {base_url}")

        log_dir = r"d:\GOOGLE PROJECT\test_evidence"
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        console_log_path = os.path.join(log_dir, f"browser_console_{ts}.log")
        pageerror_log_path = os.path.join(log_dir, f"browser_pageerror_{ts}.log")
        transcript_path = os.path.join(log_dir, f"chat_transcript_{ts}.jsonl")

        # Ensure these files exist even if no events fire
        open(console_log_path, "w", encoding="utf-8").close()
        open(pageerror_log_path, "w", encoding="utf-8").close()
        open(transcript_path, "w", encoding="utf-8").close()

        def _append(path: str, line: str):
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        page.on(
            "console",
            lambda msg: _append(
                console_log_path,
                f"[{msg.type}] {msg.text}"
                + (f" ({msg.location.get('url')}:{msg.location.get('lineNumber')})" if getattr(msg, "location", None) else ""),
            ),
        )
        page.on("pageerror", lambda err: _append(pageerror_log_path, str(err)))
        try:
            await page.goto(base_url, timeout=30000)
            print("Successfully loaded homepage")
        except Exception as e:
            print(f"Failed to load homepage: {e}")
            await browser.close()
            return

        # Screenshot Homepage
        await page.screenshot(path=os.path.join(log_dir, f"homepage_{ts}.png"))
        print(f"Screenshot saved: {log_dir}\\homepage_{ts}.png")
        print(f"Console log saved: {console_log_path}")
        print(f"Page error log saved: {pageerror_log_path}")

        # Verify Title or Content
        content = await page.content()
        if "Super Manager" in content:
            print("Verified: 'Super Manager' text found on page.")
        else:
            print("Warning: 'Super Manager' text NOT found on page.")

        # Find Input and Run 10 Prompts
        try:
            await page.wait_for_selector(".input-wrapper input", timeout=30000)
            await page.wait_for_selector(".send-btn", timeout=30000)

            prompts = [
                "Hello — confirm you're online.",
                "Summarize CORS in one paragraph.",
                "Draft a short, polite email to reschedule a meeting.",
                "Create a 5-item checklist for deploying a FastAPI app.",
                "Write a Python function that validates an email string.",
                "Explain what a circuit breaker is (software).",
                "Generate a short agenda for a 30-minute project kickoff meeting.",
                "Give me a JSON object with keys: name, priority, due_date, notes.",
                "Write a regex that matches http://localhost:<port>.",
                "Provide 3 tips to speed up a slow React app.",
            ]

            ai_locator = page.locator(".message.message-ai .msg-ai-content")

            for idx, prompt in enumerate(prompts, start=1):
                before_count = await ai_locator.count()

                await page.fill(".input-wrapper input", prompt)
                await page.click(".send-btn")
                print(f"[{idx}/10] Sent prompt")

                await page.wait_for_function(
                    "before => document.querySelectorAll('.message.message-ai .msg-ai-content').length > before",
                    arg=before_count,
                    timeout=60000,
                )

                after_count = await ai_locator.count()
                last_text = (await ai_locator.nth(after_count - 1).inner_text()).strip()

                _append(
                    transcript_path,
                    json.dumps(
                        {"i": idx, "prompt": prompt, "response": last_text},
                        ensure_ascii=False,
                    ),
                )

                await page.screenshot(path=os.path.join(log_dir, f"chat_task_{idx:02d}_{ts}.png"))
                print(f"[{idx}/10] Got response ({len(last_text)} chars)")

            await page.screenshot(path=os.path.join(log_dir, f"chat_interaction_{ts}.png"))
            print(f"Transcript saved: {transcript_path}")

        except Exception as e:
            print(f"Interaction failed: {e}")
            await page.screenshot(path=os.path.join(log_dir, f"error_state_{ts}.png"))

        await browser.close()
        print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(run())
