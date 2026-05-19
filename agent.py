"""
agent.py — Quanteve Social Media Agent v5
Main orchestrator — runs full pipeline:
1. Generate new posts
2. Engage with others' posts
3. Save everything to DB + Kafka
4. Analyze performance
5. Self-improve strategy
6. Send Telegram notifications

Usage: python agent.py [--mode post|engage|analyze|full]
"""

import asyncio
import random
import argparse
import sys
from datetime import datetime
from playwright.async_api import async_playwright, Page
from playwright_stealth import stealth
import requests
import telegram
import tweepy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Quanteve modules
from config import (DAILY_LIMITS, DELAYS, TARGET_TOPICS, TELEGRAM_BOT_TOKEN,
                    TELEGRAM_CHAT_ID, X_USERNAME, X_PASSWORD,
                    X_API_BEARER_TOKEN, X_API_BASE_URL,
                    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET,
                    LINKEDIN_EMAIL, LINKEDIN_PASSWORD,
                    LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN,
                    KAFKA, DRY_RUN_DEFAULT, BROWSER_HEADLESS, REQUIRE_MANUAL_APPROVAL)
from llm_router import LLMRouter
from storage import Database
from content_generator import ContentGenerator
from analytics import Analytics
from self_improver import SelfImprover


# ============================================================
# KAFKA (optional)
# ============================================================
def get_kafka_router():
    if KAFKA["enabled"]:
        try:
            from kafka import KafkaProducer
            import json
            producer = KafkaProducer(
                bootstrap_servers=KAFKA["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Kafka connected")
            return producer
        except Exception as e:
            print(f"⚠️ Kafka unavailable: {e}")
    return None


# ============================================================
# TELEGRAM NOTIFIER
# ============================================================
class TelegramNotifier:
    def __init__(self):
        if (not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or
                TELEGRAM_BOT_TOKEN.startswith("your_") or
                TELEGRAM_CHAT_ID.startswith("your_")):
            self.bot = None
            self.enabled = False
            print("⚠️ Telegram not configured")
            return

        try:
            self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            self.enabled = True
        except:
            self.enabled = False
            print("⚠️ Telegram not configured")

    async def send(self, message: str):
        if not self.enabled:
            return
        try:
            await self.bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                                         text=message, parse_mode='Markdown')
        except Exception as e:
            print(f"Telegram error: {e}")

    async def action(self, action_type: str, platform: str, detail: str):
        emoji = {"like": "❤️", "comment": "💬", "follow": "➕",
                 "dm": "📩", "post": "📝", "error": "❌"}.get(action_type, "📌")
        await self.send(f"{emoji} *{action_type.upper()}* — {platform}\n{detail}")

    async def session_summary(self, stats: dict):
        msg = "📊 *Session Complete*\n"
        for k, v in stats.items():
            msg += f"• {k}: {v}\n"
        await self.send(msg)


# ============================================================
# POST EVALUATOR
# ============================================================
class PostEvaluator:
    def __init__(self, llm: LLMRouter, db: Database):
        self.llm = llm
        self.db = db

    def evaluate(self, post_text: str, author: str, platform: str,
                 topic: str = "") -> dict:
        from config import AGENT_IDENTITY
        prompt = f"""You are a social media engagement agent for {AGENT_IDENTITY['name']}.

Evaluate this {platform} post for engagement:
Author: {author}
Post: {post_text}

Return JSON only:
{{
  "should_engage": true/false,
  "action": "like" | "comment" | "follow" | "skip",
  "reason": "brief reason",
  "value_score": 1-10,
  "sentiment": "positive|neutral|negative",
  "engagement_potential": 1-10
}}

Engage with: ML, AI, data science, quant, trading, research, tech.
Skip: promotional, political, spam, unrelated."""

        try:
            result, tokens, model = self.llm.complete_json("post_evaluation", prompt, max_tokens=300)
        except Exception as e:
            print(f"⚠️ Post evaluation LLM skipped: {e}")
            lowered = post_text.lower()
            relevant = any(t.lower() in lowered for t in TARGET_TOPICS)
            result, model = {
                "should_engage": relevant,
                "action": "comment" if relevant else "skip",
                "reason": "Local keyword fallback evaluation.",
                "value_score": 6 if relevant else 1,
                "sentiment": "neutral",
                "engagement_potential": 5 if relevant else 1,
            }, "local-keyword"

        # Save post seen
        post_id = self.db.save_post_seen(
            platform=platform, author=author, author_handle=author,
            post_text=post_text, topic=topic,
            value_score=result.get("value_score", 0) if result else 0,
            sentiment=result.get("sentiment", "neutral") if result else "neutral",
            engagement_potential=result.get("engagement_potential", 0) if result else 0
        )

        return {"evaluation": result or {}, "post_id": post_id, "model": model}


# ============================================================
# X.COM AGENT
# ============================================================
class XAgent:
    PLATFORM = "X.com"

    def __init__(self, page: Page, llm: LLMRouter, db: Database,
                 content_gen: ContentGenerator, notifier: TelegramNotifier,
                 dry_run: bool = True):
        self.page = page
        self.evaluator = PostEvaluator(llm, db)
        self.content_gen = content_gen
        self.db = db
        self.notifier = notifier
        self.dry_run = dry_run
        self.counts = {k: 0 for k in DAILY_LIMITS["x"]}
        self.client = None

        if all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
            try:
                self.client = tweepy.Client(
                    bearer_token=X_API_BEARER_TOKEN if X_API_BEARER_TOKEN else None,
                    consumer_key=X_API_KEY,
                    consumer_secret=X_API_SECRET,
                    access_token=X_ACCESS_TOKEN,
                    access_token_secret=X_ACCESS_TOKEN_SECRET,
                    wait_on_rate_limit=True
                )
                print("✅ X.com API (tweepy) initialized")
            except Exception as e:
                print(f"⚠️ X.com API failed to initialize: {e}")

    async def login(self):
        """No-op for API-based agent, but keeps browser login if page is provided."""
        if self.page:
            if not X_USERNAME or not X_PASSWORD:
                print("⚠️ X_USERNAME/PASSWORD not set, skipping browser login")
                return
            print("🔐 Logging into X.com (browser with stealth)...")
            try:
                await stealth(self.page)
                await self.page.goto("https://x.com/login")
                await asyncio.sleep(random.uniform(3, 5))
                
                # Username
                if await self.page.query_selector('input[autocomplete="username"]'):
                    await self.page.fill('input[autocomplete="username"]', X_USERNAME)
                    await self.page.keyboard.press('Enter')
                    await asyncio.sleep(random.uniform(2, 4))
                
                # Sometimes X asks for phone/email verification if login is from new place
                # We can't automate that easily here, but we try the password
                if await self.page.query_selector('input[name="password"]'):
                    await self.page.fill('input[name="password"]', X_PASSWORD)
                    await self.page.keyboard.press('Enter')
                    await asyncio.sleep(random.uniform(4, 6))
                
                print("✅ X.com browser ready")
            except Exception as e:
                print(f"⚠️ X.com browser login failed: {e}")

    async def search_topic(self, topic: str) -> list:
        posts = []
        if self.client:
            print(f"🔍 Searching X via API for: {topic}")
            try:
                query = f"{topic} -is:retweet lang:en"
                tweets = self.client.search_recent_tweets(
                    query=query, max_results=15, 
                    tweet_fields=['text', 'author_id', 'id']
                )
                if tweets.data:
                    for tweet in tweets.data:
                        posts.append({
                            "text": tweet.text,
                            "author": str(tweet.author_id),
                            "id": tweet.id,
                            "topic": topic
                        })
                return posts
            except tweepy.errors.Forbidden as e:
                print(f"ℹ️ X API Search is restricted (likely Free tier). Falling back to browser.")
                self.client = None
            except tweepy.errors.Unauthorized as e:
                print(f"ℹ️ X API Search unauthorized. Falling back to browser.")
                self.client = None
            except Exception as e:
                print(f"⚠️ X API search failed: {e}")

        if self.page:
            print(f"🔍 Searching X via browser for: {topic}")
            url = f"https://x.com/search?q={topic.replace(' ', '%20')}&f=live"
            await self.page.goto(url)
            await asyncio.sleep(3)
            articles = await self.page.query_selector_all('article[data-testid="tweet"]')
            for article in articles[:15]:
                try:
                    text_el = await article.query_selector('[data-testid="tweetText"]')
                    author_el = await article.query_selector('[data-testid="User-Name"]')
                    if text_el and author_el:
                        posts.append({
                            "text": await text_el.inner_text(),
                            "author": await author_el.inner_text(),
                            "element": article,
                            "topic": topic
                        })
                except:
                    pass
        return posts

    async def like(self, post_data) -> bool:
        if self.dry_run:
            print("DRY RUN: would like X post")
            return False
        
        if self.client and "id" in post_data:
            try:
                self.client.like(post_data["id"])
                return True
            except Exception as e:
                print(f"⚠️ X API like failed: {e}")
                return False

        if "element" in post_data:
            try:
                btn = await post_data["element"].query_selector('[data-testid="like"]')
                if btn:
                    await btn.click()
                    await asyncio.sleep(random.uniform(1, 3))
                    return True
            except:
                pass
        return False

    async def comment(self, post_data, text: str) -> bool:
        if self.dry_run:
            print(f"DRY RUN: would comment on X: {text[:100]}")
            return False

        if self.client and "id" in post_data:
            try:
                self.client.create_tweet(text=text, in_reply_to_tweet_id=post_data["id"])
                return True
            except Exception as e:
                print(f"⚠️ X API comment failed: {e}")
                return False

        if "element" in post_data:
            try:
                btn = await post_data["element"].query_selector('[data-testid="reply"]')
                if btn:
                    await btn.click()
                    await asyncio.sleep(2)
                    editor = await self.page.query_selector('[data-testid="tweetTextarea_0"]')
                    if editor:
                        await editor.fill(text)
                        await asyncio.sleep(1)
                        submit = await self.page.query_selector('[data-testid="tweetButtonInline"]')
                        if submit:
                            await submit.click()
                            await asyncio.sleep(2)
                            return True
            except:
                pass
        return False

    async def post_tweet(self, text: str) -> bool:
        if self.dry_run:
            print(f"DRY RUN: would post to X: {text[:180]}")
            return False

        if self.client:
            try:
                self.client.create_tweet(text=text)
                print("✅ Posted to X via API (tweepy)")
                return True
            except Exception as e:
                print(f"⚠️ X API post failed: {e}")

        if X_API_BEARER_TOKEN:
            response = requests.post(
                f"{X_API_BASE_URL.rstrip('/')}/2/tweets",
                headers={
                    "Authorization": f"Bearer {X_API_BEARER_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=60,
            )
            if response.status_code == 201:
                return True

        if self.page:
            try:
                await self.page.goto("https://x.com/home")
                await asyncio.sleep(2)
                composer = await self.page.query_selector('[data-testid="tweetTextarea_0"]')
                if composer:
                    await composer.fill(text)
                    await asyncio.sleep(1)
                    submit = await self.page.query_selector('[data-testid="tweetButtonInline"]')
                    if submit:
                        await submit.click()
                        await asyncio.sleep(3)
                        return True
            except:
                pass
        return False

    async def run_engagement(self):
        """Engage with others' posts"""
        for topic in TARGET_TOPICS:
            if self.page and self.page.is_closed():
                print("⚠️ Browser page closed unexpectedly. Stopping X engagement.")
                break

            if self.counts["likes"] >= DAILY_LIMITS["x"]["likes"]:
                break

            posts = await self.search_topic(topic)
            for post in posts:
                await asyncio.sleep(random.uniform(DELAYS["min_between_actions"],
                                                    DELAYS["max_between_actions"]))

                result = self.evaluator.evaluate(post["text"], post["author"],
                                                  self.PLATFORM, topic)
                eval_data = result["evaluation"]
                post_id = result["post_id"]

                if not eval_data.get("should_engage"):
                    self.db.update_daily_stats(self.PLATFORM, "posts_skipped")
                    continue

                self.db.update_daily_stats(self.PLATFORM, "posts_evaluated")
                action = eval_data.get("action", "skip")

                # Like
                if action in ["like", "comment"] and self.counts["likes"] < DAILY_LIMITS["x"]["likes"]:
                    success = await self.like(post)
                    self.db.save_action(post_id, self.PLATFORM, "like",
                                       reasoning=eval_data.get("reason", ""),
                                       model_used=result["model"], success=success)
                    if success:
                        self.counts["likes"] += 1
                        self.db.update_daily_stats(self.PLATFORM, "likes")
                        await self.notifier.action("like", self.PLATFORM,
                                                    f"@{post['author']}: {post['text'][:60]}...")

                # Comment
                if action == "comment" and self.counts["comments"] < DAILY_LIMITS["x"]["comments"]:
                    comment_result = self.content_gen.generate_comment(
                        post["text"], post["author"], self.PLATFORM)
                    comment_text = comment_result.get("comment", "") if comment_result else ""

                    if comment_text:
                        success = await self.comment(post, comment_text)
                        self.db.save_action(post_id, self.PLATFORM, "comment",
                                           content=comment_text,
                                           reasoning=eval_data.get("reason", ""),
                                           model_used=result["model"], success=success)
                        if success:
                            self.counts["comments"] += 1
                            self.db.update_daily_stats(self.PLATFORM, "comments")
                            await self.notifier.action("comment", self.PLATFORM,
                                                        f"@{post['author']}: {comment_text}")

    async def run_posting(self):
        """Generate and post original content"""
        # 1. Daily Kill switch: Check DB for today's total posts
        today_count = self.db.get_daily_post_count(self.PLATFORM)
        max_daily = 10 
        
        if today_count >= max_daily:
            print(f"🛑 KILL SWITCH: Already posted {today_count} times to X today. Stopping.")
            return

        # 2. 2-Hour Gap Check for X.com
        last_post = self.db.get_last_post_time(self.PLATFORM)
        if last_post:
            from datetime import timedelta
            diff = datetime.now() - last_post
            if diff < timedelta(hours=2):
                wait_mins = int((timedelta(hours=2) - diff).total_seconds() / 60)
                print(f"⏳ GAP CHECK: Last post on X was {int(diff.total_seconds() / 60)} mins ago.")
                print(f"   Skipping X post for now (min 2h gap required). Proceeding to engagement.")
                return

        posts_to_make = min(DAILY_LIMITS["x"]["posts"], max_daily - today_count)
        
        if posts_to_make <= 0:
            return

        if not self.dry_run:
            approved = [
                row for row in self.db.get_queued_content(status="approved", limit=posts_to_make)
                if row[1] == self.PLATFORM and row[2] == "x_post"
            ]
            if approved:
                for row in approved:
                    item_id, platform, content_type, topic, post_text, *_ = row
                    success = await self.post_tweet(post_text)
                    if success:
                        self.counts["posts"] += 1
                        self.db.mark_content_posted(item_id)
                        self.db.update_daily_stats(self.PLATFORM, "posts_published")
                        self.db.save_published_post(self.PLATFORM, post_text, topic,
                                                    content_type, "queue-approved")
                        await self.notifier.action("post", self.PLATFORM,
                                                   f"Posted approved draft: {post_text[:80]}...")
                return

            if REQUIRE_MANUAL_APPROVAL:
                print("No approved X.com drafts found. Run --mode queue --approve QUEUE_ID first.")
                return

        for i in range(posts_to_make):
            if self.counts["posts"] >= posts_to_make:
                break

            topic = random.choice(TARGET_TOPICS)
            post_data = self.content_gen.generate_x_post(topic=topic)

            if post_data and post_data.get("post_text"):
                post_text = post_data["post_text"]
                queue_id = self.db.queue_content(
                    self.PLATFORM, "x_post", topic, post_text,
                    source_model=post_data.get("model_used", ""),
                    notes=post_data.get("reasoning", ""))
                print(f"Queued X draft {queue_id}: {post_text[:100]}...")

                if self.dry_run:
                    self.counts["posts"] += 1
                    continue

                success = await self.post_tweet(post_text)

                if success:
                    self.counts["posts"] += 1
                    self.db.update_daily_stats(self.PLATFORM, "posts_published")
                    self.db.save_published_post(
                        self.PLATFORM, post_text, topic,
                        post_data.get("post_type", ""), post_data.get("model_used", ""))
                    await self.notifier.action("post", self.PLATFORM,
                                               f"Posted: {post_text[:80]}...")
                    print(f"📝 Posted to X: {post_text[:60]}...")
                else:
                    # Even on failure, wait a bit to avoid hitting X too hard
                    await asyncio.sleep(30)
                
                # Only sleep if there are more posts to make
                if self.counts["posts"] < posts_to_make:
                    await asyncio.sleep(random.uniform(DELAYS["min_between_posts"],
                                                        DELAYS["max_between_posts"]))


# ============================================================
# LINKEDIN AGENT
# ============================================================
class LinkedInAgent:
    PLATFORM = "LinkedIn"

    def __init__(self, page: Page, llm: LLMRouter, db: Database,
                 content_gen: ContentGenerator, notifier: TelegramNotifier,
                 dry_run: bool = True):
        self.page = page
        self.evaluator = PostEvaluator(llm, db)
        self.content_gen = content_gen
        self.db = db
        self.notifier = notifier
        self.dry_run = dry_run
        self.counts = {k: 0 for k in DAILY_LIMITS["linkedin"]}

    async def login(self):
        if not self.page:
            return
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            print("⚠️ LINKEDIN_EMAIL/PASSWORD not set, skipping browser login")
            return
        
        print("🔐 Logging into LinkedIn (browser with stealth)...")
        await stealth(self.page)
        await self.page.goto("https://www.linkedin.com/login")
        await asyncio.sleep(random.uniform(2, 4))
        
        await self.page.fill('#username', LINKEDIN_EMAIL)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await self.page.fill('#password', LINKEDIN_PASSWORD)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.page.click('[type="submit"]')
        await asyncio.sleep(random.uniform(5, 8))
        print("✅ LinkedIn browser ready")

    async def post_content(self, text: str) -> bool:
        """Post to LinkedIn via official API"""
        if self.dry_run:
            print(f"DRY RUN: would post to LinkedIn: {text[:100]}")
            return False

        if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
            print("⚠️ LinkedIn API credentials missing (LINKEDIN_ACCESS_TOKEN / LINKEDIN_AUTHOR_URN)")
            return False

        print("📝 Posting to LinkedIn via API...")
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        post_data = {
            "author": LINKEDIN_AUTHOR_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            if response.status_code in [200, 201]:
                print("✅ Successfully posted to LinkedIn via API")
                return True
            else:
                print(f"❌ LinkedIn API post failed: {response.status_code} {response.text}")
        except Exception as e:
            print(f"❌ LinkedIn API error: {e}")
        
        return False

    async def scrape_feed(self) -> list:
        if not self.page:
            return []
            
        posts = []
        await self.page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(random.uniform(3, 5))
        
        # Human-like scrolling
        for i in range(4):
            els = await self.page.query_selector_all('.feed-shared-update-v2')
            for el in els:
                try:
                    text_el = await el.query_selector('.feed-shared-text')
                    auth_el = await el.query_selector('.update-components-actor__name')
                    if text_el and auth_el:
                        text = await text_el.inner_text()
                        author = await auth_el.inner_text()
                        
                        # Avoid duplicates in same session
                        if not any(p['text'] == text for p in posts):
                            posts.append({
                                "text": text,
                                "author": author,
                                "element": el,
                                "topic": "feed"
                            })
                except:
                    pass
            
            # Scroll naturally
            scroll_amount = random.randint(600, 900)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(2, 4))
            
        return posts[:10]

    async def like(self, el) -> bool:
        if self.dry_run:
            print("DRY RUN: would like LinkedIn post")
            return False
        try:
            btn = await el.query_selector('[aria-label*="Like"]')
            if btn:
                # Scroll element into view first
                await el.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await btn.click()
                await asyncio.sleep(random.uniform(1, 3))
                return True
        except:
            pass
        return False

    async def comment(self, el, text: str) -> bool:
        if self.dry_run:
            print(f"DRY RUN: would comment on LinkedIn: {text[:100]}")
            return False
        try:
            btn = await el.query_selector('[aria-label*="Comment"]')
            if btn:
                await el.scroll_into_view_if_needed()
                await btn.click()
                await asyncio.sleep(random.uniform(1.5, 3))
                editor = await self.page.query_selector('.ql-editor')
                if editor:
                    await editor.fill(text)
                    await asyncio.sleep(random.uniform(1, 2))
                    submit = await self.page.query_selector('button.comments-comment-box__submit-button')
                    if submit:
                        await submit.click()
                        await asyncio.sleep(random.uniform(2, 4))
                        return True
        except:
            pass
        return False

    async def run_engagement(self):
        if not self.page:
            print("⚠️ LinkedIn engagement requires browser (page=None)")
            return

        posts = await self.scrape_feed()
        for post in posts:
            if self.page.is_closed():
                print("⚠️ Browser page closed. Stopping LinkedIn engagement.")
                break

            if self.counts["likes"] >= DAILY_LIMITS["linkedin"]["likes"] and \
               self.counts["comments"] >= DAILY_LIMITS["linkedin"]["comments"]:
                break

            await asyncio.sleep(random.uniform(DELAYS["min_between_actions"],
                                                DELAYS["max_between_actions"]))

            result = self.evaluator.evaluate(post["text"], post["author"], self.PLATFORM)
            eval_data = result["evaluation"]
            post_id = result["post_id"]

            if not eval_data.get("should_engage"):
                continue

            action = eval_data.get("action", "skip")

            if action in ["like", "comment"] and self.counts["likes"] < DAILY_LIMITS["linkedin"]["likes"]:
                success = await self.like(post["element"])
                self.db.save_action(post_id, self.PLATFORM, "like",
                                   model_used=result["model"], success=success)
                if success:
                    self.counts["likes"] += 1
                    self.db.update_daily_stats(self.PLATFORM, "likes")
                    await self.notifier.action("like", self.PLATFORM,
                                               f"{post['author']}: {post['text'][:60]}...")

            if action == "comment" and self.counts["comments"] < DAILY_LIMITS["linkedin"]["comments"]:
                comment_result = self.content_gen.generate_comment(
                    post["text"], post["author"], self.PLATFORM)
                comment_text = comment_result.get("comment", "") if comment_result else ""
                if comment_text:
                    success = await self.comment(post["element"], comment_text)
                    self.db.save_action(post_id, self.PLATFORM, "comment",
                                       content=comment_text, model_used=result["model"], success=success)
                    if success:
                        self.counts["comments"] += 1
                        self.db.update_daily_stats(self.PLATFORM, "comments")
                        await self.notifier.action("comment", self.PLATFORM,
                                                    f"{post['author']}: {comment_text}")

    async def run_posting(self):
        """Generate and post original content via API"""
        # 1. Daily Kill switch
        today_count = self.db.get_daily_post_count(self.PLATFORM)
        max_daily = 10 
        
        if today_count >= max_daily:
            print(f"🛑 KILL SWITCH: Already posted {today_count} times to LinkedIn today. Stopping.")
            return

        # 2. 2-Hour Gap Check
        last_post = self.db.get_last_post_time(self.PLATFORM)
        if last_post:
            from datetime import timedelta
            diff = datetime.now() - last_post
            if diff < timedelta(hours=2):
                wait_mins = int((timedelta(hours=2) - diff).total_seconds() / 60)
                print(f"⏳ GAP CHECK: Last post on LinkedIn was {int(diff.total_seconds() / 60)} mins ago.")
                print(f"   Skipping LinkedIn post for now (min 2h gap required). Proceeding to engagement.")
                return

        posts_to_make = min(DAILY_LIMITS["linkedin"]["posts"], max_daily - today_count)

        if not self.dry_run:
            approved = [
                row for row in self.db.get_queued_content(status="approved", limit=posts_to_make)
                if row[1] == self.PLATFORM and row[2] == "linkedin_post"
            ]
            if approved:
                for row in approved:
                    item_id, platform, content_type, topic, post_text, *_ = row
                    success = await self.post_content(post_text)
                    if success:
                        self.counts["posts"] += 1
                        self.db.mark_content_posted(item_id)
                        self.db.update_daily_stats(self.PLATFORM, "posts_published")
                        self.db.save_published_post(self.PLATFORM, post_text, topic,
                                                    content_type, "queue-approved")
                        await self.notifier.action("post", self.PLATFORM,
                                                   f"Posted approved draft: {post_text[:80]}...")
                return

        for i in range(posts_to_make):
            if self.counts["posts"] >= posts_to_make:
                break

            topic = random.choice(TARGET_TOPICS)
            post_data = self.content_gen.generate_linkedin_post(topic=topic)

            if post_data and post_data.get("post_text"):
                post_text = post_data["post_text"]
                queue_id = self.db.queue_content(
                    self.PLATFORM, "linkedin_post", topic, post_text,
                    source_model=post_data.get("model_used", ""),
                    notes=post_data.get("reasoning", ""))
                print(f"Queued LinkedIn draft {queue_id}: {post_text[:100]}...")

                if self.dry_run:
                    self.counts["posts"] += 1
                    continue

                if not REQUIRE_MANUAL_APPROVAL:
                    success = await self.post_content(post_text)
                    if success:
                        self.counts["posts"] += 1
                        self.db.update_daily_stats(self.PLATFORM, "posts_published")
                        self.db.save_published_post(
                            self.PLATFORM, post_text, topic,
                            "linkedin_post", post_data.get("model_used", ""))
                        await self.notifier.action("post", self.PLATFORM,
                                                   f"Posted: {post_text[:80]}...")
                        
                        # Only sleep if there are more posts to make
                        if self.counts["posts"] < posts_to_make:
                            await asyncio.sleep(random.uniform(DELAYS["min_between_posts"],
                                                                DELAYS["max_between_posts"]))


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================
async def legacy_main(mode: str = "full"):
    print(f"\n🚀 Quanteve Agent v5 — Mode: {mode}")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Init shared services
    db = Database()
    llm = LLMRouter()
    content_gen = ContentGenerator(llm, db)
    analytics = Analytics(db, llm)
    improver = SelfImprover(llm, db)
    notifier = TelegramNotifier()
    kafka = get_kafka_router()

    await notifier.send(f"🤖 *Quanteve Agent v5 Starting*\nMode: {mode}\n{datetime.now().strftime('%H:%M')}")

    if mode in ["analyze", "full"]:
        analytics.print_dashboard()

    # X.com Agent (Always initialized, uses API by default)
    x_agent = XAgent(None, llm, db, content_gen, notifier)
    
    if mode in ["post", "full"]:
        print("\n📝 Generating X.com posts (API)...")
        await x_agent.run_posting()

    # LinkedIn Agent (Initialized without page for posting)
    li_agent = LinkedInAgent(None, llm, db, content_gen, notifier)
    if mode in ["post", "full"]:
        print("\n📝 Generating LinkedIn posts (API)...")
        await li_agent.run_posting()

    # Browser-based engagement if needed
    if mode in ["engage", "full"]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=BROWSER_HEADLESS)
            
            # X engagement: always use browser for search if possible to avoid 401
            x_page = await browser.new_page()
            x_agent.page = x_page
            await x_agent.login()
            
            print("\n🤝 Engaging on X.com...")
            await x_agent.run_engagement()

            # LinkedIn engagement ALWAYS needs a browser
            li_page = await browser.new_page()
            li_agent.page = li_page
            await li_agent.login()
            print("\n🤝 Engaging on LinkedIn...")
            await li_agent.run_engagement()

            await browser.close()

    # Self-improvement
    if mode in ["analyze", "full"]:
        print("\n🧠 Running self-improvement cycle...")
        strategy = improver.analyze_and_improve()
        if strategy.get("strategy"):
            s = strategy["strategy"]
            summary = s.get("summary", "")
            actions = s.get("daily_actions", [])
            msg = f"🧠 *Strategy Update*\n{summary}\n\n*Next actions:*\n" + "\n".join(f"• {a}" for a in actions[:3])
            await notifier.send(msg)

    # Final summary
    summary = analytics.get_summary_stats()
    await notifier.session_summary(summary)
    analytics.print_dashboard()

    if kafka:
        kafka.close()

    print("\n✅ Session complete!")


def build_drafts(db: Database, content_gen: ContentGenerator, x_count: int = 2,
                 linkedin_count: int = 1):
    print("\nBuilding content drafts")
    for _ in range(x_count):
        topic = random.choice(TARGET_TOPICS)
        draft = content_gen.generate_x_post(topic=topic)
        if draft and draft.get("post_text"):
            qid = db.queue_content(
                "X.com", "x_post", topic, draft["post_text"],
                source_model=draft.get("model_used", ""),
                notes=draft.get("reasoning", ""))
            print(f"\n[{qid}] X.com / {topic}\n{draft['post_text']}")

    for _ in range(linkedin_count):
        topic = random.choice(TARGET_TOPICS)
        draft = content_gen.generate_linkedin_post(topic=topic)
        if draft and draft.get("post_text"):
            qid = db.queue_content(
                "LinkedIn", "linkedin_post", topic, draft["post_text"],
                source_model=draft.get("model_used", ""),
                notes=draft.get("reasoning", ""))
            print(f"\n[{qid}] LinkedIn / {topic}\n{draft['post_text']}")


def print_queue(db: Database, status: str = "draft", limit: int = 20):
    rows = db.get_queued_content(status=status, limit=limit)
    print(f"\nContent queue ({status})")
    if not rows:
        print("  No queued content")
        return

    for row in rows:
        item_id, platform, content_type, topic, text, item_status, scheduled, model, created = row
        print(f"\n[{item_id}] {platform} | {content_type} | {topic} | {item_status} | {created}")
        print(text[:600])


async def main(mode: str = "draft", dry_run: bool = True, approve_id: str = "",
               queue_status: str = "draft"):
    print(f"\nQuanteve Agent v5 - Mode: {mode}")
    print(f"   Automation: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    db = Database()
    llm = LLMRouter()
    content_gen = ContentGenerator(llm, db)
    analytics = Analytics(db, llm)
    improver = SelfImprover(llm, db)
    notifier = TelegramNotifier()
    kafka = get_kafka_router()

    await notifier.send(
        f"*Quanteve Agent v5 Starting*\nMode: {mode}\n{datetime.now().strftime('%H:%M')}"
    )

    if mode == "draft":
        build_drafts(db, content_gen)
        print_queue(db)
        return

    if approve_id:
        db.approve_content(approve_id)
        print(f"Approved queued content: {approve_id}")

    if mode == "queue":
        print_queue(db, status=queue_status)
        return

    if mode in ["analyze", "full"]:
        analytics.print_dashboard()

    # Posting logic (API-first)
    x_agent = XAgent(None, llm, db, content_gen, notifier, dry_run=dry_run)
    li_agent = LinkedInAgent(None, llm, db, content_gen, notifier, dry_run=dry_run)

    if mode in ["post", "full"]:
        if dry_run:
            build_drafts(db, content_gen, x_count=DAILY_LIMITS["x"]["posts"], 
                         linkedin_count=DAILY_LIMITS["linkedin"]["posts"])
        else:
            print("\nPosting to X.com (API)...")
            await x_agent.run_posting()
            print("\nPosting to LinkedIn (API)...")
            await li_agent.run_posting()

    # Engagement logic (Browser-based)
    if mode in ["engage", "full"]:
        import os
        user_data_dir = os.path.join(os.getcwd(), "playwright_session")
        
        async with async_playwright() as p:
            # Use persistent context to store login session/cache
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=BROWSER_HEADLESS,
                slow_mo=50
            )

            # X Engagement: Use browser for search (API free tier 401)
            x_page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
            x_agent.page = x_page
            
            # Only login if not already logged in (check for search input)
            await x_page.goto("https://x.com/home")
            await asyncio.sleep(3)
            if not await x_page.query_selector('[data-testid="SideNav_AccountMenu_Button"]'):
                await x_agent.login()
            
            print("\nEngaging on X.com...")
            await x_agent.run_engagement()

            # LinkedIn Engagement
            li_page = await browser_context.new_page()
            li_agent.page = li_page
            
            await li_page.goto("https://www.linkedin.com/feed/")
            await asyncio.sleep(3)
            if "login" in li_page.url or await li_page.query_selector('#username'):
                await li_agent.login()
                
            print("\nEngaging on LinkedIn...")
            await li_agent.run_engagement()

            await browser_context.close()

    if mode in ["analyze", "full"]:
        print("\nRunning self-improvement cycle...")
        strategy = improver.analyze_and_improve()
        if strategy.get("strategy"):
            s = strategy["strategy"]
            summary = s.get("summary", "")
            actions = s.get("daily_actions", [])
            msg = f"*Strategy Update*\n{summary}\n\n*Next actions:*\n" + "\n".join(
                f"- {a}" for a in actions[:3])
            await notifier.send(msg)

    summary = analytics.get_summary_stats()
    await notifier.session_summary(summary)
    analytics.print_dashboard()

    if kafka:
        kafka.close()

    print("\nSession complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="draft",
                       choices=["draft", "queue", "post", "engage", "analyze", "full"],
                       help="draft=generate queue, queue=list drafts, post/engage/full=browser modes")
    parser.add_argument("--execute", action="store_true",
                        help="Actually click/post in the browser. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run even when DRY_RUN_DEFAULT=false.")
    parser.add_argument("--approve", default="",
                        help="Mark a queued content item approved by ID.")
    parser.add_argument("--status", default="draft",
                        choices=["draft", "approved", "posted"],
                        help="Queue status to list.")
    args = parser.parse_args()
    effective_dry_run = True if args.dry_run else (not args.execute and DRY_RUN_DEFAULT)
    asyncio.run(main(args.mode, dry_run=effective_dry_run,
                     approve_id=args.approve, queue_status=args.status))
