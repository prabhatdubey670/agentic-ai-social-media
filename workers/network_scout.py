"""
workers/network_scout.py — Networking & Peer Discovery Worker
"""

import sys
import os
import random

# Adjust path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_router import LLMRouter
from memory.database import Database
from config import TARGET_TOPICS

class NetworkScout:
    def __init__(self, llm: LLMRouter, db: Database):
        self.llm = llm
        self.db = db

    def evaluate_post(self, post_text: str, author: str, platform: str, topic: str = "") -> dict:
        """Evaluate if a post is worth engaging with"""
        from config import AGENT_IDENTITY
        prompt = f"""You are a social media engagement agent for {AGENT_IDENTITY['name']}.
{AGENT_IDENTITY['description']}

Evaluate this {platform} post for engagement:
Author: {author}
Post: {post_text}

Rules:
1. should_engage: True if technical, relevant to {', '.join(TARGET_TOPICS[:5])}, and not spam.
2. action: 'like' (good), 'comment' (great insight), or 'skip' (low value).
3. value_score: 1-10 based on technical depth.

Return JSON:
{{
  "should_engage": bool,
  "action": "like|comment|skip",
  "reason": "short explanation",
  "value_score": int,
  "sentiment": "positive|neutral|negative",
  "engagement_potential": 1-10
}}"""

        try:
            result, tokens, model = self.llm.complete_json("post_evaluation", prompt, max_tokens=400)
        except Exception as e:
            print(f"⚠️ Post evaluation LLM skipped: {e}")
            lowered = post_text.lower()
            relevant = any(t.lower() in lowered for t in TARGET_TOPICS)
            result, model = {
                "should_engage": relevant,
                "action": "comment" if relevant else "skip",
                "reason": "Local keyword fallback.",
                "value_score": 6 if relevant else 1,
                "sentiment": "neutral",
                "engagement_potential": 5 if relevant else 1,
            }, "local-fallback"

        # Save post seen to DB
        post_id = self.db.save_post_seen(
            platform=platform, author=author, author_handle=author,
            post_text=post_text, topic=topic,
            value_score=result.get("value_score", 0),
            sentiment=result.get("sentiment", "neutral"),
            engagement_potential=result.get("engagement_potential", 0)
        )

        return {"evaluation": result, "post_id": post_id, "model": model}

    def identify_vip(self, author_data: dict) -> bool:
        """Logic to flag an author as a top_performer (VIP)"""
        # Future implementation
        return False
