import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)
DB_FILE = "bot_database.db"

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_FILE)

def init_db() -> None:
    """Initialize the database and create necessary tables if they don't exist."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_paused INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # User preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            topics TEXT,
            tone TEXT,
            quote_length TEXT,
            author_pref TEXT,
            delivery_time TEXT,
            weekend_toggle INTEGER DEFAULT 1,
            context_line INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Quote interactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quote_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quote_id INTEGER,
            is_liked INTEGER DEFAULT 0,
            is_disliked INTEGER DEFAULT 0,
            is_favorited INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, quote_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        conn.commit()
        logger.info("Database initialized successfully.")
        
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

def add_user(user_id: int, first_name: str, username: str = None) -> None:
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
    except sqlite3.Error as e:
        logger.error(f"Error adding user {user_id}: {e}")
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
    except sqlite3.Error as e:
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
    except sqlite3.Error as e:
        logger.error(f"Error getting active users: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """Get a user's preferences."""
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
    except sqlite3.Error as e:
        logger.error(f"Error getting preferences for user {user_id}: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_quote_interaction(user_id: int, quote_id: int) -> Dict[str, bool]:
    """Get a user's interaction with a specific quote."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT is_liked, is_disliked, is_favorited
            FROM quote_interactions
            WHERE user_id = ? AND quote_id = ?
            """,
            (user_id, quote_id)
        )
        result = cursor.fetchone()
        if result:
            return {
                'is_liked': bool(result[0]),
                'is_disliked': bool(result[1]),
                'is_favorited': bool(result[2])
            }
        return {'is_liked': False, 'is_disliked': False, 'is_favorited': False}
    except sqlite3.Error as e:
        logger.error(f"Error getting quote interaction: {e}")
        return {'is_liked': False, 'is_disliked': False, 'is_favorited': False}
    finally:
        if conn:
            conn.close()

def update_quote_interaction(user_id: int, quote_id: int, **updates) -> None:
    """Update a user's interaction with a quote."""
    if not updates:
        return
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if interaction exists
        cursor.execute(
            "SELECT id FROM quote_interactions WHERE user_id = ? AND quote_id = ?",
            (user_id, quote_id)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update existing interaction
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [user_id, quote_id]
            cursor.execute(
                f"UPDATE quote_interactions SET {set_clause} WHERE user_id = ? AND quote_id = ?",
                values
            )
        else:
            # Insert new interaction
            columns = ["user_id", "quote_id"] + list(updates.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = [user_id, quote_id] + list(updates.values())
            cursor.execute(
                f"INSERT INTO quote_interactions ({', '.join(columns)}) VALUES ({placeholders})",
                values
            )
        
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error updating quote interaction: {e}")
        raise
    finally:
        if conn:
            conn.close()

def toggle_like(user_id: int, quote_id: int) -> None:
    """Toggle like status for a quote."""
    interaction = get_quote_interaction(user_id, quote_id)
    update_quote_interaction(
        user_id, 
        quote_id,
        is_liked=1 if not interaction['is_liked'] else 0,
        is_disliked=0  # Remove dislike if user likes
    )

def toggle_dislike(user_id: int, quote_id: int) -> None:
    """Toggle dislike status for a quote."""
    interaction = get_quote_interaction(user_id, quote_id)
    update_quote_interaction(
        user_id, 
        quote_id,
        is_disliked=1 if not interaction['is_disliked'] else 0,
        is_liked=0  # Remove like if user dislikes
    )

def toggle_favorite(user_id: int, quote_id: int, is_favorite: bool = None) -> None:
    """Toggle or set favorite status for a quote."""
    if is_favorite is None:
        interaction = get_quote_interaction(user_id, quote_id)
        is_favorite = not interaction['is_favorited']
    
    update_quote_interaction(
        user_id,
        quote_id,
        is_favorited=1 if is_favorite else 0
    )

def get_disliked_quote_ids(user_id: int) -> List[int]:
    """Get a list of quote IDs that the user has disliked."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT quote_id FROM quote_interactions WHERE user_id = ? AND is_disliked = 1",
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error getting disliked quotes for user {user_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Initialize the database when this module is imported
init_db()


