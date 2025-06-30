"""Quote management service for the Quote Bot."""
import csv
import logging
import random
from pathlib import Path
from typing import List, Dict, Optional, Any
import datetime as dt
import zoneinfo    

logger = logging.getLogger(__name__)

class QuoteService:
    """Handles quote loading and selection."""
    
    def __init__(self, quotes_file: str = 'quotes.csv'):
        """Initialize the quote service.
        
        Args:
            quotes_file: Path to the CSV file containing quotes
        """
        self.quotes_file = quotes_file
        self.quotes: List[Dict[str, Any]] = []
        self.load_quotes()
    
    def should_send_today(prefs: dict) -> bool:
        """
        Return True iff we should deliver a quote *today* for this user.
        Weekend behaviour obeys prefs['weekend_toggle'].
        """
        tz = zoneinfo.ZoneInfo(prefs.get("timezone") or "UTC")
        today = dt.datetime.now(tz).weekday()          # 0=Mon … 6=Sun
        if not prefs.get("weekend_toggle", 1) and today >= 5:
            return False
        return True
    
    def load_quotes(self) -> None:
        """Load quotes from the CSV file."""
        try:
            with open(self.quotes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.quotes = []
                for idx, row in enumerate(reader, 1):
                    # Ensure each quote has an ID
                    if 'id' not in row or not row['id']:
                        row['id'] = str(idx)
                    try:
                        row['id'] = int(row['id'])
                    except (ValueError, TypeError):
                        row['id'] = idx  # Fallback to line number if ID is not a number
                    self.quotes.append(row)
                    
            logger.info(f"Loaded {len(self.quotes)} quotes from {self.quotes_file}")
        except FileNotFoundError:
            logger.error(f"Quotes file not found: {self.quotes_file}")
            self.quotes = []
    
    def get_quote_for_user(self, user_id: int, prefs: Optional[Dict] = None) -> Optional[Dict]:
        """Get a personalized quote for a user based on their preferences.
        
        Args:
            user_id: The ID of the user
            prefs: User preferences (optional)
            
        Returns:
            Optional[Dict]: A quote or None if no quotes are available
        """
        if not self.quotes:
            return None
            
        if not prefs:
            return random.choice(self.quotes)
        
        # Get disliked quote IDs to exclude
        from quote_bot.db import get_disliked_quote_ids
        disliked_quotes = get_disliked_quote_ids(user_id)
        
        # Filter quotes by topics if specified
        topics = [prefs.get(f'topic{i}') for i in range(1, 4) if prefs.get(f'topic{i}')]
        topics = [t.lower() for t in topics if t]
        
        candidate_quotes = []
        for quote in self.quotes:
            # Skip disliked quotes
            if quote['id'] in disliked_quotes:
                continue
                
            # Filter by topic if specified
            if topics and not any(topic in quote.get('quote', '').lower() for topic in topics):
                continue
                
            candidate_quotes.append(quote)
        
        # If no quotes match topics, use all non-disliked quotes
        if not candidate_quotes:
            candidate_quotes = [q for q in self.quotes if q['id'] not in disliked_quotes]
        
        # If still no quotes, use all quotes (including disliked ones as last resort)
        if not candidate_quotes:
            candidate_quotes = self.quotes
        
        # Filter by author preference if specified
        if prefs.get('author_pref') and prefs['author_pref'].lower() != 'any':
            author_quotes = [
                q for q in candidate_quotes 
                if q.get('author', '').lower() == prefs['author_pref'].lower()
            ]
            if author_quotes:
                candidate_quotes = author_quotes
        
        # Filter by quote length if specified
        if prefs.get('quote_length') and prefs['quote_length'].lower() != 'any length':
            length_filtered = []
            for q in candidate_quotes:
                word_count = len(q.get('quote', '').split())
                if prefs['quote_length'] == 'short (< 10 words)' and word_count < 10:
                    length_filtered.append(q)
                elif prefs['quote_length'] == 'medium (10-15 words)' and 10 <= word_count <= 15:
                    length_filtered.append(q)
                elif prefs['quote_length'] == 'long >20 words' and word_count > 20:
                    length_filtered.append(q)
            
            if length_filtered:  # Only apply if we found matches
                candidate_quotes = length_filtered
        
        return random.choice(candidate_quotes) if candidate_quotes else None

# Global instance for convenience
quote_service = QuoteService()
