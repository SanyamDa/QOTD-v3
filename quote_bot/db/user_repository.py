"""User-related database operations for the Quote Bot application."""
import logging
from typing import List, Optional
from .database import get_connection
from .models import User
import datetime
from .database import get_connection

logger = logging.getLogger(__name__)

def add_user(user_id: int, first_name: Optional[str] = None, username: Optional[str] = None) -> None:
    """Add a new user to the database or update existing user's info."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (user_id, username, first_name, is_paused)
            VALUES (?, ?, ?, 0)
            """,
            (user_id, username, first_name)
        )
        conn.commit()
        logger.info(f"Added/updated user {user_id} in the database")
    except Exception as e:
        logger.error(f"Error adding/updating user {user_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_user_status(user_id: int, is_paused: bool) -> None:
    """Update a user's pause status."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_paused = ? WHERE user_id = ?",
            (1 if is_paused else 0, user_id)
        )
        conn.commit()
        logger.info(f"Updated status for user {user_id}: {'paused' if is_paused else 'active'}")
    except Exception as e:
        logger.error(f"Error updating user {user_id} status: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_active_users() -> List[int]:
    """Get a list of active user IDs."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_paused = 0")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_all_user_ids() -> list[int]:
    """
    Return *all* user IDs, even if they have paused daily quotes.
    Used by the scheduler when the bot boots.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_user(user_id: int) -> Optional[User]:
    """Get a user by ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, first_name, is_paused, created_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return User(
                user_id=result[0],
                username=result[1],
                first_name=result[2],
                is_paused=bool(result[3]),
                created_at=result[4]
            )
        return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_prefs(user_id: int) -> dict:
    """
    Return the user’s onboarding answers **plus** weekend flag,
    preferred delivery time and timezone.  
    Keys absent in the DB are returned as None/0.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT topic1,
                   topic2,
                   topic3,
                   tone,
                   quote_length,
                   context_line,          -- 0 = no takeaway, 1 = yes
                   weekend_toggle,
                   delivery_time,         -- "HH:MM" string
                   COALESCE(timezone, 'UTC') AS timezone
            FROM   user_preferences
            WHERE  user_id = ?
            """,
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return {}

        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()

def record_daily_interaction(user_id: int) -> int:
    """
    If this is the first interaction today, bump or reset the streak.
    Returns the new streak_count, or 0 if already recorded today.
    """
    today = datetime.date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT streak_count, last_streak_date FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return 0

    streak_count, last_date = row
    if last_date == today:
        conn.close()
        return 0  # already recorded today
    
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    if last_date == yesterday:
        streak_count += 1
    else:
        streak_count = 1
    
    cur.execute(
        "UPDATE users SET streak_count = ?, last_streak_date = ? WHERE user_id = ?",
        (streak_count, today, user_id)
    )
    conn.commit()
    conn.close()
    return streak_count

def get_streak_badge(streak: int) -> str:
    """Return badge name/emoji for a given streak."""
    if streak >= 30:
        return "🏆 Gold Bibliophile"
    if streak >= 7:
        return "🥈 Silver Reader"
    if streak >= 3:
        return "🥉 Bronze Bookworm"
    return ""