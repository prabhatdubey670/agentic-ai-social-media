"""
core/storage.py — Full database layer
All posts, actions, content, analytics, strategies saved
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS posts_seen (
        id TEXT PRIMARY KEY, platform TEXT, author TEXT, author_handle TEXT,
        post_text TEXT, post_url TEXT, topic_matched TEXT, value_score INTEGER DEFAULT 0,
        sentiment TEXT, engagement_potential INTEGER DEFAULT 0,
        seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS actions_taken (
        id TEXT PRIMARY KEY, post_id TEXT, platform TEXT, action_type TEXT,
        content_generated TEXT, claude_reasoning TEXT, model_used TEXT,
        success INTEGER DEFAULT 0, error_message TEXT,
        acted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts_seen(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS content_generated (
        id TEXT PRIMARY KEY, content_type TEXT, platform TEXT,
        target_author TEXT, input_context TEXT, generated_text TEXT,
        tokens_used INTEGER DEFAULT 0, model_used TEXT, quality_score INTEGER DEFAULT 0,
        was_posted INTEGER DEFAULT 0, engagement_received INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS posts_published (
        id TEXT PRIMARY KEY, platform TEXT, post_text TEXT,
        topic TEXT, post_type TEXT, model_used TEXT,
        likes_received INTEGER DEFAULT 0, comments_received INTEGER DEFAULT 0,
        reposts_received INTEGER DEFAULT 0, views_received INTEGER DEFAULT 0,
        posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
        id TEXT PRIMARY KEY, date TEXT, platform TEXT,
        likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0,
        follows INTEGER DEFAULT 0, dms INTEGER DEFAULT 0,
        posts_published INTEGER DEFAULT 0, posts_evaluated INTEGER DEFAULT 0,
        posts_skipped INTEGER DEFAULT 0, new_followers INTEGER DEFAULT 0,
        profile_views INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS strategy_log (
        id TEXT PRIMARY KEY, strategy_name TEXT, insight TEXT,
        action_recommended TEXT, was_applied INTEGER DEFAULT 0,
        impact_score INTEGER DEFAULT 0, model_used TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS top_performers (
        id TEXT PRIMARY KEY, platform TEXT, author TEXT,
        author_handle TEXT, profile_url TEXT, niche TEXT,
        follower_count INTEGER DEFAULT 0, avg_engagement REAL DEFAULT 0,
        why_valuable TEXT, tracked_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS error_log (
        id TEXT PRIMARY KEY, platform TEXT, error_type TEXT,
        error_message TEXT, context TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS content_queue (
        id TEXT PRIMARY KEY, platform TEXT, content_type TEXT,
        topic TEXT, content_text TEXT, status TEXT DEFAULT 'draft',
        scheduled_for TEXT, source_model TEXT, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    print("✅ Database ready")


class Database:
    def __init__(self):
        init_db()

    def _conn(self):
        return sqlite3.connect(DB_PATH)

    def save_post_seen(self, platform, author, author_handle, post_text,
                       post_url="", topic="", value_score=0, sentiment="neutral",
                       engagement_potential=0) -> str:
        pid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO posts_seen
                (id, platform, author, author_handle, post_text, post_url,
                topic_matched, value_score, sentiment, engagement_potential)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (pid, platform, author, author_handle, post_text, post_url,
                 topic, value_score, sentiment, engagement_potential))
        return pid

    def save_action(self, post_id, platform, action_type, content="",
                    reasoning="", model_used="", success=False, error="") -> str:
        aid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO actions_taken
                (id, post_id, platform, action_type, content_generated,
                claude_reasoning, model_used, success, error_message)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (aid, post_id, platform, action_type, content,
                 reasoning, model_used, int(success), error))
        return aid

    def save_content(self, content_type, platform, target_author, input_context,
                     generated_text, tokens=0, model="", quality_score=0) -> str:
        cid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO content_generated
                (id, content_type, platform, target_author, input_context,
                generated_text, tokens_used, model_used, quality_score)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (cid, content_type, platform, target_author, input_context,
                 generated_text, tokens, model, quality_score))
        return cid

    def save_published_post(self, platform, post_text, topic, post_type, model) -> str:
        pid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO posts_published
                (id, platform, post_text, topic, post_type, model_used)
                VALUES (?,?,?,?,?,?)''',
                (pid, platform, post_text, topic, post_type, model))
        return pid

    def save_strategy(self, name, insight, action, model) -> str:
        sid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO strategy_log
                (id, strategy_name, insight, action_recommended, model_used)
                VALUES (?,?,?,?,?)''',
                (sid, name, insight, action, model))
        return sid

    def save_top_performer(self, platform, author, handle, url, niche,
                           followers, avg_engagement, why_valuable):
        with self._conn() as conn:
            conn.execute('''INSERT OR REPLACE INTO top_performers
                (id, platform, author, author_handle, profile_url, niche,
                follower_count, avg_engagement, why_valuable)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (str(uuid.uuid4()), platform, author, handle, url, niche,
                 followers, avg_engagement, why_valuable))

    def update_daily_stats(self, platform, field, amount=1):
        today = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as conn:
            existing = conn.execute(
                'SELECT id FROM daily_stats WHERE date=? AND platform=?',
                (today, platform)).fetchone()
            if existing:
                conn.execute(f'UPDATE daily_stats SET {field}={field}+? WHERE date=? AND platform=?',
                           (amount, today, platform))
            else:
                conn.execute('INSERT INTO daily_stats (id, date, platform) VALUES (?,?,?)',
                           (str(uuid.uuid4()), today, platform))
                conn.execute(f'UPDATE daily_stats SET {field}=? WHERE date=? AND platform=?',
                           (amount, today, platform))

    def log_error(self, platform, error_type, message, context=""):
        with self._conn() as conn:
            conn.execute('INSERT INTO error_log (id, platform, error_type, error_message, context) VALUES (?,?,?,?,?)',
                        (str(uuid.uuid4()), platform, error_type, message, context))

    def queue_content(self, platform, content_type, topic, content_text,
                      source_model="", notes="", scheduled_for="") -> str:
        qid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute('''INSERT INTO content_queue
                (id, platform, content_type, topic, content_text,
                source_model, notes, scheduled_for)
                VALUES (?,?,?,?,?,?,?,?)''',
                (qid, platform, content_type, topic, content_text,
                 source_model, notes, scheduled_for))
        return qid

    def get_queued_content(self, status="draft", limit=20) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT id, platform, content_type, topic,
                content_text, status, scheduled_for, source_model, created_at
                FROM content_queue WHERE status=?
                ORDER BY created_at DESC LIMIT ?''', (status, limit)).fetchall()

    def approve_content(self, item_id: str):
        with self._conn() as conn:
            conn.execute('''UPDATE content_queue
                SET status='approved', approved_at=CURRENT_TIMESTAMP
                WHERE id=?''', (item_id,))

    def mark_content_posted(self, item_id: str):
        with self._conn() as conn:
            conn.execute("UPDATE content_queue SET status='posted' WHERE id=?", (item_id,))

    # ── ANALYTICS QUERIES ──────────────────────────────────────
    def get_top_posts(self, limit=10) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT author, post_text, value_score, platform, topic_matched, seen_at
                FROM posts_seen ORDER BY value_score DESC LIMIT ?''', (limit,)).fetchall()

    def get_daily_stats(self, days=30) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT * FROM daily_stats ORDER BY date DESC LIMIT ?''', (days,)).fetchall()

    def get_best_content(self, content_type=None, limit=10) -> list:
        with self._conn() as conn:
            if content_type:
                return conn.execute('''SELECT content_type, platform, target_author, generated_text,
                    quality_score, model_used, created_at FROM content_generated
                    WHERE content_type=? ORDER BY quality_score DESC LIMIT ?''',
                    (content_type, limit)).fetchall()
            return conn.execute('''SELECT content_type, platform, target_author, generated_text,
                quality_score, model_used, created_at FROM content_generated
                ORDER BY quality_score DESC LIMIT ?''', (limit,)).fetchall()

    def get_action_success_rate(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute('''SELECT action_type, platform,
                COUNT(*) as total, SUM(success) as successful
                FROM actions_taken GROUP BY action_type, platform''').fetchall()
        result = {}
        for row in rows:
            key = f"{row[1]}_{row[0]}"
            result[key] = {"total": row[2], "success": row[3],
                          "rate": round(row[3]/row[2]*100, 1) if row[2] > 0 else 0}
        return result

    def get_strategy_log(self, limit=20) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT strategy_name, insight, action_recommended,
                was_applied, impact_score, logged_at FROM strategy_log
                ORDER BY logged_at DESC LIMIT ?''', (limit,)).fetchall()

    def get_published_posts(self, limit=20) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT platform, post_text, topic, post_type,
                likes_received, comments_received, posted_at
                FROM posts_published ORDER BY posted_at DESC LIMIT ?''', (limit,)).fetchall()

    def get_topic_performance(self) -> list:
        with self._conn() as conn:
            return conn.execute('''SELECT topic_matched, COUNT(*) as count,
                AVG(value_score) as avg_score FROM posts_seen
                GROUP BY topic_matched ORDER BY avg_score DESC''').fetchall()
