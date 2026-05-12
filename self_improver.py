"""
strategies/self_improver.py — Recursive self-improvement engine
Analyzes what worked, updates strategy, improves agent behavior
This is what makes the agent get smarter over time
"""

import json
from datetime import datetime, timedelta
from llm_router import LLMRouter
from storage import Database
from config import AGENT_IDENTITY, TARGET_TOPICS


class SelfImprover:
    """
    Analyzes agent performance and generates improved strategies.
    Run this after each session to make the agent smarter.
    """

    def __init__(self, llm: LLMRouter, db: Database):
        self.llm = llm
        self.db = db

    def analyze_and_improve(self) -> dict:
        """Main improvement cycle — run after each session"""
        print("\n🧠 Running self-improvement analysis...")

        insights = {}

        # 1. Analyze what content performed best
        insights["content"] = self._analyze_content_performance()

        # 2. Analyze engagement patterns
        insights["engagement"] = self._analyze_engagement_patterns()

        # 3. Analyze topic performance
        insights["topics"] = self._analyze_topic_performance()

        # 4. Generate strategy updates via LLM
        try:
            strategy = self._generate_strategy_update(insights)
        except Exception as e:
            print(f"⚠️ Strategy update skipped: {e}")
            strategy = {}

        # 5. Save strategy to DB
        if strategy:
            self.db.save_strategy(
                name=f"auto_strategy_{datetime.now().strftime('%Y%m%d')}",
                insight=json.dumps(insights, indent=2),
                action=strategy.get("actions", ""),
                model=strategy.get("model_used", "")
            )

        return {"insights": insights, "strategy": strategy}

    def _analyze_content_performance(self) -> dict:
        """What type of content gets best engagement?"""
        best_content = self.db.get_best_content(limit=20)
        published = self.db.get_published_posts(limit=20)

        if not best_content and not published:
            return {"status": "insufficient_data"}

        # Summarize patterns
        content_types = {}
        for row in best_content:
            ct = row[0]
            score = row[4] or 0
            content_types[ct] = content_types.get(ct, [])
            content_types[ct].append(score)

        avg_by_type = {k: sum(v)/len(v) for k, v in content_types.items()}

        return {
            "best_content_type": max(avg_by_type, key=avg_by_type.get) if avg_by_type else "unknown",
            "avg_scores": avg_by_type,
            "total_content_generated": len(best_content)
        }

    def _analyze_engagement_patterns(self) -> dict:
        """What actions have highest success rates?"""
        success_rates = self.db.get_action_success_rate()

        if not success_rates:
            return {"status": "insufficient_data"}

        best_action = max(success_rates.items(), key=lambda x: x[1]["rate"]) if success_rates else None

        return {
            "success_rates": success_rates,
            "best_action": best_action[0] if best_action else "unknown",
            "best_rate": best_action[1]["rate"] if best_action else 0
        }

    def _analyze_topic_performance(self) -> dict:
        """Which topics generate highest value posts?"""
        topic_perf = self.db.get_topic_performance()

        if not topic_perf:
            return {"status": "insufficient_data"}

        return {
            "top_topics": [{"topic": r[0], "count": r[1], "avg_score": round(r[2], 2)}
                          for r in topic_perf[:5]],
            "underperforming": [{"topic": r[0], "count": r[1], "avg_score": round(r[2], 2)}
                               for r in topic_perf[-3:]] if len(topic_perf) > 3 else []
        }

    def _generate_strategy_update(self, insights: dict) -> dict:
        """Use LLM to generate actionable strategy from insights"""
        prompt = f"""You are a growth strategy AI for {AGENT_IDENTITY['company']}.

Analyze this performance data and generate specific actionable improvements:

PERFORMANCE INSIGHTS:
{json.dumps(insights, indent=2)}

CURRENT TOPICS: {', '.join(TARGET_TOPICS[:10])}

Generate a strategy update with:
1. What's working — double down on this
2. What's not working — stop or change this
3. New topics to try
4. Content format changes
5. Engagement behavior changes
6. Specific daily actions to take

Return JSON:
{{
  "summary": "2-3 sentence summary of performance",
  "working_well": ["thing1", "thing2"],
  "not_working": ["thing1", "thing2"],
  "new_topics_to_try": ["topic1", "topic2"],
  "content_format_changes": "specific changes to make",
  "engagement_changes": "specific behavior changes",
  "daily_actions": ["action1", "action2", "action3"],
  "actions": "the full strategy text for logging"
}}"""

        result, tokens, model = self.llm.complete_json("strategy_analysis", prompt, max_tokens=1000)
        if result:
            result["model_used"] = model
        return result

    def generate_growth_report(self) -> str:
        """Generate a human-readable growth report"""
        stats = self.db.get_daily_stats(7)
        strategies = self.db.get_strategy_log(5)
        top_posts = self.db.get_top_posts(5)

        prompt = f"""Generate a weekly growth report for {AGENT_IDENTITY['company']} social media agent.

DAILY STATS (last 7 days):
{stats}

RECENT STRATEGIES:
{strategies}

TOP PERFORMING POSTS SEEN:
{top_posts}

Write a clear, actionable report covering:
- Overall performance this week
- Best performing content/topics
- Engagement quality
- Top 3 things to improve next week
- Specific next actions

Format as readable report with sections."""

        text, tokens, model = self.llm.complete("strategy_analysis", prompt, max_tokens=1500)
        return text

    def suggest_new_accounts_to_follow(self) -> dict:
        """Suggest new accounts to engage with based on performance"""
        top_topics = self.db.get_topic_performance()
        best_topics = [t[0] for t in top_topics[:5]] if top_topics else TARGET_TOPICS[:5]

        prompt = f"""Suggest specific Twitter/LinkedIn accounts to follow for someone building:
{AGENT_IDENTITY['description']}

Best performing topics: {', '.join(best_topics)}

Suggest 10 specific accounts (real people in ML/AI/quant/data science) who:
- Post high quality technical content
- Have engaged communities
- Are accessible (not just mega-celebrities)

Return JSON:
{{
  "accounts": [
    {{"handle": "username", "platform": "X|LinkedIn", "reason": "why follow", "niche": "their niche"}},
    ...
  ]
}}"""

        result, tokens, model = self.llm.complete_json("strategy_analysis", prompt, max_tokens=800)
        return result or {}
