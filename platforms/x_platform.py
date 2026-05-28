"""
platforms/x_platform.py — X.com (Twitter) Execution Layer
"""

import asyncio
import random
import tweepy
import requests
from playwright.async_api import Page
from playwright_stealth import Stealth
from platforms.base_platform import BasePlatform
from memory.database import Database
from config import (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET,
                    X_API_BEARER_TOKEN, X_API_BASE_URL, X_USERNAME, X_PASSWORD,
                    DAILY_LIMITS)

class XPlatform(BasePlatform):
    PLATFORM_NAME = "X.com"

    def __init__(self, page: Page, db: Database, dry_run: bool = True):
        super().__init__(page, db, dry_run)
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
        if not self.page:
            return
        if not X_USERNAME or not X_PASSWORD:
            print("⚠️ X_USERNAME/PASSWORD not set, skipping browser login")
            return
        
        print("🔐 Logging into X.com (browser with stealth)...")
        try:
            await Stealth().apply_stealth_async(self.page)
            await self.page.goto("https://x.com/login")
            await asyncio.sleep(random.uniform(3, 5))
            
            username_selector = 'input[autocomplete*="username"], input[name="text"], input[name="username_or_email"]'
            if await self.page.query_selector(username_selector):
                await self.page.fill(username_selector, X_USERNAME)
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(random.uniform(2, 4))
            
            password_selector = 'input[name="password"], input[type="password"]'
            if await self.page.query_selector(password_selector):
                await self.page.fill(password_selector, X_PASSWORD)
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(random.uniform(4, 6))
            
            print("✅ X.com browser ready")
        except Exception as e:
            print(f"⚠️ X.com browser login failed: {e}")

    async def post_content(self, text: str, **kwargs) -> bool:
        if self.dry_run:
            print(f"DRY RUN: would post to X: {text[:60]}...")
            return True

        if self.client:
            try:
                self.client.create_tweet(text=text)
                return True
            except Exception as e:
                print(f"⚠️ X API post failed: {e}")

        # Fallback to direct HTTP if Bearer Token available
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

        # Last resort: Browser
        if self.page and not self.page.is_closed():
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

    async def like(self, post_data) -> bool:
        if self.dry_run:
            return False
        
        if self.client and "id" in post_data:
            try:
                self.client.like(post_data["id"])
                return True
            except Exception as e:
                print(f"⚠️ X API like failed: {e}")
                return False

        if "element" in post_data and self.page and not self.page.is_closed():
            try:
                btn = await post_data["element"].query_selector('[data-testid="like"]')
                if btn:
                    await btn.click()
                    await asyncio.sleep(self._random_delay())
                    return True
            except:
                pass
        return False

    async def comment(self, post_data, text: str) -> bool:
        if self.dry_run:
            return False

        if self.client and "id" in post_data:
            try:
                self.client.create_tweet(text=text, in_reply_to_tweet_id=post_data["id"])
                return True
            except Exception as e:
                print(f"⚠️ X API comment failed: {e}")
                return False

        if "element" in post_data and self.page and not self.page.is_closed():
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

    async def scrape_feed(self, topic: str = None) -> list:
        posts = []
        # Try API Search first
        if self.client and topic:
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
            except tweepy.errors.Forbidden:
                print(f"ℹ️ X API Search restricted. Falling back to browser.")
                self.client = None # Cache failure
            except tweepy.errors.Unauthorized:
                print(f"ℹ️ X API Search unauthorized. Falling back to browser.")
                self.client = None
            except Exception as e:
                print(f"⚠️ X API search error: {e}")

        # Browser Fallback
        if self.page and not self.page.is_closed() and topic:
            try:
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
            except Exception as e:
                print(f"⚠️ X browser search error: {e}")
        return posts

    async def get_profile_metrics(self) -> dict:
        """Fetch live follower and following counts"""
        if self.client:
            try:
                me = self.client.get_me(user_auth=True, user_fields=['public_metrics'])
                if me.data:
                    metrics = me.data.public_metrics
                    return {
                        "followers": metrics.get('followers_count', 0),
                        "following": metrics.get('following_count', 0),
                        "posts": metrics.get('tweet_count', 0)
                    }
            except Exception as e:
                print(f"⚠️ X API profile fetch failed: {e}")
        
        return {"followers": 0, "following": 0, "posts": 0}
