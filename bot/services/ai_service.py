"""AI-powered quote generation service."""
import logging
from openai import AsyncOpenAI
from typing import Optional
import re
from typing import List

logger = logging.getLogger(__name__)

class AIService:
    """Handles AI-powered quote generation."""
    
    def __init__(self, api_key: str = None):
        """Initialize the AI service with an optional API key."""
        self.client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
    
    async def generate_quote(self, user_id: int, preferences: dict = None) -> Optional[str]:
        """Generate a personalized quote using the OpenAI API.
        
        Args:
            user_id: The ID of the user requesting the quote
            preferences: Dictionary of user preferences
            
        Returns:
            Optional[str]: The generated quote or None if generation failed
        """
        prompt = self._build_prompt(preferences or {})
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative and insightful quote generator. You only output the quote and its attribution, nothing else."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=70,
                temperature=0.9,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed for user {user_id}: {e}")
            return None
    
    async def deep_dive_by_author(
        self, author: str, count: int = 5
    ) -> list[str]:
        """
        Ask the model to return `count` real, attributed quotes by `author`.
        Returns a list of lines like: '"…quote…" - Author Name'
        """
        system = (
            "You are a helpful assistant that returns EXACTLY N distinct verified quotations "
            "by the requested public figure.  "
            "Output each on its own line with the format:\n"
            "\"<quote>\" - <Full Author Name>"
        )
        user = (
            f"Please give me {count} well‐known quotes by {author}, each on its own line "
            "in the format exactly as described above."
        )

        try:
            resp = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",  "content": system},
                    {"role": "user",    "content": user},
                ],
                max_tokens=200,
                temperature=0.7,
            )
            text = resp.choices[0].message.content.strip()
            # split on lines and filter out any empties:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return lines[:count]
        except Exception as e:
            logger.error(f"deep_dive_by_author failed for {author}: {e}")
            return []
    
    async def generate_by_topic(self, topic: str, count: int = 3) -> list[str]:

        """
        Ask the model for `count` real, verifiable quotations on the given topic.
        Returns a list of lines like '"…quote…" - Full Author Name'.
        """

        system = (
            "You are an expert curator of real quotations.  "
            "Output exactly N distinct quotes, each on its own line in the format:\n"
            "\"<quote>\" - <Full Author Name>"
        )

        user = (
            f"Please give me {count} well-known, verifiable quotes about “{topic}”, "
            "each on its own line in the format exactly as described above."
        )

        try:
            resp = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",  "content": system},
                    {"role": "user",    "content": user},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            text = resp.choices[0].message.content.strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return lines[:count]
        except Exception as e:
            logger.error(f"generate_by_topic failed for '{topic}': {e}")
            return []
    
    def _build_prompt(self, prefs: dict) -> str:
        """Build a prompt for the AI based on user preferences, instructing it to include a one-line takeaway."""
        if not prefs:
            return (
                "Generate exactly three lines:\n"
                "1) A short, insightful quote in straight double quotes.\n"
                "2) A hyphen, space, then the full author name.\n"
                "3) A one-sentence takeaway prefaced with Takeaway: \n"
                "If you cannot find a suitable real quote, reply exactly RETRY."
            )

        # Gather topics, tone, and length preferences
        user_topics = [prefs.get(f'topic{i}') for i in range(1, 4) if prefs.get(f'topic{i}')]
        topics_str = ", ".join(user_topics) if user_topics else "general wisdom"
        tone = prefs.get('tone', 'inspirational')
        length_pref = prefs.get('quote_length', 'any length')

        return (
            f"You are Quotemaster, a curator of real, verifiable quotations.\n\n"
            f"Requirements:\n"
            f"- Theme: {topics_str}\n"
            f"- Tone: {tone}\n"
            f"- Length: {length_pref} (very short ≤8 words, short 9–15, medium 16–30, long 31–50).\n"
            f"- Source: speeches, books, interviews, essays only.\n\n"
            "Produce exactly three lines:\n"
            "1) The quote in straight double quotes\n"
            "2) A hyphen and the author’s full name (e.g. - Maya Angelou)\n"
            "3) Takeaway: <one-sentence explanation>\n\n"
        )

# Global instance for convenience
ai_service = AIService()
