"""
workers/market_analyst.py — World Trends & Sentiment Analyst
"""

import sys
import os
import json

# Adjust path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_router import LLMRouter
from memory.database import Database
from config import TARGET_TOPICS, AGENT_IDENTITY

class MarketAnalyst:
    def __init__(self, llm: LLMRouter, db: Database):
        self.llm = llm
        self.db = db

    def get_world_summary(self) -> list:
        """Generate a simple 5-point summary of what's happening in the niche world."""
        prompt = f"""You are a research analyst for {AGENT_IDENTITY['name']}.
Topics: {', '.join(TARGET_TOPICS[:10])}

Provide a concise, 5-point bulleted list of current trends, breakthroughs, or major events 
happening in the world of AI, Quant Finance, and Tech research as of late May 2026.

Focus on:
- Technical relevance
- New model releases or research papers
- Market shifts in quant trading
- LLM agent advancements

Return JSON only:
{{
  "summary": [
    "Point 1: ...",
    "Point 2: ...",
    "Point 3: ...",
    "Point 4: ...",
    "Point 5: ..."
  ]
}}"""

        try:
            result, tokens, model = self.llm.complete_json("market_analysis", prompt, max_tokens=600)
            return result.get("summary", ["Error generating summary."])
        except Exception as e:
            print(f"⚠️ World summary failed: {e}")
            return [
                "1. LLM Agents are shifting toward autonomous multi-step reasoning.",
                "2. HFT firms are increasingly integrating real-time transformer models for orderbook prediction.",
                "3. Open-source models (Llama 4 series) are narrowing the gap with closed-source giants.",
                "4. Reinforcement Learning is seeing a resurgence in robotic and financial control systems.",
                "5. Generative AI is moving from 'chatting' to 'doing' via structured tool-use and APIs."
            ]

    def suggest_peers(self) -> list:
        """Suggest 10 niche-relevant peers/influencers."""
        prompt = f"""You are a network growth specialist for {AGENT_IDENTITY['name']}.
Target Niche: {', '.join(TARGET_TOPICS[:5])}

Suggest 10 specific high-value social media accounts (X.com or LinkedIn) 
that post deeply technical or insightful content in this space.

Return JSON only:
{{
  "peers": [
    {{"name": "...", "handle": "...", "platform": "X|LinkedIn", "reason": "..."}},
    ...
  ]
}}"""

        try:
            result, tokens, model = self.llm.complete_json("peer_suggestion", prompt, max_tokens=1000)
            return result.get("peers", [])
        except Exception as e:
            print(f"⚠️ Peer suggestion failed: {e}")
            return []
