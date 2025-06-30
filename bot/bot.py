"""Main entry point for the Quote Bot application."""
from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

from telegram.ext import Application
from telegram.request import HTTPXRequest

# ─── project imports ────────────────────────────────────────────
from bot.handlers import setup_handlers
from bot.tasks.quote_tasks import send_daily_quotes_task
from bot.services import quote_service, scheduler_service
from quote_bot.db import init_db

# ─── logging ────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# ────────────────────── PTB lifecycle hooks ────────────────────
async def _post_init(app: Application) -> None:
    """Runs once, right after PTB has started (event-loop alive)."""
    scheduler_service.start()

    async def _send_quotes_wrapper() -> None:
        # adapter: APScheduler → coroutine without parameters
        await send_daily_quotes_task(app.bot)

    # one global dispatch every day at 07:00 UTC (change if you like)
    scheduler_service.schedule_global_daily(_send_quotes_wrapper, hour=7, minute=0)
    logger.info("Daily-quote job scheduled (07:00 UTC) ✅")


async def _on_shutdown(_: Application) -> None:
    """Called when PTB begins shutting down (loop still alive)."""
    scheduler_service.shutdown()


# ─────────────────────────── main ──────────────────────────────
def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    # DB + quotes
    init_db()
    quote_service.load_quotes()

    # Telegram client
    request = HTTPXRequest(connect_timeout=10, read_timeout=30)
    application = (
        Application.builder()
        .token(token)
        .request(request)
        .build()
    )

    # handlers & lifecycle hooks
    setup_handlers(application)
    application.post_init     = _post_init
    application.post_shutdown = _on_shutdown

    logger.info("Bot is starting …")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
