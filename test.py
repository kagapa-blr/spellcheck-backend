import unicodedata


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


word_list = """
೧. ಪಾಲಿಸಯ್ಯ ಪಾರ್ವತೀಪತಿ
ಪಾಲಿಸಯ್ಯ ಪಾರ್ವತೀಪತಿ 
ತ್ರಿಲೋಕದೋಳ್ ವಿರತಿ	|| ಪ ||

ಗಂಗಾಧರನ ಸ್ತುತಿ 
ಧ್ಯಾನಿಸುವ ಆತ್ಮಾಭಿರತಿ
ಕರುಣಿ ಕೈಲಾಸಕಧಿಪತಿ	|| 1 ||

ಗಿರಿಜಾ ರಮಣನ ಸ್ತು ತಿ
ಭಜಿಸಿ ಶಿವಯೋಗ ಸ್ಥಿತಿ
ಸಿದ್ದ ಶಿ ವ ಯೋಗ ಿ ಸು ಮ ತಿ
ಕಂಡು ಕಂ ಡು ನಾನೆಂತು ಭ ಜಿ ಸಲಿ
ಕಂತುಹರನೆ ಗೌರಿಕಾಂತನೆ	|| 1 ||

ಶಾಂತಮೂರ್ತಿ ನೀ ಎಂಬೆನೆ ನಾನು 
ಭ್ರಾಂತಿಯಿಂದ ತ್ರಿ ಶೂಲವ ಪಿಡಿದೆ 
ಉರಿಗ ಣ್ಣು ಉರಿಹ ಸ್ತ ಹಿರಿಯ ದೇವರೊಳು 
ನಿರುತ ಬೇಡಿ ಕಾಡುತಿಹುದು ಖೋಡಿ ಮನ	|| 2 ||

ವಾ ಹನ ಬೇಡಲು ಮ ತ್ತೇ ನು
ಆದಿ ಅನಾದಿ ಮುದಿ ಎತ್ತು ತಾನು 
ಆವ ಆ ಶೆಯಿರುವದು ಇ ನ್ನು 
ದೇವ ಭವದ ಪಾಶಹರಿ ನೀನು
ಕಾವ ಕರುಣಿ ಶಿಶುನಾಳಧೀಶ 


"""

for word in word_list.split():
    if is_single_kannada_akshara(word):
        print(word, end=",")
