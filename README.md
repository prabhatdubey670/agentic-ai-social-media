# Quanteve Social Media Agent v5
## Multi-Model | Full Logging | Self-Improving | Analytics

## Architecture
```
agent.py (orchestrator)
├── core/
│   ├── llm_router.py     → Claude + GPT + Groq + Ollama routing
│   └── storage.py        → SQLite — saves EVERYTHING
├── agents/
│   └── content_generator.py → Post + comment + DM generation
├── analysis/
│   └── analytics.py      → Dashboard + CSV export
├── strategies/
│   └── self_improver.py  → Recursive self-improvement
└── config.py             → All settings here
```

## Setup

### 1. Install
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure config.py
Fill in your API keys:
- Anthropic API key (required)
- OpenAI API key (optional)
- Groq API key (optional — free tier available at groq.com)
- Ollama (optional — free local models)
- Telegram bot token + chat ID
- X.com credentials
- LinkedIn credentials

### 3. Run modes

Generate local drafts and save them to SQLite queue. This is the default safe mode:
```bash
python agent.py --mode draft
```

Inspect queued drafts:
```bash
python agent.py --mode queue
```

Approve a queued item:
```bash
python agent.py --mode queue --approve QUEUE_ID
```

Full pipeline (post + engage + analyze):
```bash
python agent.py --mode full --execute
```

Only generate and post content:
```bash
python agent.py --mode post --execute
```

Only engage with others:
```bash
python agent.py --mode engage --execute
```

Only analyze performance:
```bash
python agent.py --mode analyze
```

By default the app runs in dry-run mode. Use `--execute` only when credentials
are configured and you want the browser automation to click/post.

## Multi-Model Support

The agent automatically routes tasks to the best model:
- Post evaluation → Groq (fast + cheap)
- Comment generation → Claude (best quality)
- Post generation → Claude (best quality)
- Strategy analysis → Claude (deep thinking)
- Content repurposing → GPT-4o-mini (good enough)

If a model fails → automatically falls back to next available.

## What Gets Saved (SQLite DB)
- `posts_seen` — every post evaluated
- `actions_taken` — every like/comment/follow
- `content_generated` — every AI comment/DM/post
- `posts_published` — every post published
- `daily_stats` — daily counters
- `strategy_log` — all strategy insights
- `top_performers` — valuable accounts found
- `error_log` — all errors

## Self-Improvement Loop
After each session, the agent:
1. Analyzes what content/topics performed best
2. Checks action success rates
3. Generates strategy update via Claude
4. Saves updated strategy to DB
5. Next session uses improved strategy

This makes the agent recursively smarter over time.

## Kafka (optional)
Set `KAFKA["enabled"] = True` in config.py.
Topics automatically created:
- agent.posts.seen
- agent.actions.taken
- agent.content.generated
- agent.errors

## Analytics Export
```python
from analysis.analytics import Analytics
from core.storage import Database
from core.llm_router import LLMRouter

db = Database()
llm = LLMRouter()
a = Analytics(db, llm)

# Print dashboard
a.print_dashboard()

# Export to CSV for Excel
a.export_to_csv("posts_seen", "posts_analysis.csv")
a.export_to_csv("content_generated", "content_analysis.csv")
a.export_to_csv("daily_stats", "stats.csv")
```

## Hosting
- Local + Task Scheduler: Schedule daily at 9am
- VPS (Hostinger ₹300/month): Run 24/7
- Docker: containerize easily
