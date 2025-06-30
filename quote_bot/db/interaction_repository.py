"""Quote interaction database operations for the Quote Bot application."""
import logging
from typing import List, Dict, Optional, Tuple
from .database import get_connection
from .models import QuoteInteraction

logger = logging.getLogger(__name__)

def get_quote_interaction(user_id: int, quote_id: int) -> Dict[str, bool]:
    """
    Get a user's interaction with a specific quote.
    
    Args:
        user_id: The Telegram user ID
        quote_id: The ID of the quote
        
    Returns:
        Dictionary with interaction status (liked, disliked, favorited)
    """
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
    except Exception as e:
        logger.error(f"Error getting quote interaction: {e}")
        return {'is_liked': False, 'is_disliked': False, 'is_favorited': False}
    finally:
        if conn:
            conn.close()

def update_quote_interaction(user_id: int, quote_id: int, **updates) -> None:
    """
    Update a user's interaction with a quote.
    
    Args:
        user_id: The Telegram user ID
        quote_id: The ID of the quote
        **updates: Dictionary of fields to update (is_liked, is_disliked, is_favorited)
    """
    if not updates:
        return
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Log the update attempt
        logger.debug(f"Updating interaction - User: {user_id}, Quote: {quote_id}, Updates: {updates}")
        
        # Check if interaction exists
        cursor.execute(
            "SELECT id, is_liked, is_disliked, is_favorited FROM quote_interactions WHERE user_id = ? AND quote_id = ?",
            (user_id, quote_id)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update existing interaction
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(updates.values()) + [user_id, quote_id]
            query = f"UPDATE quote_interactions SET {set_clause} WHERE user_id = ? AND quote_id = ?"
            logger.debug(f"Executing update query: {query} with values {values}")
            cursor.execute(query, values)
        else:
            # Insert new interaction
            columns = ["user_id", "quote_id"] + list(updates.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = [user_id, quote_id] + list(updates.values())
            query = f"INSERT INTO quote_interactions ({', '.join(columns)}) VALUES ({placeholders})"
            logger.debug(f"Executing insert query: {query} with values {values}")
            cursor.execute(query, values)
        
        # Verify the update/insert was successful
        cursor.execute(
            "SELECT is_liked, is_disliked, is_favorited FROM quote_interactions WHERE user_id = ? AND quote_id = ?",
            (user_id, quote_id)
        )
        result = cursor.fetchone()
        logger.debug(f"Verification query result: {result}")
        
        conn.commit()
        logger.info(f"Successfully updated interaction - User: {user_id}, Quote: {quote_id}")
        
    except Exception as e:
        logger.error(f"Error updating quote interaction: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def toggle_like(user_id: int, quote_id: int) -> bool:
    """
    Toggle like status of a quote.
    If disliked, removes the dislike and adds a like.
    
    Args:
        user_id: The Telegram user ID
        quote_id: The ID of the quote to like
        
    Returns:
        bool: Current like status after the operation
    """
    interaction = get_quote_interaction(user_id, quote_id)
    
    if interaction['is_liked']:
        # Already liked, remove the like
        update_quote_interaction(
            user_id,
            quote_id,
            is_liked=0
        )
        return False
    else:
        # Not liked, add like and remove dislike
        update_quote_interaction(
            user_id, 
            quote_id,
            is_liked=1,
            is_disliked=0  # Remove dislike when liking
        )
        return True
    return True

def toggle_dislike(user_id: int, quote_id: int) -> bool:
    """
    Dislike a quote. If already disliked, does nothing.
    If liked, removes the like and adds a dislike.
    
    Args:
        user_id: The Telegram user ID
        quote_id: The ID of the quote to dislike
        
    Returns:
        bool: True if disliked, False if already disliked
    """
    interaction = get_quote_interaction(user_id, quote_id)
    
    # If already disliked, do nothing
    if interaction['is_disliked']:
        return False
        
    update_quote_interaction(
        user_id, 
        quote_id,
        is_disliked=1,
        is_liked=0  # Remove like when disliking
    )
    return True

def toggle_favorite(user_id: int, quote_id: int, is_favorite: bool = None) -> None:
    """
    Toggle or set favorite status for a quote.
    
    Args:
        user_id: The Telegram user ID
        quote_id: The ID of the quote to favorite/unfavorite
        is_favorite: Optional boolean to set favorite status directly
    """
    if is_favorite is None:
        interaction = get_quote_interaction(user_id, quote_id)
        is_favorite = not interaction['is_favorited']
    
    update_quote_interaction(
        user_id,
        quote_id,
        is_favorited=1 if is_favorite else 0
    )

def get_disliked_quote_ids(user_id: int) -> List[int]:
    """
    Get a list of quote IDs that the user has disliked.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        List of disliked quote IDs
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT quote_id FROM quote_interactions WHERE user_id = ? AND is_disliked = 1",
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting disliked quotes for user {user_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_favorite_quotes(user_id: int, limit: int = 10, offset: int = 0) -> List[dict]:
    """
    Get a user's favorite quotes.
    
    Args:
        user_id: The Telegram user ID
        limit: Maximum number of quotes to return
        offset: Offset for pagination
        
    Returns:
        List of dictionaries containing quote details
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT q.id, q.quote, q.author, qi.updated_at
            FROM quote_interactions qi
            JOIN quotes q ON qi.quote_id = q.id
            WHERE qi.user_id = ? AND qi.is_favorited = 1
            ORDER BY qi.updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        return [{
            'quote_id': row[0],
            'quote': row[1],
            'author': row[2],
            'updated_at': row[3]
        } for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting favorite quotes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_quotes_by_interaction(user_id: int, interaction_type: str, limit: int = 50) -> List[dict]:
    """
    Get a user's liked or disliked quotes.
    
    Args:
        user_id: The Telegram user ID
        interaction_type: Either 'liked' or 'disliked'
        limit: Maximum number of quotes to return
        
    Returns:
        List of dictionaries containing quote details
    """
    if interaction_type not in ['liked', 'disliked']:
        raise ValueError("interaction_type must be 'liked' or 'disliked'")
        
    column = 'is_liked' if interaction_type == 'liked' else 'is_disliked'
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT quote_id, quote_text, quote_author, updated_at
            FROM quote_interactions
            WHERE user_id = ? AND {column} = 1
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        
        return [{
            'quote_id': row[0],
            'quote': row[1] or 'Quote text not available',
            'author': row[2] or 'Unknown',
            'updated_at': row[3]
        } for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"Error getting {interaction_type} quotes: {e}")
        return []
    finally:
        if conn:
            conn.close()