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
        
        # Schedule the user's daily quote job with the updated preferences
        try:
            from bot.services.scheduler import scheduler_service
            from bot.tasks.quote_tasks import send_quote_to_user
            
            # Parse delivery time to handle test options like "21:35 (Test)"
            delivery_time = preferences.get('delivery_time', '07:00')
            if '(' in delivery_time:
                delivery_time = delivery_time.split('(')[0].strip()
            
            logger.info(f"Attempting to schedule user {user_id} for delivery at {delivery_time}")
            
            # Create preferences dict for scheduler
            scheduler_prefs = {
                'delivery_time': delivery_time,
                'weekend_toggle': preferences.get('weekend_toggle', True),
                'timezone': 'Asia/Bangkok'  # Use the timezone from .env
            }
            
            # Create a simple wrapper function
            async def send_quote_wrapper(uid: int):
                try:
                    # Get bot instance from scheduler service
                    if hasattr(scheduler_service, '_bot_instance') and scheduler_service._bot_instance:
                        logger.info(f"Sending quote to user {uid}")
                        await send_quote_to_user(scheduler_service._bot_instance, uid)
                    else:
                        logger.error(f"Bot instance not available for user {uid}")
                except Exception as e:
                    logger.error(f"Error sending quote to user {uid}: {e}")
            
            # Schedule the user's job
            scheduler_service.schedule_user_daily_quote(
                user_id, 
                scheduler_prefs, 
                send_quote_wrapper
            )
            logger.info(f"Successfully scheduled daily quote for user {user_id} at {delivery_time}")
            
        except Exception as scheduler_error:
            logger.error(f"Error scheduling daily quote for user {user_id}: {scheduler_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise here - preferences were saved successfully
        
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

def get_all_users_with_preferences() -> List[tuple]:
    """
    Get all users who have preferences set up.
    
    Returns:
        List of tuples (user_id, preferences_dict)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, topics, tone, quote_length, author_pref, delivery_time, 
                   weekend_toggle, context_line
            FROM user_preferences
            """
        )
        results = []
        for row in cursor.fetchall():
            user_id = row[0]
            prefs = {
                'topics': row[1].split(',') if row[1] else [],
                'tone': row[2],
                'quote_length': row[3],
                'author_pref': row[4],
                'delivery_time': row[5],
                'weekend_toggle': bool(row[6]),
                'context_line': bool(row[7]),
                'timezone': 'Asia/Bangkok'  # Default timezone
            }
            results.append((user_id, prefs))
        return results
    except Exception as e:
        logger.error(f"Error getting all users with preferences: {e}")
        return []
    finally:
        if conn:
            conn.close()
