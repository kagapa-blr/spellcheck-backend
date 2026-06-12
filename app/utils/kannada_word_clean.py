import re

import unicodedata

# Kannada Unicode block
KANNADA_PATTERN = re.compile(r"[\u0C80-\u0CFF]+")

# English digits + Kannada digits
DIGIT_PATTERN = re.compile(r"[0-9\u0CE6-\u0CEF]")


def clean_kannada_word(word: str) -> str:
    """
    Clean a Kannada word by:
    - Unicode normalization (NFC)
    - Removing whitespace
    - Rejecting entire word if it contains any digit
      (English 0-9 or Kannada ೦-೯)
    - Keeping only Kannada Unicode characters

    Returns:
        Cleaned Kannada word, or "" if invalid.
    """

    if not word:
        return ""

    # Normalize Unicode
    cleaned = unicodedata.normalize("NFC", str(word))

    # Remove whitespace
    cleaned = re.sub(r"\s+", "", cleaned)

    # Reject entire word if any digit exists
    if DIGIT_PATTERN.search(cleaned):
        return ""

    # Keep only Kannada characters
    cleaned = "".join(KANNADA_PATTERN.findall(cleaned))

    return cleaned
