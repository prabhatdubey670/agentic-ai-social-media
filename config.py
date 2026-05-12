"""
config.py - Central configuration for Quanteve Agent v5.

Secrets are read from environment variables so credentials do not live in
source code. Defaults keep the app in local/dry-run mode.
"""

import os


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
        "provider": "anthropic",
        "model": env("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "api_key": env("ANTHROPIC_API_KEY", ""),
    },
    "secondary": {
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
}

TASK_MODEL_MAP = {
    "post_evaluation": "fast",
    "comment_generation": "primary",
    "post_generation": "primary",
    "dm_generation": "primary",
    "strategy_analysis": "primary",
    "content_repurpose": "secondary",
}

# ============================================================
# PLATFORM CREDENTIALS
# ============================================================
X_USERNAME = env("X_USERNAME", "")
X_PASSWORD = env("X_PASSWORD", "")

LINKEDIN_EMAIL = env("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = env("LINKEDIN_PASSWORD", "")

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
REQUIRE_MANUAL_APPROVAL = env_bool("REQUIRE_MANUAL_APPROVAL", True)

# ============================================================
# AGENT IDENTITY
# ============================================================
AGENT_IDENTITY = {
    "name": env("AGENT_NAME", "Prabhat"),
    "company": env("AGENT_COMPANY", "Quanteve Technologies"),
    "description": env(
        "AGENT_DESCRIPTION",
        "Building AI/ML research infrastructure for quantitative finance and data science",
    ),
    "tone": env("AGENT_TONE", "technical, genuine, curious, thoughtful"),
    "avoid": env("AGENT_AVOID", "salesy, generic, promotional, political"),
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
    "x": {"likes": 20, "comments": 6, "follows": 5, "dms": 0, "posts": 2},
    "linkedin": {"likes": 12, "comments": 4, "follows": 3, "dms": 0, "posts": 1},
}

POST_SCHEDULE = {
    "x": ["09:00", "14:00", "19:00"],
    "linkedin": ["09:30", "17:00"],
}

DELAYS = {
    "min_between_actions": 12,
    "max_between_actions": 35,
    "min_between_posts": 180,
    "max_between_posts": 300,
}

DB_PATH = env("DB_PATH", "quanteve_agent.db")
