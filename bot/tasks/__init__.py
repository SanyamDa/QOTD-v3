"""Background tasks for the Quote Bot."""
from .quote_tasks import send_daily_quotes_task

__all__ = ['send_daily_quotes_task']
