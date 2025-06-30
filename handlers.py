from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging
from typing import Dict, Any, Optional, Tuple
from quote_bot.db.interaction_repository import get_quote_interaction, update_quote_interaction, get_user_favorites, get_quotes_by_interaction
from quote_bot.db.quote_repository import get_quote_by_id

logger = logging.getLogger(__name__)

# Constants for callback data
LIKE_CALLBACK = "like_"
DISLIKE_CALLBACK = "dislike_"
FAVORITE_CALLBACK = "favorite_"
UNFAVORITE_CALLBACK = "unfavorite_"

def get_quote_keyboard(quote_id: int, user_id: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with like/dislike and favorite buttons for a quote.
    
    Args:
        quote_id: The ID of the quote
        user_id: The ID of the user to check current interactions
        
    Returns:
        InlineKeyboardMarkup with appropriate buttons
    """
    interaction = get_quote_interaction(user_id, quote_id)
    
    like_emoji = "❤️" if (interaction and interaction.get('is_liked')) else "🤍"
    dislike_emoji = "👎" if (interaction and interaction.get('is_disliked')) else "👎"
    favorite_emoji = "⭐" if (interaction and interaction.get('is_favorited')) else "☆"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{like_emoji} Like", callback_data=f"{LIKE_CALLBACK}{quote_id}"),
            InlineKeyboardButton(f"{dislike_emoji} Dislike", callback_data=f"{DISLIKE_CALLBACK}{quote_id}"),
            InlineKeyboardButton(f"{favorite_emoji} Save", 
                              callback_data=f"{FAVORITE_CALLBACK if not (interaction and interaction.get('is_favorited')) else UNFAVORITE_CALLBACK}{quote_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles like button clicks."""
    await handle_quote_interaction(update, context, 'like')

async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles dislike button clicks."""
    await handle_quote_interaction(update, context, 'dislike')

async def handle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles favorite button clicks."""
    await handle_quote_interaction(update, context, 'favorite')

async def handle_quote_interaction(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str
) -> None:
    """
    Process 👍 👎 ⭐ clicks.

    action is one of: 'like', 'dislike', 'favorite', 'remove_favorite'
    """
    query = update.callback_query
    await query.answer()

    user_id  = query.from_user.id
    quote_id = int(query.data.split("_")[1])          # e.g. like_17 → 17

    # Map action → column we need to set to 1
    column_map = {
        "like":            "is_liked",
        "dislike":         "is_disliked",
        "favorite":        "is_favorited",
        "remove_favorite": "is_favorited"
    }

    # Build kwargs for update_quote_interaction
    payload = {column_map[action]: 0 if action == "remove_favorite" else 1}

    # When liking, clear dislike; when disliking, clear like
    if action == "like":
        payload["is_disliked"] = 0
    elif action == "dislike":
        payload["is_liked"] = 0

    try:
        update_quote_interaction(user_id, quote_id, **payload)

        # Refresh buttons
        keyboard = get_quote_keyboard(quote_id, user_id)
        await query.edit_message_reply_markup(reply_markup=keyboard)

        # Optional toast
        if action == "favorite":
            await query.answer("Saved to favourites ⭐️", show_alert=False)
        elif action == "remove_favorite":
            await query.answer("Removed from favourites", show_alert=False)

    except Exception as e:
        logger.error("handle_quote_interaction failed: %s", e, exc_info=True)
        await query.answer("DB error; try again later.", show_alert=True)

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the user's favorite quotes."""
    user_id = update.effective_user.id
    
    # Get favorite quotes with details
    favorites = get_quotes_by_interaction(user_id, 'favorited')
    
    if not favorites:
        await update.message.reply_text("You don't have any favorite quotes yet!")
        return
    
    # Build the message with favorite quotes
    message = "⭐ <b>Your Favorite Quotes</b> ⭐\n\n"
    
    for idx, quote in enumerate(favorites[:10], 1):  # Show first 10 favorites
        message += f"{idx}. {quote['quote']}"
        if quote.get('author'):
            message += f"\n   - <i>{quote['author']}</i>"
        message += "\n\n"
    
    if len(favorites) > 10:
        message += "\nUse /favorites2 to see more."
    
    await update.message.reply_text(message, parse_mode='HTML')

# Register the callback handlers
def register_handlers(application):
    """Registers all callback query handlers."""
    application.add_handler(CallbackQueryHandler(handle_like, pattern=f"^{LIKE_CALLBACK}\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_dislike, pattern=f"^{DISLIKE_CALLBACK}\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_favorite, pattern=f"^{FAVORITE_CALLBACK}\\d+$"))
    application.add_handler(CallbackQueryHandler(handle_unfavorite, pattern=f"^{UNFAVORITE_CALLBACK}\\d+$"))
