import re

import unicodedata

# Kannada Unicode block
KANNADA_PATTERN = re.compile(r"^[\u0C80-\u0CFF]+$")

# blacklist characters (your provided set)
SPECIAL_CHARACTERS = set(
    r"""೧^l=F–೬B#yJwfz•+2umE<'!CxULvr]8o೦VNd0hH'_>)- :sYQ7.g9n%W,G`1…"&?6೯I"೮೨Tb"@೭೫ʼKX4೪[iDScM;*t'{5k/pa(PAeZ~O3R|j}q೩$"""
)


def clean_kannada_word(word: str) -> str:
    """
    Cleans Kannada word by:
    - Unicode normalization
    - removing spaces
    - removing blacklisted characters
    - enforcing Kannada-only characters
    """

    if not word:
        raise ValueError("Empty word not allowed")

    # normalize Unicode
    cleaned = unicodedata.normalize("NFC", word.strip())

    # remove whitespace completely
    cleaned = re.sub(r"\s+", "", cleaned)

    # remove special characters (blacklist pass)
    cleaned = "".join(ch for ch in cleaned if ch not in SPECIAL_CHARACTERS)

    if not cleaned:
        raise ValueError("Word became empty after cleaning")

    # enforce Kannada-only characters
    if not KANNADA_PATTERN.match(cleaned):
        raise ValueError(f"Invalid Kannada word after cleaning: {word}")

    return cleaned
