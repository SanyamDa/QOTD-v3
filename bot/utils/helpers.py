"""Helper functions for the Quote Bot."""
import re

def escape_markdown(text: str) -> str:
    """Escape special HTML characters for Telegram's HTML parse mode.
    
    This function escapes special characters to be safe for HTML display.
    
    Args:
        text: The text to escape
        
    Returns:
        str: Escaped text safe for HTML display
    """
    if not text:
        return ""
    
    # Convert to string in case it's not
    text = str(text)
    
    # Escape HTML special characters
    text = (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )
    
    return text

def format_quote(quote: str, author: str = None) -> str:
    """Format a quote with its author in a nice way."""
    if not quote:
        return ""
        
    formatted = f'<i>"{escape_markdown(quote)}"</i>'
    if author and author.strip():
        formatted += f'\n  — <b>{escape_markdown(author.strip())}</b>'
    
    return formatted



