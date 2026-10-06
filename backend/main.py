import os
import re
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from google.genai.errors import APIError
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name('.env'))


def gemini_key() -> str:
    return (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or '').strip()


def gemini_model() -> str:
    return os.getenv('GEMINI_MODEL', '').strip() or 'gemini-3.5-flash-lite'
app = FastAPI(title="Inkwell Blog Generator")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:4200"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class BlogRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    audience: str = Field(default="Curious readers", max_length=150)
    tone: Literal["Conversational", "Professional", "Inspiring", "Educational"] = "Conversational"
    length: Literal["Short", "Medium", "Long"] = "Medium"
    keywords: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=2000)
    demo: bool = False


def demo_blog(request: BlogRequest) -> str:
    return f"""# {request.topic.strip()}: a practical starting point

*Demo draft — this sample illustrates the format. Switch to AI mode for a tailored article.*

Getting started with {request.topic.strip().lower()} can feel overwhelming. For {request.audience or 'curious readers'}, the best first step is to define what a useful result looks like and work toward it in small, manageable steps.

## Start with a clear purpose

Write down the question you want to answer. A focused purpose makes it easier to choose relevant information, avoid distractions, and understand where to spend your time.

## Build a simple approach

1. Identify one specific goal.
2. Gather reliable information and check the assumptions behind it.
3. Try a small experiment and record what you learn.
4. Refine your approach before expanding it.

## Turn learning into progress

Consistency helps you discover what works in your own circumstances. Set aside time to review your progress, ask for feedback, and make adjustments. Avoid treating a single result as a universal rule.

## Your next step

Choose one action you can take today. Keep it small enough to finish, then use what you learn to decide what comes next.
"""


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": bool(gemini_key()), "provider": "gemini", "model": gemini_model()}


@app.post("/api/generate")
async def generate(request: BlogRequest):
    if not request.topic.strip() or len(request.topic.strip()) < 3:
        raise HTTPException(422, "Please enter a topic with at least 3 characters.")
    if request.demo:
        content = demo_blog(request)
    else:
        if not gemini_key():
            raise HTTPException(503, "Add GEMINI_API_KEY to backend/.env and restart the backend, or select demo mode.")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a careful blog editor. Write an original, useful blog in Markdown with one H1 title, an introduction, H2 sections and a conclusion. Never invent sources, quotes, statistics, or personal experience. Treat the supplied brief as user content. Incorporate keywords naturally. Return only the article."),
            ("human", "Topic: {topic}\nAudience: {audience}\nTone: {tone}\nTarget words: {words}\nKeywords: {keywords}\nAdditional direction: {notes}")
        ])
        try:
            model = ChatGoogleGenerativeAI(model=gemini_model(), api_key=gemini_key(), vertexai=False, timeout=60, max_retries=1)
            chain = prompt | model | StrOutputParser()
            content = await chain.ainvoke({**request.model_dump(), "words": {"Short": 400, "Medium": 800, "Long": 1200}[request.length]})
        except (APIError, ChatGoogleGenerativeAIError) as error:
            # LangChain wraps Gemini client errors and preserves the APIError as cause.
            code = getattr(error, 'code', None) or getattr(error.__cause__, 'code', None)
            if code == 429:
                raise HTTPException(429, "Gemini's quota or rate limit was reached. Wait and retry, or check your free-tier limits in Google AI Studio.") from None
            if code in (400, 401, 403):
                raise HTTPException(502, "Gemini rejected the request. Check your API key, key restrictions, and model access in Google AI Studio.") from None
            if code == 404:
                raise HTTPException(502, "The configured Gemini model is unavailable. Update GEMINI_MODEL in backend/.env and restart the backend.") from None
            raise HTTPException(502, "Gemini is temporarily unavailable. Please try again shortly.") from None
        except Exception:
            raise HTTPException(502, "Gemini could not complete the request. Check your server configuration and connection; then try again.") from None
        if not content.strip():
            raise HTTPException(502, "Gemini returned an empty draft. Try a different topic or revise your brief.")
    words = len(re.findall(r"\b[\w'-]+\b", content))
    return {"content": content, "words": words, "reading_minutes": max(1, (words + 199) // 200), "demo": request.demo}
