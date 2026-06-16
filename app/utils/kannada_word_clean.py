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
    - Rejecting digits
    - Keeping only Kannada characters
    - Rejecting invalid starting dependent signs
    - Rejecting single akshara words

    Returns:
        Cleaned Kannada word, or "" if invalid.
    """

    if not word:
        return ""

    cleaned = unicodedata.normalize("NFC", str(word))

    # Remove whitespace
    cleaned = re.sub(r"\s+", "", cleaned)

    # Reject digits
    if DIGIT_PATTERN.search(cleaned):
        return ""

    # Keep only Kannada characters
    cleaned = "".join(KANNADA_PATTERN.findall(cleaned))

    if not cleaned:
        return ""

    # Reject invalid starting characters
    if starts_with_invalid_kannada_sign(cleaned):
        return ""

    # Reject single akshara
    if is_single_kannada_akshara(cleaned):
        return ""

    return cleaned


def starts_with_invalid_kannada_sign(text: str) -> bool:
    """
    Reject words starting with:
    - Anusvara (ಂ)
    - Visarga (ಃ)
    - Vowel signs (ಾಿೀುೂೃೆೇೈೊೋೌ)
    - Virama (್)

    Examples:
        ಂಬದೇ -> True
        ್ಕ -> True
        ಕನ್ನಡ -> False
    """

    if not text:
        return True

    first = text[0]

    invalid_start_chars = {
        "\u0C82",  # ಂ anusvara
        "\u0C83",  # ಃ visarga
        "\u0CCD",  # ್ virama
    }

    # Kannada vowel signs range
    if first in invalid_start_chars:
        return True

    if "\u0CBE" <= first <= "\u0CCC":
        return True

    return False


def is_single_kannada_akshara(text: str) -> bool:
    """
    Returns True if text contains exactly one Kannada akshara.
    """

    if not text:
        return False

    text = unicodedata.normalize("NFC", text.strip())

    if any(not ("\u0C80" <= ch <= "\u0CFF") for ch in text):
        return False

    akshara_count = 0
    previous_was_virama = False

    for ch in text:

        category = unicodedata.category(ch)

        if category == "Lo":

            if not previous_was_virama:
                akshara_count += 1

            previous_was_virama = False

        elif ch == "\u0CCD":
            previous_was_virama = True

        elif category in ("Mc", "Mn"):
            continue

        else:
            return False

    return akshara_count == 1
