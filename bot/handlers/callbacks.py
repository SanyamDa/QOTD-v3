"""Callback query handlers for the Quote Bot."""
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from telegram.constants import ParseMode
from typing import Tuple

from bot.utils.helpers import escape_markdown
from bot.services.quote_service import quote_service
from quote_bot.db.interaction_repository import (
    toggle_like,
    toggle_dislike,
    toggle_favorite,
    get_quote_interaction,
    update_quote_interaction
)
from quote_bot.db.user_repository import get_user

logger = logging.getLogger(__name__)

def _extract_quote_parts(message_text: str) -> tuple[str, str]:
    """Extract quote text and author from a formatted message."""
    if not message_text:
        return "Unknown quote", "Unknown"
    
    # Remove HTML tags for processing
    import re
    clean_text = re.sub(r'<[^>]+>', '', message_text)
    
    # Try to split by author pattern (— AuthorName)
    parts = clean_text.split('\n— ')
    if len(parts) == 2:
        quote_text = parts[0].strip().strip('"')
        author = parts[1].strip()
        return quote_text, author
    
    # Try to split by author pattern (- AuthorName)
    parts = clean_text.split('\n- ')
    if len(parts) == 2:
        quote_text = parts[0].strip().strip('"')
        author = parts[1].strip()
        return quote_text, author
    
    # If no author found, return the whole text as quote
    quote_text = clean_text.strip().strip('"')
    return quote_text, "Unknown"

def get_quote_keyboard(quote_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Generate an inline keyboard for a quote with like/dislike buttons.
    
    Args:
        quote_id: The ID of the quote
        user_id: The ID of the user
        
    Returns:
        InlineKeyboardMarkup: The generated keyboard
    """
    # Get the current interaction status
    interaction = get_quote_interaction(user_id, quote_id) or {}
    
    # Create buttons with appropriate emojis based on current state
    like_emoji = '👍' if not interaction.get('is_liked') else '❤️'
    dislike_emoji = '👎' if not interaction.get('is_disliked') else '💔'
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{like_emoji} Like",
                callback_data=f"like_{quote_id}"
            ),
            InlineKeyboardButton(
                f"{dislike_emoji} Dislike",
                callback_data=f"dislike_{quote_id}"
            )
        ],
        [
            InlineKeyboardButton("🔄 Another", callback_data=f"another_{quote_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    
    user_id = query.from_user.id
    action, *rest = query.data.split('_')
    quote_id = int(rest[0]) if rest else None
    
    if not quote_id:
        await query.answer("Error: Could not process this action.")
        return
    
    # Handle different actions
    if action == 'like':
        await handle_like(query, user_id, quote_id)
    elif action == 'dislike':
        await handle_dislike(query, user_id, quote_id)
    elif action == 'another':
        await handle_another_quote(query, user_id, quote_id)
    else:
        await query.answer("Unknown action")

async def handle_like(query, user_id: int, quote_id: int) -> None:
    """Handle like action."""
    try:
        # Get the current message text
        current_text = query.message.text
        
        # Extract quote text and author from the message
        quote_text, quote_author = _extract_quote_parts(current_text)
        
        # Always save to liked quotes (remove from disliked if exists)
        update_quote_interaction(
            user_id,
            quote_id,
            quote_text=quote_text,
            quote_author=quote_author,
            is_liked=1,
            is_disliked=0
        )
        
        # Get the updated keyboard
        keyboard = get_quote_keyboard(quote_id, user_id)
        
        # Update the message with the same text but updated keyboard
        await query.edit_message_text(
            text=current_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Send confirmation message
        await query.answer("Saved to liked quotes!")
        
    except Exception as e:
        logger.error(f"Error in handle_like: {e}", exc_info=True)
        await query.answer("Sorry, there was an error processing your like.")

async def handle_dislike(query, user_id: int, quote_id: int) -> None:
    """Handle dislike action."""
    try:
        # Get the current message text
        current_text = query.message.text
        
        # Extract quote text and author from the message
        quote_text, quote_author = _extract_quote_parts(current_text)
        
        # Always save to disliked quotes (remove from liked if exists)
        update_quote_interaction(
            user_id,
            quote_id,
            quote_text=quote_text,
            quote_author=quote_author,
            is_liked=0,
            is_disliked=1
        )
        
        # Get the updated keyboard
        keyboard = get_quote_keyboard(quote_id, user_id)
        
        # Update the message with the same text but updated keyboard
        await query.edit_message_text(
            text=current_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Send confirmation message
        await query.answer("Saved to disliked quotes!")
       
    except Exception as e:
        logger.error(f"Error in handle_dislike: {e}", exc_info=True)
        await query.answer("Sorry, there was an error processing your dislike.")

async def handle_another_quote(query, user_id: int, current_quote_id: int) -> None:
    """Handle request for another quote."""
    try:
        # Get user preferences
        user = get_user(user_id)
        prefs = {
            'is_paused': user.get('is_paused', False),
            'preferred_time': user.get('preferred_time'),
            'timezone': user.get('timezone')
        } if user else {}
        
        # Get a new quote
        quote_data = quote_service.get_quote_for_user(user_id, prefs)
        
        if not quote_data or quote_data['id'] == current_quote_id:
            await query.answer("No more quotes available right now!")
            return
        
        # Get the quote text and author, with proper escaping
        quote = escape_markdown(quote_data.get("quote", ""))
        author = escape_markdown(quote_data.get("author", ""))
        
        # Format the message with HTML
        message_text = f'<i>"{quote}"</i>'
        if author:
            message_text += f'<i>\n\n- {author}</i>'
        
        # Get the keyboard with like/dislike buttons
        keyboard = get_quote_keyboard(quote_data['id'], user_id)
        
        # Update the message with the new quote
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in handle_another_quote: {e}", exc_info=True)
        await query.answer("Sorry, there was an error getting another quote. Please try again.")

def setup_callback_handlers(application: Application) -> None:
    """Set up all callback query handlers."""
    # Create a single handler for all callback queries
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Remove the favorite handler since we're not using it anymore
    application.handlers[0] = [
        h for h in application.handlers[0] 
        if not (hasattr(h, 'callback') and h.callback.__name__ == 'handle_favorite')
    ]
    
    logger.info("Callback query handlers have been set up")
