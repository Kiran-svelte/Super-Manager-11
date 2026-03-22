import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on('console', lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on('pageerror', lambda err: print(f"ERROR: {err}"))
        
        await page.goto("http://localhost:3003")
        await page.wait_for_timeout(3000)
        
        root_html = await page.evaluate('document.getElementById("root").innerHTML')
        print("ROOT HTML 3003:")
        print(root_html)
        
        await browser.close()

asyncio.run(run())
