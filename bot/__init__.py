"""Main bot package for the Quote of the Day Bot."""

from .handlers import setup_handlers
from .services.scheduler import scheduler_service

__all__ = ['setup_handlers', 'scheduler_service']
