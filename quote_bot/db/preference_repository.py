"""User preferences database operations for the Quote Bot application."""
import logging
from typing import Dict, Any, Optional, List
from .database import get_connection
from .models import UserPreferences

logger = logging.getLogger(__name__)

def save_user_preferences(user_id: int, preferences: Dict[str, Any]) -> None:
    """
    Save or update user preferences in the database.
    
    Args:
        user_id: The Telegram user ID
        preferences: Dictionary containing user preferences with keys:
            - topics: List of topics
            - tone: Preferred tone
            - quote_length: Preferred quote length
            - author_pref: Preferred authors
            - delivery_time: Preferred delivery time (HH:MM format)
            - weekend_toggle: Boolean for weekend delivery
            - context_line: Boolean for including context line
    """
    if not preferences:
        return
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Convert topics list to comma-separated string if it's a list
        topics = preferences.get('topics', [])
        if isinstance(topics, list):
            topics = ','.join(topics)
            
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences 
            (user_id, topics, tone, quote_length, author_pref, delivery_time, weekend_toggle, context_line)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            topics if topics else None,
            preferences.get('tone'),
            preferences.get('quote_length'),
            preferences.get('author_pref'),
            preferences.get('delivery_time', '07:00'),
            1 if preferences.get('weekend_toggle', True) else 0,
            1 if preferences.get('context_line', False) else 0
        ))
        conn.commit()
        logger.info(f"Saved preferences for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error saving preferences for user {user_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """
    Get a user's preferences from the database.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Dictionary containing user preferences or empty dict if not found
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT topics, tone, quote_length, author_pref, delivery_time, 
                   weekend_toggle, context_line
            FROM user_preferences
            WHERE user_id = ?
            """,
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return {
                'topics': result[0].split(',') if result[0] else [],
                'tone': result[1],
                'quote_length': result[2],
                'author_pref': result[3],
                'delivery_time': result[4],
                'weekend_toggle': bool(result[5]),
                'context_line': bool(result[6])
            }
        return {}
    except Exception as e:
        logger.error(f"Error getting preferences for user {user_id}: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_user_delivery_time(user_id: int) -> str:
    """
    Get a user's preferred delivery time.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Delivery time in 'HH:MM' format, or '07:00' if not set
    """
    prefs = get_user_preferences(user_id)
    return prefs.get('delivery_time', '07:00')

def get_users_by_delivery_time(hour: int, minute: int) -> List[int]:
    """
    Get all users who have scheduled delivery at the specified time.
    
    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        
    Returns:
        List of user IDs with matching delivery time
    """
    time_str = f"{hour:02d}:{minute:02d}"
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id FROM user_preferences 
            WHERE delivery_time = ?
            """,
            (time_str,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting users for delivery time {time_str}: {e}")
        return []
    finally:
        if conn:
            conn.close()
