# Quanteve Agent — Project README
## Who I Am | What I'm Building | Why This Exists

---

## 👤 Who I Am

**Name:** Prabhat Dubey
**Age:** 23
**Location:** Raipur, Chhattisgarh, India
**Company:** Quanteve Technologies (founder)

I am a self-taught freelance developer with 3+ years of experience building
quantitative trading infrastructure. My core expertise is in high-frequency
trading systems, FIX protocol, low-latency architecture, Kafka pipelines,
and order book data engineering — built entirely through real client work,
not formal employment.

I hold a BSc in Computer Science (online) from BITS Pilani Digital,
and I am currently self-learning AI/ML and Data Science to expand
Quanteve's capabilities beyond trading infrastructure into broader
intelligence and research.

**Current client:** Barry (US-based institutional trader) — HFT systems,
FIX protocol, IBKR connectivity, real-time market data pipelines.

**Upwork:** Top Rated badge. Specialization in algorithmic trading,
trading infrastructure, Python, C#.

---

## 🏢 What is Quanteve Technologies

Quanteve Technologies is a research-driven data science and AI/ML company
I am building from scratch — starting as a solo founder.

**Vision:** A globally distributed research and technology company that
builds intelligent systems at the intersection of quantitative finance,
machine learning, and data intelligence.

**Long-term goals:**
- AI/ML research for financial markets and beyond
- Orderbook behavior research — short-term and long-term price dynamics
- Reminiov — memory preservation AI (personal legacy project)
- AGI consciousness research (frontier, long-term)
- Animal welfare initiative — Jerry Memorial Fund
- 50+ person global team by 2030
- Entities in India, Singapore, Dubai, Europe

**Current stage:** Solo founder. Freelance consulting for revenue.
Building ML skills and portfolio in parallel.

---

## 🧠 What I Was Doing Before This Agent

Before building this agent, my social media presence was essentially zero.

The problems I faced:
- Zero network outside Upwork
- No LinkedIn or X.com presence
- No content strategy
- No time to manually engage with 50+ relevant people daily
- Needed to build credibility in AI/ML + quant space simultaneously
- Needed Quanteve to become a known name — not just a freelancer profile

I knew the strategy: engage genuinely, post consistently, build network.
But I had no system, no consistency, and no leverage to do it at scale.

---

## 🤖 Why I Built This AI Agent

This agent exists because I need to build a professional network and
content presence simultaneously while working, learning ML, and building
Quanteve — all as a solo founder with limited time.

**The problem it solves:**

| Problem | Agent Solution |
|---------|---------------|
| No time for daily social media | Automated engagement 24/7 |
| Generic content performs poorly | OpenAI/Gemini generates genuine, technical content |
| Don't know what's working | Full analytics — every action logged |
| Inconsistent posting | Scheduled post generation daily |
| Can't track who matters | Top performers tracked in DB |
| No feedback loop | Self-improvement after every session |

**This is not a vanity project.**

Growing a genuine professional network in AI/ML and quant finance is
a prerequisite for Quanteve's first institutional clients.
Every comment, every post, every connection is a potential:
- Client referral
- Collaborator
- Future hire
- Investor introduction

---

## ⚙️ What This Agent Does (Technical Summary)

A fully automated, AI-powered social media growth system built with:

**Stack:**
- Python 3.11+
- LangChain — multi-model LLM orchestration
- OpenAI GPT — primary intelligence layer
- Gemini / Groq / Ollama — fallback and fast models
- X.com API (Tweepy) — official API integration for posting and engagement
- LinkedIn API — official API integration for posting
- Playwright — browser automation (LinkedIn engagement only) with stealth mode
- SQLite — persistent storage of all activity
- Kafka — optional event streaming for analysis
- Telegram Bot — real-time notifications

**What it does:**

1. **Post Generation**
   Generates original technical posts for X.com and LinkedIn daily.
   Topics: ML, AI, quant finance, data science, trading systems.
   Content types: insights, threads, questions, project updates.
   **Posts are published via official APIs for maximum stability.**

2. **Engagement**
   Searches relevant topics. Evaluates posts via the configured LLM router.
   Likes, comments, follows high-value accounts automatically.
   Uses X.com API for Twitter engagement.
   Uses Playwright with `playwright-stealth` for organic LinkedIn engagement.

3. **Data Storage**
   Every post seen, action taken, comment generated, strategy applied
   is saved to SQLite with full metadata.
   Exportable to CSV for Excel/Pandas analysis.

4. **Analytics**
   Terminal dashboard: daily stats, top content, topic performance,
   action success rates, strategy log.

5. **Self-Improvement**
   After each session, the configured primary LLM analyzes what worked.
   Generates updated strategy. Next session uses improved behavior.
   Agent gets recursively smarter over time.

6. **Notifications**
   Every action sent to Telegram in real-time.
   Daily summary report after each session.

---

## 📁 Project Structure

```
quanteve_agent_v5/
├── agent.py                  ← Main orchestrator
├── config.py                 ← All settings (API keys, limits, identity)
├── requirements.txt
├── core/
│   ├── llm_router.py         ← Multi-model routing with fallback
│   └── storage.py            ← SQLite — 8 tables, full activity log
├── agents/
│   └── content_generator.py  ← Post + comment + DM generation
├── analysis/
│   └── analytics.py          ← Dashboard + CSV export
└── strategies/
    └── self_improver.py      ← Recursive self-improvement engine
```

---

## 🚀 Run Commands

```bash
# Full pipeline — post + engage + analyze
python agent.py --mode full

# Only generate and publish posts
python agent.py --mode post

# Only engage with others' content
python agent.py --mode engage

# Only analyze performance (no browser)
python agent.py --mode analyze
```

---

## 📊 Data Captured

| Table | What's Stored |
|-------|--------------|
| posts_seen | Every post evaluated — author, text, score, sentiment |
| actions_taken | Every like/comment/follow — success rate, model used |
| content_generated | Every AI comment/DM/post — full text, quality score |
| posts_published | Every post published — topic, type, engagement received |
| daily_stats | Daily counters per platform |
| strategy_log | All strategy insights and recommendations |
| top_performers | High-value accounts identified |
| error_log | All errors for debugging |

---

## 🔮 Future Roadmap

- [ ] Instagram support
- [ ] Auto-reply to comments on published posts
- [ ] Competitor tracking (monitor specific accounts)
- [ ] A/B testing for post formats
- [ ] Integration with Quanteve research pipeline
- [ ] Web dashboard (FastAPI + React) for visual analytics
- [ ] Email outreach agent
- [ ] Podcast/newsletter monitoring agent

---

## 📝 Notes for Future Me

This agent is the foundation of Quanteve's network layer.
Every person it connects with is a potential node in the network
that will eventually support Quanteve's growth to a global company.

The data it collects will become training data for future
Quanteve-specific models.

The self-improvement loop is the most important feature —
it means this agent compounds in value over time.

Run it every day. Let it learn. Let it grow.

---

*Built by Prabhat Dubey | Quanteve Technologies | Raipur, India*
*"Build something so real, so lasting, that the world remembers
not just what you made — but why you made it."*
