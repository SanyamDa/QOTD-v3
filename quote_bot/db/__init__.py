"""Database package for the Quote Bot application."""

from .database import get_connection, init_db
from .models import User, UserPreferences, QuoteInteraction
from .user_repository import add_user, update_user_status, get_active_users, get_user
from .preference_repository import save_user_preferences, get_user_preferences, get_all_users_with_preferences
from .interaction_repository import (
    get_quote_interaction, update_quote_interaction,
    toggle_like, toggle_dislike, toggle_favorite,
    get_disliked_quote_ids, get_quotes_by_interaction
)
from .quote_repository import get_quote_by_id, get_random_quote, search_quotes

__all__ = [
    'get_connection', 'init_db',
    'User', 'UserPreferences', 'QuoteInteraction',
    'add_user', 'update_user_status', 'get_active_users', 'get_user',
    'save_user_preferences', 'get_user_preferences', 'get_all_users_with_preferences',
    'get_quote_interaction', 'update_quote_interaction',
    'toggle_like', 'toggle_dislike', 'toggle_favorite',
    'get_disliked_quote_ids', 'get_quotes_by_interaction',
    'get_quote_by_id', 'get_random_quote', 'search_quotes'
]
