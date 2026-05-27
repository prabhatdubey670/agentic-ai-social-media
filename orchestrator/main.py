"""
orchestrator/main.py — Production-grade AI Social Media Orchestrator
Modular Supervisor-Worker Architecture
"""

import asyncio
import random
import argparse
import sys
import os
from datetime import datetime, timedelta

# Adjust path to root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
from config import (DAILY_LIMITS, DELAYS, TARGET_TOPICS, 
                    BROWSER_HEADLESS, DRY_RUN_DEFAULT, REQUIRE_MANUAL_APPROVAL)

# Modular Imports
from memory.database import Database
from llm_router import LLMRouter
from core.utils import TelegramNotifier, get_kafka_router
from workers.content_creator import ContentCreator
from workers.network_scout import NetworkScout
from platforms.x_platform import XPlatform
from platforms.linkedin_platform import LinkedInPlatform

class Supervisor:
    def __init__(self, mode="draft", dry_run=True):
        self.mode = mode
        self.dry_run = dry_run
        self.db = Database()
        self.llm = LLMRouter()
        self.notifier = TelegramNotifier()
        self.kafka = get_kafka_router()
        self.creator = ContentCreator(self.llm, self.db)
        self.scout = NetworkScout(self.llm, self.db)
        
    async def run_broadcaster(self, platform_obj):
        """Workflow: Post new content with safety checks"""
        platform = platform_obj.PLATFORM_NAME
        print(f"\n📢 [Workflow: Broadcaster] Checking {platform}...")

        # 1. Kill Switch
        today_count = self.db.get_daily_post_count(platform)
        if today_count >= 10:
            print(f"🛑 KILL SWITCH: Already posted {today_count} times to {platform} today.")
            return

        # 2. Gap Check
        last_post = self.db.get_last_post_time(platform)
        if last_post:
            gap = 1 if platform == "X.com" else 2
            diff = datetime.now() - last_post
            if diff < timedelta(hours=gap):
                print(f"⏳ GAP CHECK: Last post was {int(diff.total_seconds()/60)} mins ago. Skipping post.")
                return

        # 3. Generate or Get from Queue
        # (Simplified for now: generate new)
        topic = random.choice(TARGET_TOPICS)
        if platform == "X.com":
            draft = self.creator.generate_x_post(topic=topic)
        else:
            draft = self.creator.generate_linkedin_post(topic=topic)

        if not draft or not draft.get("post_text"):
            return

        # 4. Execute
        text = draft["post_text"]
        print(f"📝 Drafting for {platform}: {text[:60]}...")
        
        success = await platform_obj.post_content(text)
        if success and not self.dry_run:
            self.db.save_published_post(
                platform, text, topic, draft.get("post_type", "post"), draft.get("model_used", "ai")
            )
            self.db.update_daily_stats(platform, "posts_published")
            print(f"✅ Successfully published to {platform}")

    async def run_networking(self, platform_obj):
        """Workflow: Engage with others"""
        platform = platform_obj.PLATFORM_NAME
        print(f"\n🤝 [Workflow: Networking] Engaging on {platform}...")
        
        for topic in random.sample(TARGET_TOPICS, 3):
            posts = await platform_obj.scrape_feed(topic=topic)
            for post in posts:
                # 1. Evaluate
                result = self.scout.evaluate_post(post["text"], post["author"], platform, topic)
                eval_data = result["evaluation"]
                
                if not eval_data.get("should_engage"):
                    continue
                
                action = eval_data.get("action", "skip")
                
                # 2. Like
                if action in ["like", "comment"]:
                    if await platform_obj.like(post):
                        self.db.update_daily_stats(platform, "likes")
                        self.db.save_action(result["post_id"], platform, "like", success=True)
                        print(f"❤️ Liked post by {post['author']}")

                # 3. Comment
                if action == "comment":
                    comment_draft = self.creator.generate_comment(post["text"], post["author"], platform)
                    if comment_draft.get("comment"):
                        if await platform_obj.comment(post, comment_draft["comment"]):
                            self.db.update_daily_stats(platform, "comments")
                            self.db.save_action(result["post_id"], platform, "comment", 
                                              content=comment_draft["comment"], success=True)
                            print(f"💬 Commented on {post['author']}'s post")

                await asyncio.sleep(random.uniform(DELAYS["min_between_actions"], DELAYS["max_between_actions"]))

    async def run(self):
        print(f"🚀 Supervisor starting in '{self.mode}' mode (Execute={not self.dry_run})")
        
        # Initialize Platforms
        if self.mode in ["post", "engage", "full"]:
            from config import BASE_DIR
            user_data_dir = os.path.join(BASE_DIR, "playwright_session")
            
            async with async_playwright() as p:
                browser_context = await p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=BROWSER_HEADLESS,
                    slow_mo=50
                )
                
                # Setup platform objects
                x_platform = XPlatform(browser_context.pages[0], self.db, self.dry_run)
                li_platform = LinkedInPlatform(await browser_context.new_page(), self.db, self.dry_run)

                # WORKFLOW: BROADCASTING
                if self.mode in ["post", "full"]:
                    await self.run_broadcaster(x_platform)
                    await self.run_broadcaster(li_platform)

                # WORKFLOW: NETWORKING
                if self.mode in ["engage", "full"]:
                    await x_platform.login()
                    await self.run_networking(x_platform)
                    
                    await li_platform.login()
                    await self.run_networking(li_platform)

                await browser_context.close()
        
        print("\n🏁 Session Complete.")

async def main():
    parser = argparse.ArgumentParser(description="Quanteve AI Social Media Manager v5 (Modular)")
    parser.add_argument("--mode", choices=["draft", "post", "engage", "full", "analyze"], default="draft")
    parser.add_argument("--execute", action="store_true", help="Disable dry-run and actually post")
    args = parser.parse_args()

    supervisor = Supervisor(mode=args.mode, dry_run=not args.execute)
    await supervisor.run()

if __name__ == "__main__":
    asyncio.run(main())
