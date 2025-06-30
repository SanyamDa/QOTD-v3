"""Quote-related database operations for the Quote Bot application."""
import logging
from typing import Dict, Optional, List, Any
from .database import get_connection
from .models import QuoteInteraction

logger = logging.getLogger(__name__)

def get_quote_by_id(quote_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a quote by its ID.
    
    Args:
        quote_id: The ID of the quote to retrieve
        
    Returns:
        Dictionary containing quote details or None if not found
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, quote, author, topic, tone, takeaway, created_at
            FROM quotes
            WHERE id = ?
            """,
            (quote_id,)
        )
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'quote': result[1],
                'author': result[2],
                'topic': result[3],
                'tone': result[4],
                'takeaway': result[5],
                'created_at': result[6]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting quote {quote_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_random_quote() -> Optional[Dict[str, Any]]:
    """
    Get a random quote from the database.
    
    Returns:
        Dictionary containing quote details or None if no quotes found
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, quote, author, topic, tone, takeaway, created_at
            FROM quotes
            ORDER BY RANDOM()
            LIMIT 1
            """
        )
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'quote': result[1],
                'author': result[2],
                'topic': result[3],
                'tone': result[4],
                'takeaway': result[5],
                'created_at': result[6]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting random quote: {e}")
        return None
    finally:
        if conn:
            conn.close()

def search_quotes(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for quotes containing the given query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching quotes
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute(
            """
            SELECT id, quote, author, topic, tone, takeaway, created_at
            FROM quotes
            WHERE quote LIKE ? OR author LIKE ? OR topic LIKE ?
            LIMIT ?
            """,
            (search_term, search_term, search_term, limit)
        )
        return [
            {
                'id': row[0],
                'quote': row[1],
                'author': row[2],
                'topic': row[3],
                'tone': row[4],
                'takeaway': row[5],
                'created_at': row[6]
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        logger.error(f"Error searching quotes: {e}")
        return []
    finally:
        if conn:
            conn.close()
