"""
user_profile.py — Level 3: Personality & adaptation for Orrbit.

Tracks how each user communicates and adapts Orrbit's responses accordingly.

Tracks:
- Communication style (formal/casual/technical)
- Preferred response length (short/medium/detailed)
- Favorite domains (what they ask about most)
- Expertise level per domain (beginner/intermediate/expert)
- Language preference
- Interaction patterns

Stored in MongoDB under user_profiles collection.
Each user gets their own isolated profile.
"""

from datetime import datetime
from auth.models import get_db


# ── Default profile template ───────────────────────────────────────────────────

DEFAULT_PROFILE = {
    "communication_style": "balanced",   # formal | casual | technical | balanced
    "response_length":     "medium",      # short | medium | detailed
    "language":            "english",     # detected from messages
    "expertise": {
        "computing":     "unknown",
        "finance":       "unknown",
        "health":        "unknown",
        "legal":         "unknown",
        "mental_health": "unknown",
        "business":      "unknown",
        "history":       "unknown",
        "astronomy":     "unknown",
        "sports":        "unknown",
        "technology":    "unknown",
        "general":       "unknown",
    },
    "domain_counts": {
        "computing":     0,
        "finance":       0,
        "health":        0,
        "legal":         0,
        "mental_health": 0,
        "business":      0,
        "history":       0,
        "astronomy":     0,
        "sports":        0,
        "technology":    0,
        "general":       0,
    },
    "total_conversations": 0,
    "created_at":          None,
    "updated_at":          None,
}


class UserProfile:
    """
    Manages a user's communication profile and adapts Orrbit's behavior.
    """

    def __init__(self, user_id: str):
        self.user_id    = user_id
        self.collection = get_db()["user_profiles"]
        self._ensure_profile()

    # ── Public API ─────────────────────────────────────────────────────────────

    def update_from_message(self, message: str, domain: str):
        """
        Analyze a user message and update their profile accordingly.
        Called after every user message.
        """
        updates = {}

        # Detect communication style
        style = self._detect_style(message)
        if style:
            updates["communication_style"] = style

        # Detect preferred response length
        length = self._detect_length_preference(message)
        if length:
            updates["response_length"] = length

        # Detect expertise level
        expertise = self._detect_expertise(message, domain)
        if expertise:
            updates[f"expertise.{domain}"] = expertise

        # Increment domain count
        updates[f"domain_counts.{domain}"] = self._get_domain_count(domain) + 1
        updates["total_conversations"] = self._get_total() + 1
        updates["updated_at"] = datetime.utcnow().isoformat()

        if updates:
            self.collection.update_one(
                {"_id": self.user_id},
                {"$set": updates},
            )

    def get_system_prompt_addon(self) -> str:
        """
        Returns personalization instructions to append to system prompts.
        This is what makes Orrbit adapt its tone and style per user.
        """
        profile = self._get_profile()
        if not profile:
            return ""

        style      = profile.get("communication_style", "balanced")
        length     = profile.get("response_length", "medium")
        total      = profile.get("total_conversations", 0)
        top_domain = self._get_top_domain(profile)

        lines = ["\n--- Personalization Instructions ---"]

        # Style adaptation
        if style == "casual":
            lines.append("- Use a friendly, conversational tone. Use contractions freely.")
        elif style == "formal":
            lines.append("- Use a professional, formal tone. Avoid slang.")
        elif style == "technical":
            lines.append("- Use precise technical language. Include details and specs.")
        else:
            lines.append("- Use a balanced, clear tone suitable for general audiences.")

        # Length adaptation
        if length == "short":
            lines.append("- Keep responses concise and to the point. Avoid long explanations.")
        elif length == "detailed":
            lines.append("- Provide thorough, detailed responses with examples.")
        else:
            lines.append("- Provide moderately detailed responses with key points.")

        # Expertise adaptation
        if top_domain:
            domain_expertise = profile.get("expertise", {}).get(top_domain, "unknown")
            if domain_expertise == "expert":
                lines.append(f"- User is an expert in {top_domain}. Skip basics, go deep.")
            elif domain_expertise == "beginner":
                lines.append(f"- User is a beginner in {top_domain}. Use simple language.")

        # Returning user recognition
        if total > 10:
            lines.append(f"- This is a returning user with {total} conversations. Be warm and familiar.")

        lines.append("------------------------------------")
        return "\n".join(lines)

    def get_favorite_domain(self) -> str:
        """Returns the domain the user asks about most."""
        profile = self._get_profile()
        return self._get_top_domain(profile) or "general"

    def set_language(self, language: str):
        """Update the user's preferred language."""
        self.collection.update_one(
            {"_id": self.user_id},
            {"$set": {"language": language}},
        )

    def reset(self):
        """Reset profile to defaults."""
        profile = DEFAULT_PROFILE.copy()
        profile["created_at"] = datetime.utcnow().isoformat()
        profile["updated_at"] = datetime.utcnow().isoformat()
        self.collection.update_one(
            {"_id": self.user_id},
            {"$set": profile},
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _detect_style(self, message: str) -> str | None:
        """Detect communication style from message content."""
        msg = message.lower()

        casual_indicators  = ["hey", "hi", "lol", "btw", "gonna", "wanna",
                               "cool", "awesome", "thanks", "thx", "pls"]
        formal_indicators  = ["please", "kindly", "could you", "would you",
                               "i would like", "furthermore", "however"]
        technical_indicators = ["algorithm", "function", "api", "database",
                                 "implementation", "architecture", "syntax",
                                 "compile", "debug", "framework"]

        casual_score   = sum(1 for w in casual_indicators   if w in msg)
        formal_score   = sum(1 for w in formal_indicators   if w in msg)
        technical_score = sum(1 for w in technical_indicators if w in msg)

        max_score = max(casual_score, formal_score, technical_score)
        if max_score == 0:
            return None

        if technical_score == max_score:
            return "technical"
        if formal_score == max_score:
            return "formal"
        if casual_score == max_score:
            return "casual"
        return None

    def _detect_length_preference(self, message: str) -> str | None:
        """Detect preferred response length from message."""
        msg = message.lower()

        if any(phrase in msg for phrase in [
            "brief", "short", "quick", "summarize", "in a nutshell",
            "just tell me", "simple answer", "tldr"
        ]):
            return "short"

        if any(phrase in msg for phrase in [
            "detailed", "in depth", "explain everything", "thorough",
            "comprehensive", "elaborate", "step by step", "full explanation"
        ]):
            return "detailed"

        return None

    def _detect_expertise(self, message: str, domain: str) -> str | None:
        """Detect expertise level from message content."""
        msg = message.lower()

        expert_indicators = [
            "what is the difference between", "optimize", "best practice",
            "trade-off", "complexity", "performance", "advanced", "deep dive"
        ]
        beginner_indicators = [
            "what is", "what are", "how do i", "i don't understand",
            "explain", "for beginners", "simple", "basics", "introduction"
        ]

        expert_score   = sum(1 for w in expert_indicators   if w in msg)
        beginner_score = sum(1 for w in beginner_indicators if w in msg)

        if expert_score > beginner_score:
            return "expert"
        if beginner_score > expert_score:
            return "beginner"
        return "intermediate"

    def _get_top_domain(self, profile: dict) -> str | None:
        """Get the domain the user asks about most."""
        counts = profile.get("domain_counts", {})
        if not counts:
            return None
        max_domain = max(counts, key=counts.get)
        return max_domain if counts[max_domain] > 0 else None

    def _get_domain_count(self, domain: str) -> int:
        """Get current count for a domain."""
        profile = self._get_profile()
        return profile.get("domain_counts", {}).get(domain, 0)

    def _get_total(self) -> int:
        """Get total conversation count."""
        profile = self._get_profile()
        return profile.get("total_conversations", 0)

    def _get_profile(self) -> dict:
        """Get raw profile from MongoDB."""
        return self.collection.find_one({"_id": self.user_id}) or {}

    def _ensure_profile(self):
        """Create profile document if it doesn't exist."""
        profile = DEFAULT_PROFILE.copy()
        profile["created_at"] = datetime.utcnow().isoformat()
        profile["updated_at"] = datetime.utcnow().isoformat()

        self.collection.update_one(
            {"_id": self.user_id},
            {"$setOnInsert": {"_id": self.user_id, **profile}},
            upsert=True,
        )


# ── Factory function ───────────────────────────────────────────────────────────

def get_user_profile(user_id: str) -> UserProfile:
    """
    Get a UserProfile instance for a specific user.
    Each user gets their own isolated profile.
    """
    return UserProfile(user_id)