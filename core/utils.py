"""
core/utils.py — Shared Utilities (Kafka, Telegram)
"""

import json
import telegram
from config import KAFKA, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def get_kafka_router():
    if KAFKA["enabled"]:
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=KAFKA["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Kafka connected")
            return producer
        except Exception as e:
            print(f"⚠️ Kafka unavailable: {e}")
    return None

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
