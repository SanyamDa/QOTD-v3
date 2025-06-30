"""Database connection and initialization for the Quote Bot application."""
import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "quote_bot.db")
print("🔍 Using database:", DB_FILE)

def get_connection() -> sqlite3.Connection:
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
            quote_text TEXT,
            quote_author TEXT,
            is_liked INTEGER DEFAULT 0,
            is_disliked INTEGER DEFAULT 0,
            is_favorited INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, quote_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Create indexes for better query performance
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_quote_interactions_user 
        ON quote_interactions(user_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_quote_interactions_quote 
        ON quote_interactions(quote_id)
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully.")
        
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Initialize the database when this module is imported
init_db()
