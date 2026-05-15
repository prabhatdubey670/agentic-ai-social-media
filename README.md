# Quanteve Social Media Agent v5
## Multi-Model | Full Logging | Self-Improving | Analytics

## Architecture
```
agent.py (orchestrator)
├── llm_router.py          -> OpenAI + Gemini + Groq + Ollama routing
├── storage.py             -> SQLite activity log
├── content_generator.py   -> Post + comment + DM generation
├── analytics.py           -> Dashboard + CSV export
├── self_improver.py       -> Recursive self-improvement
└── config.py              -> Environment-driven settings
```

## Setup

### 1. Create and activate the venv
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install
```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Configure environment
Copy `.env.example` to `.env` and fill in what you need:
- `OPENROUTER_API_KEY` enables `openrouter/free`, the recommended hosted free-model router.
- `GOOGLE_API_KEY` enables Gemini as fallback.
- `GROQ_API_KEY` enables the fast/cheap post-evaluation model.
- `OPENAI_API_KEY` enables OpenAI as paid fallback.
- `OLLAMA_ENABLED=true` enables a local fallback only if you have hardware for it.
- `ANTHROPIC_ENABLED=true` enables Claude only if you explicitly want it later.
- X.com, LinkedIn, and Telegram credentials are only needed for those features.

### 4. Run modes

Generate local drafts and save them to SQLite queue. This is the default safe mode:
```powershell
python agent.py --mode draft
```

Inspect queued drafts:
```powershell
python agent.py --mode queue
```

Approve a queued item:
```powershell
python agent.py --mode queue --approve QUEUE_ID
```

Full pipeline:
```powershell
python agent.py --mode full --execute
```

Only generate and post content:
```powershell
python agent.py --mode post --execute
```

Only engage with others:
```powershell
python agent.py --mode engage --execute
```

Only analyze performance:
```powershell
python agent.py --mode analyze
```

By default the app runs in dry-run mode. Use `--execute` only when credentials
are configured and you want browser automation to click/post.

## Multi-Model Support

Default routing:
- Post evaluation -> Groq when configured, otherwise fallback
- Comment generation -> OpenRouter free router, Gemini fallback, OpenAI fallback
- Post generation -> OpenRouter free router, Gemini fallback, OpenAI fallback
- DM generation -> OpenRouter free router, Gemini fallback, OpenAI fallback
- Strategy analysis -> OpenRouter free router, Gemini fallback, OpenAI fallback
- Content repurposing -> OpenRouter free router

If a model fails, the router tries the next available provider.

## Hosted Free API Options

There is no hosted LLM API that is truly free without limits. Every provider has
rate limits, quota limits, model availability limits, or abuse controls. The most
practical hosted options are:

- OpenRouter `openrouter/free`: best first option when you do not have local hardware. It routes to currently available free models behind one OpenAI-compatible API. Create a key at https://openrouter.ai and set `OPENROUTER_API_KEY`.
- GroqCloud: good for fast free/cheap inference when your selected model has available quota. Create a key at https://console.groq.com and set `GROQ_API_KEY`.
- Gemini API: useful if your Google project has quota enabled. Set `GOOGLE_API_KEY`, but some projects show zero free quota until billing/access is fixed.

For this repo, use OpenRouter first because it needs no local machine and can
route across free models automatically.

## What Gets Saved
- `posts_seen`: every post evaluated
- `actions_taken`: every like/comment/follow
- `content_generated`: every AI comment/DM/post
- `posts_published`: every post published
- `daily_stats`: daily counters
- `strategy_log`: all strategy insights
- `top_performers`: valuable accounts found
- `error_log`: all errors

## Self-Improvement Loop
After each session, the agent analyzes performance, generates a strategy update
with the configured primary LLM, saves that strategy to SQLite, and uses it in
the next session.

## Analytics Export
```python
from analytics import Analytics
from storage import Database
from llm_router import LLMRouter

db = Database()
llm = LLMRouter()
a = Analytics(db, llm)

a.print_dashboard()
a.export_to_csv("posts_seen", "posts_analysis.csv")
a.export_to_csv("content_generated", "content_analysis.csv")
a.export_to_csv("daily_stats", "stats.csv")
```
