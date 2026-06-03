"""
long_term_memory.py — Level 2: Persistent memory across sessions using MongoDB.

Each user gets their own memory document in MongoDB.
Memory survives server restarts and new sessions.

MongoDB structure:
    collection: user_memories
    document: {
        "_id": "user_id",
        "facts": [
            {
                "fact": "User's name is Vinn",
                "category": "personal",
                "timestamp": "2026-05-16T..."
            }
        ]
    }
"""

from datetime import datetime
from auth.models import get_db

MAX_FACTS = 100


class LongTermMemory:
    """
    Stores and retrieves persistent facts about a specific user.
    Each user has their own isolated memory document in MongoDB.
    """

    def __init__(self, user_id: str):
        self.user_id    = user_id
        self.collection = get_db()["user_memories"]
        self._ensure_document()

    # ── Public API ─────────────────────────────────────────────────────────────

    def remember(self, fact: str, category: str = "general"):
        """Store a new fact about the user."""
        existing = self._get_facts()
        existing_texts = [f["fact"].lower() for f in existing]

        if fact.lower() in existing_texts:
            return  # avoid duplicates

        new_fact = {
            "fact":      fact,
            "category":  category,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.collection.update_one(
            {"_id": self.user_id},
            {"$push": {"facts": new_fact}},
        )

        # Trim if too many facts
        all_facts = self._get_facts()
        if len(all_facts) > MAX_FACTS:
            self.collection.update_one(
                {"_id": self.user_id},
                {"$set": {"facts": all_facts[-MAX_FACTS:]}},
            )

        print(f"[Memory:{self.user_id[:8]}] Remembered: {fact}")

    def recall(self, category: str = None) -> list[str]:
        """Retrieve stored facts, optionally filtered by category."""
        facts = self._get_facts()
        if category:
            return [f["fact"] for f in facts if f.get("category") == category]
        return [f["fact"] for f in facts]

    def get_context_summary(self) -> str:
        """
        Returns a formatted summary of everything remembered about this user.
        Injected into system prompts for personalized responses.
        """
        facts = self._get_facts()
        if not facts:
            return ""

        lines = ["--- What I know about you ---"]
        for fact in facts[-20:]:
            lines.append(f"• {fact['fact']}")
        lines.append("-----------------------------")
        return "\n".join(lines)

    def forget(self, fact: str):
        """Remove a specific fact from this user's memory."""
        self.collection.update_one(
            {"_id": self.user_id},
            {"$pull": {"facts": {"fact": {"$regex": fact, "$options": "i"}}}},
        )

    def forget_all(self):
        """Clear all memory for this user."""
        self.collection.update_one(
            {"_id": self.user_id},
            {"$set": {"facts": []}},
        )
        print(f"[Memory:{self.user_id[:8]}] All memory cleared")

    def extract_and_remember(self, user_message: str, assistant_response: str):
        """
        Automatically extract memorable facts from the conversation.
        Called after every exchange.
        """
        msg = user_message.lower()

        # Name detection
        for phrase in ["my name is", "i am called", "call me"]:
            if phrase in msg:
                name = msg.split(phrase)[-1].strip().split()[0].capitalize()
                if len(name) > 1:
                    self.remember(f"User's name is {name}", "personal")

        # Profession detection
        for phrase in ["i am a", "i'm a", "i work as"]:
            if phrase in msg:
                rest = msg.split(phrase)[-1].strip()
                profession = rest.split(".")[0].split(",")[0][:60]
                self.remember(f"User is a {profession}", "profession")
                break

        # Location detection
        for phrase in ["i live in", "i am in", "i am from", "i'm from"]:
            if phrase in msg:
                rest = msg.split(phrase)[-1].strip()
                location = rest.split(".")[0].split(",")[0][:60]
                self.remember(f"User is located in {location}", "location")
                break

        # Interest detection
        for phrase in ["i love", "i enjoy", "i like", "i'm interested in",
                       "i am interested in", "i want to learn", "i'm learning"]:
            if phrase in msg:
                rest = msg.split(phrase)[-1].strip()
                interest = rest.split(".")[0].split(",")[0][:60]
                self.remember(f"User is interested in {interest}", "interest")
                break

        # Preference detection
        for phrase in ["i prefer", "i like it when"]:
            if phrase in msg:
                rest = msg.split(phrase)[-1].strip()
                preference = rest.split(".")[0][:80]
                self.remember(f"User prefers {preference}", "preference")
                break

    # ── Private helpers ────────────────────────────────────────────────────────

    def _ensure_document(self):
        """Create memory document for this user if it doesn't exist."""
        self.collection.update_one(
            {"_id": self.user_id},
            {"$setOnInsert": {"_id": self.user_id, "facts": []}},
            upsert=True,
        )

    def _get_facts(self) -> list[dict]:
        """Get all facts for this user from MongoDB."""
        doc = self.collection.find_one({"_id": self.user_id})
        return doc.get("facts", []) if doc else []


# ── Factory function ───────────────────────────────────────────────────────────

def get_user_memory(user_id: str) -> LongTermMemory:
    """
    Get a LongTermMemory instance for a specific user.
    Each user gets their own isolated memory.
    """
    return LongTermMemory(user_id)