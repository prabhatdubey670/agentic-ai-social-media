"""
agents/content_generator.py — AI post generation
Generates original posts for X.com and LinkedIn
Multiple content types: technical, insight, question, thread
"""

import random
from datetime import datetime
from llm_router import LLMRouter
from storage import Database
from config import AGENT_IDENTITY, TARGET_TOPICS


CONTENT_TYPES = ["technical_insight", "question", "lesson_learned",
                  "project_update", "industry_observation", "thread"]

LINKEDIN_TYPES = ["thought_leadership", "project_showcase",
                   "industry_insight", "personal_journey", "how_to"]


class ContentGenerator:
    def __init__(self, llm: LLMRouter, db: Database):
        self.llm = llm
        self.db = db

    def _fallback_x_post(self, topic: str, post_type: str) -> dict:
        text = (
            f"Learning {topic} is forcing me to think in systems, not buzzwords. "
            "The useful question is not 'can this model work?' but 'what signal, "
            "feedback loop, and failure mode are we actually measuring?'"
        )
        return {
            "post_text": text[:280],
            "post_type": post_type,
            "topic": topic,
            "estimated_engagement": "medium",
            "reasoning": "Local fallback draft generated without an LLM provider.",
            "best_time_to_post": "morning",
            "hashtags": [],
            "model_used": "local-template",
        }

    def _fallback_linkedin_post(self, topic: str, post_type: str) -> dict:
        text = (
            f"I have been thinking about {topic} from the perspective of building real systems.\n\n"
            "The hard part is rarely the demo. It is the data quality, the feedback loop, "
            "the failure cases, and the discipline to measure whether the system is actually "
            "improving.\n\n"
            "That mindset from trading infrastructure transfers directly into AI/ML work: "
            "latency, observability, edge cases, and honest evaluation matter more than hype.\n\n"
            "What is one failure mode you now check earlier than you used to?"
        )
        return {
            "post_text": text,
            "post_type": post_type,
            "topic": topic,
            "hook": f"What does {topic} look like when it becomes infrastructure?",
            "estimated_engagement": "medium",
            "reasoning": "Local fallback draft generated without an LLM provider.",
            "hashtags": ["AI", "MachineLearning", "DataScience"],
            "model_used": "local-template",
        }

    def _fallback_comment(self, post_text: str, platform: str) -> dict:
        snippet = " ".join(post_text.split()[:12])
        return {
            "comment": (
                f"This point about \"{snippet}\" is worth separating into signal, "
                "measurement, and operational risk. That is usually where the real lesson is."
            ),
            "approach": "technical reflection",
            "value_added": "Adds a systems-thinking angle.",
            "model_used": "local-template",
        }

    def generate_x_post(self, topic: str = None, post_type: str = None) -> dict:
        """Generate an original X.com post"""
        topic = topic or random.choice(TARGET_TOPICS)
        post_type = post_type or random.choice(CONTENT_TYPES)

        # Get recent performance for context
        top_topics = self.db.get_topic_performance()
        best_topics = [t[0] for t in top_topics[:3]] if top_topics else TARGET_TOPICS[:3]

        prompt = f"""You are {AGENT_IDENTITY['name']}.
{AGENT_IDENTITY['description']}

Generate an original X.com post about: {topic}
Post type: {post_type}
Tone: {AGENT_IDENTITY['tone']}

High performing topics recently: {', '.join(best_topics)}

Rules:
- Max 280 characters for single post
- If thread: write 3-5 connected tweets separated by "---TWEET---"
- No hashtag spam (max 2 relevant hashtags)
- Technical but accessible
- Share genuine insight or ask thought-provoking question
- Never promotional

Return JSON only:
{{
  "post_text": "the actual post content",
  "post_type": "{post_type}",
  "topic": "{topic}",
  "estimated_engagement": "low|medium|high",
  "reasoning": "why this post will resonate",
  "best_time_to_post": "morning|afternoon|evening",
  "hashtags": ["tag1", "tag2"]
}}"""

        try:
            result, tokens, model = self.llm.complete_json("post_generation", prompt, max_tokens=800)
        except Exception as e:
            print(f"⚠️ X post LLM generation skipped: {e}")
            result, tokens, model = self._fallback_x_post(topic, post_type), 0, "local-template"

        if result:
            # Save to DB
            content_id = self.db.save_content(
                content_type="x_post",
                platform="X.com",
                target_author="",
                input_context=f"topic:{topic} type:{post_type}",
                generated_text=result.get("post_text", ""),
                tokens=tokens,
                model=model,
                quality_score={"low": 3, "medium": 6, "high": 9}.get(
                    result.get("estimated_engagement", "medium"), 5)
            )
            result["content_id"] = content_id
            result["model_used"] = model

        return result

    def generate_linkedin_post(self, topic: str = None, post_type: str = None) -> dict:
        """Generate an original LinkedIn post"""
        topic = topic or random.choice(TARGET_TOPICS)
        post_type = post_type or random.choice(LINKEDIN_TYPES)

        prompt = f"""You are {AGENT_IDENTITY['name']}.
{AGENT_IDENTITY['description']}

Generate a LinkedIn post about: {topic}
Post type: {post_type}
Tone: {AGENT_IDENTITY['tone']}

LinkedIn post rules:
- 150-300 words ideal
- Start with a hook (first line must grab attention)
- Use line breaks for readability (short paragraphs)
- End with a question to drive comments
- 3-5 relevant hashtags at bottom
- Share genuine expertise, no fluff
- Can be slightly personal/story-driven

Return JSON only:
{{
  "post_text": "full post with line breaks",
  "post_type": "{post_type}",
  "topic": "{topic}",
  "hook": "just the opening line",
  "estimated_engagement": "low|medium|high",
  "reasoning": "why this will work on LinkedIn",
  "hashtags": ["tag1", "tag2", "tag3"]
}}"""

        try:
            result, tokens, model = self.llm.complete_json("post_generation", prompt, max_tokens=1000)
        except Exception as e:
            print(f"⚠️ LinkedIn post LLM generation skipped: {e}")
            result, tokens, model = self._fallback_linkedin_post(topic, post_type), 0, "local-template"

        if result:
            content_id = self.db.save_content(
                content_type="linkedin_post",
                platform="LinkedIn",
                target_author="",
                input_context=f"topic:{topic} type:{post_type}",
                generated_text=result.get("post_text", ""),
                tokens=tokens,
                model=model,
                quality_score={"low": 3, "medium": 6, "high": 9}.get(
                    result.get("estimated_engagement", "medium"), 5)
            )
            result["content_id"] = content_id
            result["model_used"] = model

        return result

    def repurpose_content(self, original_text: str, from_platform: str, to_platform: str) -> dict:
        """Repurpose content from one platform to another"""
        prompt = f"""Repurpose this {from_platform} content for {to_platform}:

Original: {original_text}

Adapt tone, length, and format for {to_platform}.
Keep the core insight but optimize for the platform.

Return JSON:
{{
  "repurposed_text": "adapted content",
  "changes_made": "what was changed and why"
}}"""

        result, tokens, model = self.llm.complete_json("content_repurpose", prompt, max_tokens=600)

        if result:
            self.db.save_content(
                content_type="repurposed",
                platform=to_platform,
                target_author="",
                input_context=original_text[:300],
                generated_text=result.get("repurposed_text", ""),
                tokens=tokens,
                model=model
            )

        return result

    def generate_comment(self, post_text: str, author: str, platform: str) -> dict:
        """Generate a genuine comment for a post"""
        prompt = f"""You are {AGENT_IDENTITY['name']}.

Write a genuine, valuable comment on this {platform} post:

Author: {author}
Post: {post_text}

Rules:
- 1-3 sentences max
- Add actual value (insight, question, experience)
- Never generic ("great post!", "so true!")
- Reference something specific from the post
- Natural conversational tone

Return JSON:
{{
  "comment": "the comment text",
  "approach": "what angle you took",
  "value_added": "what value this adds to the conversation"
}}"""

        try:
            result, tokens, model = self.llm.complete_json("comment_generation", prompt, max_tokens=300)
        except Exception as e:
            print(f"⚠️ Comment LLM generation skipped: {e}")
            result, tokens, model = self._fallback_comment(post_text, platform), 0, "local-template"

        if result:
            self.db.save_content(
                content_type="comment",
                platform=platform,
                target_author=author,
                input_context=post_text[:300],
                generated_text=result.get("comment", ""),
                tokens=tokens,
                model=model
            )

        return result

    def generate_dm(self, profile_name: str, profile_bio: str,
                    platform: str, context: str = "") -> dict:
        """Generate a personalized DM"""
        prompt = f"""You are {AGENT_IDENTITY['name']}.

Write a personalized DM to connect with:
Name: {profile_name}
Bio: {profile_bio}
Context: {context}

Rules:
- 2-3 sentences max
- Reference something specific about their work
- Clear reason for reaching out
- No ask in first message — just genuine connection
- Not salesy

Return JSON:
{{
  "dm_text": "the message",
  "connection_angle": "why you're reaching out specifically"
}}"""

        result, tokens, model = self.llm.complete_json("dm_generation", prompt, max_tokens=300)

        if result:
            self.db.save_content(
                content_type="dm",
                platform=platform,
                target_author=profile_name,
                input_context=profile_bio[:300],
                generated_text=result.get("dm_text", ""),
                tokens=tokens,
                model=model
            )

        return result
