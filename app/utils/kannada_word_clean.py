# import re
#
# import unicodedata
#
# # Kannada Unicode block
# KANNADA_PATTERN = re.compile(r"^[\u0C80-\u0CFF]+$")
#
# # blacklist characters (your provided set)
# SPECIAL_CHARACTERS = set(
#     r"""೧^l=F–೬B#yJwfz•+2umE<'!CxULvr]8o೦VNd0hH'_>)- :sYQ7.g9n%W,G`1…"&?6೯I"೮೨Tb"@೭೫ʼKX4೪[iDScM;*t'{5k/pa(PAeZ~O3R|j}q೩$"""
# )

import re

import unicodedata

# Kannada Unicode block
KANNADA_PATTERN = re.compile(r"[\u0C80-\u0CFF]+")


def clean_kannada_word(word: str) -> str:
    """
    Clean a Kannada word by:
    - Unicode normalization (NFC)
    - Removing whitespace
    - Keeping only Kannada Unicode characters

    Returns:
        Cleaned Kannada word, or "" if no valid Kannada characters remain.
    """

    if not word:
        return ""

    # Normalize Unicode
    cleaned = unicodedata.normalize("NFC", str(word))

    # Remove all whitespace
    cleaned = re.sub(r"\s+", "", cleaned)

    # Keep only Kannada characters
    cleaned = "".join(KANNADA_PATTERN.findall(cleaned))

    return cleaned
