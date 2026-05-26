"""
analysis/analytics.py — Full analytics engine
Prints reports, generates insights, tracks growth
"""

import sqlite3
from datetime import datetime
from memory.database import Database
from llm_router import LLMRouter
from config import DB_PATH


class Analytics:
    def __init__(self, db: Database, llm: LLMRouter):
        self.db = db
        self.llm = llm

    def print_dashboard(self):
        """Print full analytics dashboard to terminal"""
        print("\n" + "="*60)
        print("📊 QUANTEVE AGENT — ANALYTICS DASHBOARD")
        print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)

        self._print_daily_stats()
        self._print_content_performance()
        self._print_topic_performance()
        self._print_action_success()
        self._print_recent_strategies()

        print("="*60 + "\n")

    def _print_daily_stats(self):
        print("\n📅 DAILY STATS (Last 7 Days)")
        print("-" * 40)
        stats = self.db.get_daily_stats(7)
        if not stats:
            print("  No data yet")
            return

        print(f"  {'Date':<12} {'Platform':<12} {'Likes':<8} {'Comments':<10} {'Posts':<8} {'Follows':<8}")
        for row in stats:
            print(f"  {row[1]:<12} {row[2]:<12} {row[3]:<8} {row[4]:<10} {row[6]:<8} {row[5]:<8}")

    def _print_content_performance(self):
        print("\n✍️  TOP CONTENT GENERATED")
        print("-" * 40)
        content = self.db.get_best_content(limit=5)
        if not content:
            print("  No content generated yet")
            return

        for row in content:
            print(f"  [{row[0]}] {row[1]} → @{row[2]}")
            print(f"  Score: {row[4]} | Model: {row[5]}")
            print(f"  \"{row[3][:80]}...\"")
            print()

    def _print_topic_performance(self):
        print("\n🎯 TOPIC PERFORMANCE")
        print("-" * 40)
        topics = self.db.get_topic_performance()
        if not topics:
            print("  No topic data yet")
            return

        for row in topics:
            bar = "█" * int(row[2] or 0)
            print(f"  {row[0]:<25} Count:{row[1]:<5} Avg Score: {row[2]:.1f} {bar}")

    def _print_action_success(self):
        print("\n✅ ACTION SUCCESS RATES")
        print("-" * 40)
        rates = self.db.get_action_success_rate()
        if not rates:
            print("  No action data yet")
            return

        for key, val in rates.items():
            print(f"  {key:<20} {val['success']}/{val['total']} ({val['rate']}%)")

    def _print_recent_strategies(self):
        print("\n🧠 RECENT STRATEGY INSIGHTS")
        print("-" * 40)
        strategies = self.db.get_strategy_log(3)
        if not strategies:
            print("  No strategies logged yet")
            return

        for row in strategies:
            print(f"  [{row[5][:10]}] {row[0]}")
            print(f"  → {row[2][:100]}...")
            print()

    def get_summary_stats(self) -> dict:
        """Get summary stats as dict for Telegram reporting"""
        with sqlite3.connect(DB_PATH) as conn:
            total_posts_seen = conn.execute("SELECT COUNT(*) FROM posts_seen").fetchone()[0]
            total_actions = conn.execute("SELECT COUNT(*) FROM actions_taken").fetchone()[0]
            total_content = conn.execute("SELECT COUNT(*) FROM content_generated").fetchone()[0]
            total_published = conn.execute("SELECT COUNT(*) FROM posts_published").fetchone()[0]
            success_actions = conn.execute("SELECT COUNT(*) FROM actions_taken WHERE success=1").fetchone()[0]

        return {
            "posts_seen": total_posts_seen,
            "actions_taken": total_actions,
            "content_generated": total_content,
            "posts_published": total_published,
            "action_success_rate": round(success_actions/total_actions*100, 1) if total_actions > 0 else 0
        }

    def export_to_csv(self, table: str, filename: str = None):
        """Export any table to CSV for Excel analysis"""
        import csv
        filename = filename or f"{table}_{datetime.now().strftime('%Y%m%d')}.csv"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(f"SELECT * FROM {table}")
            headers = [d[0] for d in cursor.description]
            rows = cursor.fetchall()

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"✅ Exported {len(rows)} rows to {filename}")
        return filename
