"""Background tasks related to quotes."""
import logging
from typing import TYPE_CHECKING
import datetime    

if TYPE_CHECKING:
    from telegram import Bot
    from telegram.ext import CallbackContext

from bot.services import quote_service
from bot.utils.helpers import escape_markdown
from quote_bot.db import get_user_preferences

logger = logging.getLogger(__name__)

async def send_daily_quotes_task(bot: 'Bot') -> None:
    """Task to send daily quotes to all active users.
    
    Args:
        bot: The Telegram bot instance
    """
    from quote_bot.db import get_active_users
    import asyncio
    
    user_ids = get_active_users()
    logger.info(f"Scheduler running for {len(user_ids)} active users.")
    
    # Process users in batches to avoid rate limiting
    BATCH_SIZE = 10
    for i in range(0, len(user_ids), BATCH_SIZE):
        batch = user_ids[i:i+BATCH_SIZE]
        # Process batch concurrently
        await asyncio.gather(
            *[send_quote_to_user(bot, user_id) for user_id in batch],
            return_exceptions=True
        )
        # Small delay between batches
        await asyncio.sleep(1)

async def send_quote_to_user(bot: 'Bot', user_id: int) -> None:
    """Send a personalized quote to a specific user.
    
    Args:
        bot: The Telegram bot instance
        user_id: The ID of the user to send the quote to
    """
    # Get user preferences
    prefs = get_user_preferences(user_id)

    if not prefs.get("weekend_toggle", 1):              # 0 = off, 1 = on
        today = datetime.date.today().weekday()         # 0-Mon … 5-Sat 6-Sun
        if today in (5, 6):                             # Sat/Sun
            return 
    
    # Get a personalized quote
    quote_data = quote_service.get_quote_for_user(user_id, prefs or {})
    
    if not quote_data:
        logger.warning(f"No quote found for user {user_id}")
        await bot.send_message(
            chat_id=user_id,
            text="I couldn't find a suitable quote for you right now. Try again later!"
        )
        return
    
    # Format the quote
    quote_text = f'"{escape_markdown(quote_data["quote"])}"'
    if quote_data.get('author'):
        quote_text += f'\n\n- {escape_markdown(quote_data["author"])}'
    
    # Get the keyboard with like/dislike/favorite buttons
    from bot.handlers.callbacks import get_quote_keyboard
    keyboard = get_quote_keyboard(quote_data['id'], user_id)
    
    # Send the quote
    await bot.send_message(
        chat_id=user_id,
        text=quote_text,
        reply_markup=keyboard,
        parse_mode='MarkdownV2'
    )
    logger.info(f"Sent quote {quote_data['id']} to user {user_id}")
