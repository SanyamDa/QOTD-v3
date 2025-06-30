"""Handlers package for the Quote Bot."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import Application

from . import commands, callbacks, conversations


def setup_handlers(application: 'Application') -> None:
    """Set up all handlers for the bot.
    
    Args:
        application: The Telegram application
    """
    # Setup command handlers
    commands.setup_command_handlers(application)
    
    # Setup callback query handlers
    callbacks.setup_callback_handlers(application)
    
    # Setup conversation handlers (onboarding)
    conversations.setup_conversation_handlers(application)
    
    # Log that handlers were set up
    import logging
    logging.info("All handlers have been set up")
