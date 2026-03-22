import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on('console', lambda msg: print(f"BROWSER CONSOLE [{msg.type}]: {msg.text}"))
        page.on('pageerror', lambda err: print(f"BROWSER ERROR: {err}"))
        
        # Assume Vite runs on port 3002 or 3003
        import urllib.request
        port = 3002
        try:
            urllib.request.urlopen("http://localhost:3002")
        except:
            port = 3003
            try:
                urllib.request.urlopen("http://localhost:3003")
            except:
                print("Cannot connect to frontend server.")
                return

        print(f"Opening http://localhost:{port} ...")
        await page.goto(f"http://localhost:{port}")
        await page.wait_for_timeout(3000)
        
        await browser.close()

asyncio.run(run())
