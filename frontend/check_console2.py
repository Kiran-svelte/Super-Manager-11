import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # intercept console logs AND evaluate a window.onerror listener to catch everything
        page.on('console', lambda msg: print(f"CONSOLE: {msg.text}"))
        
        await page.goto("http://localhost:3002")
        await page.wait_for_timeout(3000)
        
        await browser.close()

asyncio.run(run())
