"""
config.py - Central configuration for Quanteve Agent v5.

Secrets are read from environment variables so credentials do not live in
source code. Defaults keep the app in local/dry-run mode.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ============================================================
# AI MODEL CONFIG
# ============================================================
MODELS = {
    "primary": {
        "provider": "openrouter",
        "model": env("OPENROUTER_MODEL", "openrouter/free"),
        "api_key": env("OPENROUTER_API_KEY", ""),
        "base_url": env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    },
    "secondary": {
        "provider": "google_genai",
        "model": env("GOOGLE_MODEL", "gemini-2.0-flash-lite"),
        "api_key": env("GOOGLE_API_KEY", ""),
    },
    "openai": {
        "provider": "openai",
        "model": env("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key": env("OPENAI_API_KEY", ""),
    },
    "fast": {
        "provider": "groq",
        "model": env("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "api_key": env("GROQ_API_KEY", ""),
    },
    "local": {
        "provider": "ollama",
        "model": env("OLLAMA_MODEL", "llama3.2"),
        "base_url": env("OLLAMA_BASE_URL", "http://localhost:11434"),
        "enabled": env_bool("OLLAMA_ENABLED", False),
    },
    "claude": {
        "provider": "anthropic",
        "model": env("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "api_key": env("ANTHROPIC_API_KEY", ""),
        "enabled": env_bool("ANTHROPIC_ENABLED", False),
    },
}

TASK_MODEL_MAP = {
    "post_evaluation": "fast",
    "comment_generation": "primary",
    "post_generation": "primary",
    "dm_generation": "primary",
    "strategy_analysis": "primary",
    "content_repurpose": "primary",
}

# ============================================================
# PLATFORM CREDENTIALS
# ============================================================
X_USERNAME = env("X_USERNAME", "")
X_PASSWORD = env("X_PASSWORD", "")
X_HANDLE = env("X_HANDLE", "")
X_API_BEARER_TOKEN = env("X_API_BEARER_TOKEN", "")
X_API_BASE_URL = env("X_API_BASE_URL", "https://api.x.com")

# X API v2 (Tweepy)
X_API_KEY = env("X_API_KEY", "")
X_API_SECRET = env("X_API_SECRET", "")
X_ACCESS_TOKEN = env("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = env("X_ACCESS_TOKEN_SECRET", "")

LINKEDIN_EMAIL = env("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = env("LINKEDIN_PASSWORD", "")
LINKEDIN_ACCESS_TOKEN = env("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN = env("LINKEDIN_AUTHOR_URN", "") # e.g. urn:li:person:XXXXX

# ============================================================
# NOTIFICATIONS
# ============================================================
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", "")

# ============================================================
# KAFKA
# ============================================================
KAFKA = {
    "enabled": env_bool("KAFKA_ENABLED", False),
    "bootstrap_servers": env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
}

# ============================================================
# AUTOMATION SAFETY
# ============================================================
DRY_RUN_DEFAULT = env_bool("DRY_RUN_DEFAULT", True)
BROWSER_HEADLESS = env_bool("BROWSER_HEADLESS", False)
REQUIRE_MANUAL_APPROVAL = False

# ============================================================
# AGENT IDENTITY
# ============================================================
AGENT_IDENTITY = {
    "name": env("AGENT_NAME", "Prabhat"),
    "company": env("AGENT_COMPANY", ""), # Removed company name for now
    "description": env(
        "AGENT_DESCRIPTION",
        "Self-taught developer and quant researcher building AI/ML infrastructure and exploring deep learning systems.",
    ),
    "tone": env("AGENT_TONE", "technical, genuine, curious, thoughtful"),
    "avoid": env("AGENT_AVOID", "salesy, generic, promotional, political, company-focused"),
}

# ============================================================
# TARGET AUDIENCE
# ============================================================
TARGET_TOPICS = [
    "machine learning", "deep learning", "data science",
    "quantitative finance", "algorithmic trading", "AI research",
    "LLM agents", "reinforcement learning", "time series forecasting",
    "market microstructure", "HFT", "quant", "python ML",
    "neural networks", "transformer models", "AI startup",
]

TARGET_ACCOUNTS = [
    # Add specific accounts to track.
]

# ============================================================
# DAILY LIMITS
# ============================================================
DAILY_LIMITS = {
    "x": {"likes": 8, "comments": 2, "follows": 0, "dms": 0, "posts": 1},
    "linkedin": {"likes": 5, "comments": 1, "follows": 0, "dms": 0, "posts": 1},
}

POST_SCHEDULE = {
    "x": ["09:00", "14:00", "19:00"],
    "linkedin": ["09:30", "17:00"],
}

DELAYS = {
    "min_between_actions": 30,
    "max_between_actions": 60,
    "min_between_posts": 60, # Reduced from 900 for faster testing
    "max_between_posts": 120,
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = env("DB_PATH", os.path.join(BASE_DIR, "quanteve_agent.db"))
