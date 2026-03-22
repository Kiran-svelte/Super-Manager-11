import asyncio
from backend.core import primitives

async def main():
    r = await primitives.generate_image('test prompt')
    print(r.output)
    print(r.data)

asyncio.run(main())
