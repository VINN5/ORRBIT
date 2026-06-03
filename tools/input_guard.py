"""
input_guard.py — Validates and sanitizes user input before it reaches the agent.

Catches:
- Empty / whitespace-only messages
- Messages that are too short or too long
- Gibberish / random character input
- Prompt injection attempts
- Offensive or harmful content patterns
- Repeated spam messages
- Special character abuse
"""

import re
import unicodedata
from dataclasses import dataclass


# ── Config ────────────────────────────────────────────────────────────────────

MIN_LENGTH       = 2        # minimum characters
MAX_LENGTH       = 4000     # maximum characters
MAX_WORD_LENGTH  = 50       # flag words longer than this (gibberish)
MIN_WORD_RATIO   = 0.4      # at least 40% of tokens must look like real words
MAX_REPEATS      = 3        # max times same message allowed in a session


# ── Prompt injection patterns ─────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+(a\s+)?(?!an?\s+expert)",   # "you are now DAN"
    r"act\s+as\s+if\s+you\s+(have\s+no|don.t\s+have)",
    r"pretend\s+(you\s+are|to\s+be)\s+(?!an?\s+expert)",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"override\s+(your\s+)?(safety|guidelines|restrictions)",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"ignore\s+(your\s+)?(safety|guidelines|restrictions)",
]

# ── Harmful content patterns ───────────────────────────────────────────────────

HARMFUL_PATTERNS = [
    r"\b(how\s+to\s+)?(make|build|create|synthesize)\s+(a\s+)?(bomb|weapon|poison|drug)",
    r"\b(hack|crack|exploit)\s+(into\s+)?(a\s+)?(system|server|account|password)",
    r"(suicide|self.harm)\s+(method|instruction|guide|how)",
]


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    valid: bool
    cleaned: str
    error: str = ""
    warning: str = ""


# ── Main guard ────────────────────────────────────────────────────────────────

class InputGuard:
    def __init__(self):
        self._recent_messages: list[str] = []   # tracks last N messages per session

    def validate(self, raw_input: str) -> ValidationResult:
        """Run all checks on the raw input. Returns cleaned text or an error."""

        # Step 1 — Basic sanitization
        text = self._sanitize(raw_input)

        # Step 2 — Length checks
        if len(text) < MIN_LENGTH:
            return ValidationResult(
                valid=False,
                cleaned=text,
                error="Message is too short. Please type a proper question.",
            )

        if len(text) > MAX_LENGTH:
            return ValidationResult(
                valid=False,
                cleaned=text,
                error=f"Message is too long ({len(text)} chars). "
                      f"Please keep it under {MAX_LENGTH} characters.",
            )

        # Step 3 — Gibberish check
        if self._is_gibberish(text):
            return ValidationResult(
                valid=False,
                cleaned=text,
                error="I couldn't understand that. Could you rephrase your question?",
            )

        # Step 4 — Prompt injection check
        injection = self._check_injection(text)
        if injection:
            return ValidationResult(
                valid=False,
                cleaned=text,
                error="That type of request isn't supported. "
                      "Please ask a normal question.",
            )

        # Step 5 — Harmful content check
        harmful = self._check_harmful(text)
        if harmful:
            return ValidationResult(
                valid=False,
                cleaned=text,
                error="I can't help with that request.",
            )

        # Step 6 — Spam / repeat check
        if self._is_spam(text):
            return ValidationResult(
                valid=False,
                cleaned=text,
                error="You've sent the same message several times. "
                      "Try rephrasing or ask something different.",
            )

        # Step 7 — Track message
        self._recent_messages.append(text.lower())
        if len(self._recent_messages) > 20:
            self._recent_messages.pop(0)

        # All checks passed
        warning = ""
        if len(text) > MAX_LENGTH * 0.8:
            warning = "Your message is quite long — consider splitting into smaller questions."

        return ValidationResult(valid=True, cleaned=text, warning=warning)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _sanitize(self, text: str) -> str:
        """Strip leading/trailing whitespace and normalize unicode."""
        text = text.strip()
        # Normalize unicode (e.g. fancy quotes → standard)
        text = unicodedata.normalize("NFKC", text)
        # Collapse multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple spaces
        text = re.sub(r" {3,}", " ", text)
        return text

    def _is_gibberish(self, text: str) -> bool:
        """Detect random character strings with no real words."""
        words = text.split()
        if not words:
            return True

        # If very short, skip gibberish check
        if len(words) <= 2:
            return False

        # Check ratio of very long "words" (likely keyboard mashing)
        long_words = [w for w in words if len(w) > MAX_WORD_LENGTH]
        if len(long_words) / len(words) > 0.5:
            return True

        # Check consonant-only ratio (gibberish has no vowels)
        vowels = set("aeiouAEIOU")
        total_alpha = sum(c.isalpha() for c in text)
        if total_alpha == 0:
            return False  # might be all numbers/symbols, not gibberish
        vowel_count = sum(c in vowels for c in text)
        vowel_ratio = vowel_count / total_alpha
        if vowel_ratio < 0.05 and len(text) > 20:
            return True

        # Check for excessive repeated characters (aaaaaaa, zzzzz)
        if re.search(r"(.)\1{6,}", text):
            return True

        return False

    def _check_injection(self, text: str) -> bool:
        """Detect prompt injection attempts."""
        lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    def _check_harmful(self, text: str) -> bool:
        """Detect harmful content requests."""
        lower = text.lower()
        for pattern in HARMFUL_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    def _is_spam(self, text: str) -> bool:
        """Detect repeated identical messages."""
        lower = text.lower().strip()
        repeat_count = self._recent_messages.count(lower)
        return repeat_count >= MAX_REPEATS


# ── Singleton for use across the app ──────────────────────────────────────────
guard = InputGuard()


def validate_input(raw: str) -> ValidationResult:
    """Main entry point — call this before passing input to the agent."""
    return guard.validate(raw)
