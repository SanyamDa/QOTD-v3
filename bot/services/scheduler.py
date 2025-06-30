"""Scheduling service for the Quote Bot."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Awaitable, Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Handles ALL scheduling (per-user & global) for the bot."""

    def __init__(self, default_tz: str = "UTC") -> None:
        self.default_tz = default_tz
        self.scheduler  = AsyncIOScheduler(timezone=pytz.timezone(default_tz))

    # ─────────────── LIFECYCLE ────────────────
    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started (default tz %s)", self.default_tz)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

    # ─────────────── GLOBAL DAILY JOB ────────────────
    def schedule_global_daily(
        self,
        coro: Callable[[], Awaitable[None]],
        hour: int = 7,
        minute: int = 0,
    ) -> None:
        """Run *one* coroutine once a day at server time."""
        self._replace_job(
            "global_daily",
            coro,
            CronTrigger(hour=hour, minute=minute, timezone=self.scheduler.timezone),
        )
        logger.info("Global daily job scheduled for %02d:%02d", hour, minute)

    # ─────────────── USER-SPECIFIC DAILY JOB ────────────────
    def schedule_user_daily_quote(
        self,
        user_id: int,
        prefs: dict,
        coro: Callable[[int], Awaitable[None]],
    ) -> None:
        """
        Schedule the quote-delivery coroutine for one user.

        • Skips weekends if weekend_toggle == 0  
        • Uses the user’s timezone & HH:MM stored in *prefs*
        """
        delivery_time = prefs.get("delivery_time", "07:00")
        hour, minute  = map(int, delivery_time.split(":"))
        tz_name       = prefs.get("timezone", self.default_tz)
        weekends_ok   = bool(prefs.get("weekend_toggle", 1))

        job_id = f"daily_quote_{user_id}"
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass  # job did not exist – fine

        day_of_week = "*" if weekends_ok else "mon-fri"

        self.scheduler.add_job(
            coro,
            trigger="cron",
            id=job_id,
            name=f"daily quote for {user_id}",
            timezone=pytz.timezone(tz_name),
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            args=[user_id],          # pass the user_id to the coroutine
            replace_existing=True,
        )
        logger.info(
            "Scheduled daily quote for %s at %02d:%02d %s (%s)",
            user_id,
            hour,
            minute,
            tz_name,
            "weekends OK" if weekends_ok else "weekdays only",
        )

    # ─────────────── HELPERS ────────────────
    def _replace_job(self, job_id: str, func, trigger) -> None:
        """Safely replace an existing job."""
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
        self.scheduler.add_job(func, trigger, id=job_id, replace_existing=True)

    def next_run(self, job_id: str) -> Optional[datetime]:
        job = self.scheduler.get_job(job_id)
        return job.next_run_time if job else None


# Singleton instance used throughout the project
scheduler_service = SchedulerService()
