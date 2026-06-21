import asyncio
from google import genai
import os

async def main():
    client = genai.Client(api_key="fake")
    try:
        response = await client.aio.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents='say hi'
        )
        print(type(response))
    except Exception as e:
        print(f"Exception type: {type(e)}")

asyncio.run(main())
