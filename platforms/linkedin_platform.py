"""
platforms/linkedin_platform.py — LinkedIn Execution Layer
"""

import asyncio
import random
import requests
from playwright.async_api import Page
from playwright_stealth import stealth
from platforms.base_platform import BasePlatform
from memory.database import Database
from config import (LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN, 
                    LINKEDIN_EMAIL, LINKEDIN_PASSWORD, DAILY_LIMITS)

class LinkedInPlatform(BasePlatform):
    PLATFORM_NAME = "LinkedIn"

    def __init__(self, page: Page, db: Database, dry_run: bool = True):
        super().__init__(page, db, dry_run)
        self.counts = {k: 0 for k in DAILY_LIMITS["linkedin"]}

    async def login(self):
        if not self.page:
            return
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            print("⚠️ LINKEDIN_EMAIL/PASSWORD not set, skipping browser login")
            return
        
        print("🔐 Logging into LinkedIn (browser with stealth)...")
        try:
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
        except Exception as e:
            print(f"⚠️ LinkedIn browser login failed: {e}")

    async def post_content(self, text: str, **kwargs) -> bool:
        if self.dry_run:
            print(f"DRY RUN: would post to LinkedIn: {text[:60]}...")
            return True

        if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
            print("⚠️ LinkedIn API credentials missing")
            return False

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
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }

        try:
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            if response.status_code in [200, 201]:
                return True
            print(f"❌ LinkedIn API failed: {response.status_code} {response.text}")
        except Exception as e:
            print(f"❌ LinkedIn API error: {e}")
        return False

    async def like(self, el) -> bool:
        if self.dry_run or not self.page or self.page.is_closed():
            return False
        try:
            await el.scroll_into_view_if_needed()
            btn = await el.query_selector('[aria-label*="Like"]')
            if btn:
                await asyncio.sleep(self._random_delay(0.5, 1.5))
                await btn.click()
                await asyncio.sleep(self._random_delay(1, 3))
                return True
        except:
            pass
        return False

    async def comment(self, el, text: str) -> bool:
        if self.dry_run or not self.page or self.page.is_closed():
            return False
        try:
            await el.scroll_into_view_if_needed()
            btn = await el.query_selector('[aria-label*="Comment"]')
            if btn:
                await btn.click()
                await asyncio.sleep(self._random_delay(1.5, 3))
                editor = await self.page.query_selector('.ql-editor')
                if editor:
                    await editor.fill(text)
                    await asyncio.sleep(self._random_delay(1, 2))
                    submit = await self.page.query_selector('button.comments-comment-box__submit-button')
                    if submit:
                        await submit.click()
                        await asyncio.sleep(self._random_delay(2, 4))
                        return True
        except:
            pass
        return False

    async def scrape_feed(self, topic: str = None) -> list:
        if not self.page or self.page.is_closed():
            return []
            
        posts = []
        try:
            await self.page.goto("https://www.linkedin.com/feed/")
            await asyncio.sleep(random.uniform(3, 5))
            
            for i in range(4):
                els = await self.page.query_selector_all('.feed-shared-update-v2')
                for el in els:
                    try:
                        text_el = await el.query_selector('.feed-shared-text')
                        auth_el = await el.query_selector('.update-components-actor__name')
                        if text_el and auth_el:
                            text = await text_el.inner_text()
                            author = await auth_el.inner_text()
                            if not any(p['text'] == text for p in posts):
                                posts.append({
                                    "text": text,
                                    "author": author,
                                    "element": el,
                                    "topic": "feed"
                                })
                    except:
                        pass
                
                await self.page.evaluate(f"window.scrollBy(0, {random.randint(600, 900)})")
                await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"⚠️ LinkedIn feed scrape error: {e}")
            
        return posts[:10]
