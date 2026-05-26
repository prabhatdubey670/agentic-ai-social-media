"""
platforms/base_platform.py — Common Interface for Execution Layer
"""

import asyncio
import random
from playwright.async_api import Page
from memory.database import Database

class BasePlatform:
    PLATFORM_NAME = "Base"

    def __init__(self, page: Page, db: Database, dry_run: bool = True):
        self.page = page
        self.db = db
        self.dry_run = dry_run
        self.counts = {}

    async def login(self):
        """Perform platform login"""
        raise NotImplementedError

    async def post_content(self, text: str, **kwargs) -> bool:
        """Publish original content"""
        raise NotImplementedError

    async def like(self, post_data) -> bool:
        """Like a post"""
        raise NotImplementedError

    async def comment(self, post_data, text: str) -> bool:
        """Comment on a post"""
        raise NotImplementedError

    async def scrape_feed(self, topic: str = None) -> list:
        """Find posts to engage with"""
        raise NotImplementedError

    def _random_delay(self, min_s=1, max_s=3):
        return random.uniform(min_s, max_s)
