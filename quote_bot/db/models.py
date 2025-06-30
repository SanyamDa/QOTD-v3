"""Database models for the Quote Bot application."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class User:
    """User model representing a bot user."""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_paused: bool = False
    created_at: Optional[datetime] = None

@dataclass
class UserPreferences:
    """User preferences model."""
    user_id: int
    topics: List[str] = None
    tone: Optional[str] = None
    quote_length: Optional[str] = None
    author_pref: Optional[str] = None
    delivery_time: str = "07:00"  # Default to 7:00 AM
    weekend_toggle: bool = True
    context_line: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary format."""
        return {
            'topics': self.topics if self.topics else [],
            'tone': self.tone,
            'quote_length': self.quote_length,
            'author_pref': self.author_pref,
            'delivery_time': self.delivery_time,
            'weekend_toggle': self.weekend_toggle,
            'context_line': self.context_line
        }

    @classmethod
    def from_dict(cls, user_id: int, data: Dict[str, Any]) -> 'UserPreferences':
        """Create UserPreferences from a dictionary."""
        return cls(
            user_id=user_id,
            topics=data.get('topics', []),
            tone=data.get('tone'),
            quote_length=data.get('quote_length'),
            author_pref=data.get('author_pref'),
            delivery_time=data.get('delivery_time', '07:00'),
            weekend_toggle=bool(data.get('weekend_toggle', True)),
            context_line=bool(data.get('context_line', False))
        )

@dataclass
class QuoteInteraction:
    """Quote interaction model for tracking user interactions with quotes."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    quote_id: Optional[int] = None
    is_liked: bool = False
    is_disliked: bool = False
    is_favorited: bool = False
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary format."""
        return {
            'is_liked': self.is_liked,
            'is_disliked': self.is_disliked,
            'is_favorited': self.is_favorited
        }
