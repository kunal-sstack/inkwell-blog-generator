# Inkwell Blog Generator

An Angular blog studio with a Python FastAPI backend and a LangChain prompt → ChatGoogleGenerativeAI (Gemini) → text pipeline. Configure topic, audience, tone, length, keywords and extra direction; edit the result, copy it, or download Markdown.

## Run locally

Install Python 3.11+ and Node.js 22.12+.

In one PowerShell terminal:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python -m uvicorn main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm start
```

Open http://localhost:4200. Backend API documentation: http://127.0.0.1:8000/docs.

You can also start the frontend with `ng serve`: its proxy is configured in `angular.json` for both startup commands. After changing `angular.json` or `proxy.conf.json`, stop and restart the frontend server. http://localhost:4200/api/health should return JSON from the backend, not the Angular page.

## AI configuration

Demo mode needs no API key and returns a clearly labeled template sample. It does not generate AI content and does not apply tone, length, keywords or notes.

AI mode uses Gemini by default. Set `GEMINI_API_KEY` in `backend/.env` and restart the backend. `GOOGLE_API_KEY` is also accepted as a fallback. Optionally set `GEMINI_MODEL` to a model available to your account; the default is `gemini-3.5-flash-lite`. Keep the key on the server; never put it in Angular or commit `.env`. Existing local credentials are preserved by the setup command.

Create a key in [Google AI Studio](https://aistudio.google.com/app/api-keys). Gemini 3.5 Flash-Lite offers a [free tier](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite), subject to account eligibility and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). A key alone does not guarantee available quota. No billing changes are needed in this project. The API returns a helpful message when quota is exhausted or credentials are rejected. To try a sample without an API call, check **Try demo mode**.

The development proxy forwards Angular `/api` calls to the backend. For production, host both behind a reverse proxy serving `/api` to FastAPI. This local starter has no authentication or rate limiting; add both before exposing the AI endpoint publicly.

## Checks

```powershell
cd frontend
npm run build
```

```powershell
cd backend
python -m pytest -q
```

To make one live Gemini request through the same chain used by the app:

```powershell
cd backend
python smoke_gemini.py
```

This consumes API quota and prints only status and word count. `gemini-3.5-flash-lite` was verified with a complete blog draft. You can set `GEMINI_MODEL=gemini-3.8-flash` to use Flash instead if it is available; temporary provider overload can return a 503 response.

Drafts stay in browser memory and are lost on refresh unless downloaded. Word count and reading time reflect the generated draft before edits. The app generates drafts without web research; verify factual claims before publishing.
