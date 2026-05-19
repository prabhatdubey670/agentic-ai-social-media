# SOTA Modular AI Agent Architecture Plan (2026)

## 🎯 Objective
Transition the current monolithic `agent.py` into a **Modular Multi-Agent System (MAS)** using the **Supervisor-Worker** pattern. This architecture is designed for extreme scalability, allowing us to add features like VIP monitoring, sentiment analysis, and new social platforms without breaking core logic.

---

## 🏗️ The New Structure

```text
quanteve_agent/
│
├── orchestrator/           # The Supervisor (State & Routing)
│   ├── main.py             # Entry point (CLI parser)
│   └── workflow.py         # Defines the graph/path of tasks
│
├── workers/                # Specialized Cognitive Agents
│   ├── content_creator.py  # Logic for drafting posts/replies
│   ├── network_scout.py    # Logic for finding VIPs & evaluating peers
│   └── market_analyst.py   # Logic for trend & sentiment analysis
│
├── platforms/              # The Execution Layer (Platform Agnostic)
│   ├── base_platform.py    # Common interface (login, post, engage)
│   ├── x_platform.py       # Tweepy + Playwright Search
│   └── linkedin_platform.py# REST API + Playwright Stealth
│
└── memory/                 # The Data & Context Layer
    ├── database.py         # Migrated from storage.py (SQLite)
    └── context_store.py    # NEW: Logic for session persistence & VIP lists
```

---

## 🛠️ Implementation Phases

### Phase 1: Structural Foundation (The Skeleton)
*   Create new directories.
*   Extract `storage.py` into `memory/database.py`.
*   Extract `llm_router.py` into a shared core service.
*   Update all imports to maintain existing functionality.

### Phase 2: Decoupling the "Hands" (Platforms)
*   **Target**: Rip platform logic out of `agent.py`.
*   Move `XAgent` and `LinkedInAgent` to `platforms/`.
*   **Result**: Platforms become "dumb" tools that simply receive text and click buttons or call APIs. They no longer decide *what* to say.

### Phase 3: Decoupling the "Brain" (Workers)
*   **Target**: Isolate AI generation.
*   Move prompt engineering and generation logic into `workers/content_creator.py`.
*   Implement the **Network Scout** worker to handle the new "VIP tracking" logic.

### Phase 4: The Orchestrator (The Boss)
*   Implement the central loop in `orchestrator/main.py`.
*   **New Flow**:
    1.  Orchestrator asks **Network Scout** for targets.
    2.  Orchestrator asks **Content Creator** for a draft.
    3.  Orchestrator asks **Platform** to execute.
*   Enforce safety limits (2h gap, 10 posts/day) at this top level.

---

## 🚀 Scalability Features
1.  **VIP Monitoring**: Easily plug in a loop that visits peer profiles and saves their data to the database.
2.  **Market Sentiment**: A weekly cron job can pass all `posts_seen` to the **Market Analyst** worker to generate a report.
3.  **New Platforms**: Adding Instagram or Mastodon only requires one new file in `platforms/`.

---

## 🛡️ Security & Stability
*   **Persistent Context**: All browser sessions are cached to prevent repetitive logins.
*   **Error Bubbling**: Platform errors (like 401/403) are caught by the Orchestrator, which can decide to retry or switch platforms.
