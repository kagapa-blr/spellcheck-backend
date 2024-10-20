from collections import Counter
from typing import List

from docx import Document as DocxDocument
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from routers.bloom_api import filter_missing_words

# This is the string containing all unwanted characters
special_characters = """೧^l=F–೬B#yJwfz•+2umE<'!CxULvr]8o೦VNd0hH‘_>)- :sYQ7.g9n%W,G`1…"&?6೯I”೮೨Tb“@೭೫ʼKX4೪[iDScM;*t\’{5k/pa(PAeZ~O3R|j}q೩$"""

# Create a translation table to remove unwanted characters
translation_table = str.maketrans('', '', special_characters)


async def extract_words_from_txt(file: UploadFile) -> List[str]:
    """
    Extracts words from a .txt file.

    Args:
        file (UploadFile): The uploaded .txt file.

    Returns:
        List[str]: A list of words extracted from the file.
    """
    if file.content_type != 'text/plain':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .txt file.")

    contents = await file.read()
    text = contents.decode('utf-8')
    words = text.split()
    return words


def clean_words(words: List[str]) -> List[str]:
    """
    Cleans the list of words by removing any characters found in the string `p`.

    Args:
        words (List[str]): The list of words extracted from the file.

    Returns:
        List[str]: The cleaned list of words.
    """
    cleaned_words = []
    for word in words:
        # Remove any characters found in the string `p`
        cleaned_word = word.translate(translation_table)
        # Add the cleaned word to the list if it's not empty
        if cleaned_word:
            cleaned_words.append(cleaned_word.strip())  # Optionally convert to lowercase
    return cleaned_words
def clean_single_word(word: str) -> str:
    """
    Cleans a single word by removing unwanted characters.

    Args:
        word (str): The word to be cleaned.

    Returns:
        str: The cleaned word.
    """
    # Remove unwanted characters using the translation table
    cleaned_word = word.translate(translation_table)
    return cleaned_word.strip()  # Optionally convert to lowercase if needed


async def extract_words_from_docx(file: UploadFile) -> List[str]:
    """
    Extracts words from a .docx file.

    Args:
        file (UploadFile): The uploaded .docx file.

    Returns:
        List[str]: A list of words extracted from the file.
    """
    if file.content_type != 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")

    document = DocxDocument(file.file)
    words = []
    for paragraph in document.paragraphs:
        words.extend(paragraph.text.split())
    return words


async def extract_words(file: UploadFile) -> List[str]:
    """
    Extracts words from either a .txt or .docx file.

    Args:
        file (UploadFile): The uploaded file.

    Returns:
        List[str]: A list of words extracted from the file.
    """
    if file.filename.endswith('.txt'):
        return await extract_words_from_txt(file)
    elif file.filename.endswith('.docx'):
        return await extract_words_from_docx(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a .txt or .docx file.")


async def filter_words_from_file(file: UploadFile) -> List[str]:
    """
    Extracts words from the uploaded file and filters out the words already present in the Bloom filter.

    Args:
        file (UploadFile): The uploaded file.
        db (Session): The database session.
        bloom_filter (BloomWordFilter): An instance of the Bloom filter.

    Returns:
        List[str]: A list of words that are not present in the Bloom filter.
    """
    # Extract words based on file type
    words = await extract_words(file)
    words = clean_words(words)

    # Filter missing words using the Bloom filter
    missing_words = filter_missing_words(words=words)

    return missing_words


async def filter_missing_words_from_list(words: List[str]) -> List[str]:
    """
    Filters a list of words to remove those that are already present in a Bloom filter.

    Args:
        words (List[str]): A list of words to be filtered.

    Returns:
        List[str]: A list of words that are not present in the Bloom filter.

    This function takes a list of words as input and uses the `filter_missing_words` function
    to filter out the words that are already present in a Bloom filter. The filtered words are
    then returned as a new list.
    """
    # Filter missing words using the Bloom filter
    missing_words = filter_missing_words(words=words)

    return missing_words


async def count_word_frequency(file: UploadFile) -> dict:
    """
    Counts the frequency of each word in the uploaded .txt or .docx file.

    Args:
        file (UploadFile): The uploaded file.

    Returns:
        dict: A dictionary where keys are words and values are their frequencies.
    """
    # Extract words based on file type
    words = await extract_words(file)
    words = clean_words(words)

    # Count the frequency of each word using Counter
    word_frequency = Counter(words)

    return dict(word_frequency)
