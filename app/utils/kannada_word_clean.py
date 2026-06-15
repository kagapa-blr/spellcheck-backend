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

    if is_single_kannada_akshara(cleaned):
        return ""

    return cleaned


def is_single_kannada_akshara(text: str) -> bool:
    """
    Returns True if text contains exactly one Kannada akshara.

    Examples:
        ಕ       -> True
        ಕಾ      -> True
        ಸ್ತ     -> True
        ಕನ್ನಡ   -> False
        ಮನೆ     -> False
    """

    if not text:
        return False

    text = unicodedata.normalize("NFC", text.strip())

    # Check all chars are Kannada
    if any(not ("\u0C80" <= ch <= "\u0CFF") for ch in text):
        return False

    akshara_count = 0
    previous_was_virama = False

    for ch in text:

        category = unicodedata.category(ch)

        # Kannada consonant/vowel letters
        if category == "Lo":
            if not previous_was_virama:
                akshara_count += 1

            previous_was_virama = False

        # Halant (್) joins next consonant
        elif ch == "\u0CCD":
            previous_was_virama = True

        # Vowel signs, anusvara, visarga, etc. are part of same akshara
        elif category in ("Mc", "Mn"):
            continue

        else:
            return False

    return akshara_count == 1
