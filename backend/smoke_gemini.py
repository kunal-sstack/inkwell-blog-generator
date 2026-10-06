"""One real request through the app's LangChain chain; never print credentials."""
import asyncio
import json

from fastapi import HTTPException
from main import BlogRequest, generate


async def main():
    try:
        result = await generate(BlogRequest(topic="Building a daily reading habit", length="Short", demo=False))
        print(json.dumps({"status": "ok", "words": result["words"], "demo": result["demo"], "has_content": bool(result["content"].strip())}))
    except HTTPException as error:
        print(json.dumps({"status": "failed", "http_status": error.status_code, "detail": error.detail}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    asyncio.run(main())
