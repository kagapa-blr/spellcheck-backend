from sqlalchemy.future import select
from sqlalchemy.orm import Session
from symspellpy import SymSpell

from database import get_db
from models import MainDictionary

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)


# Load words into SymSpell from the main dictionary
def symspell_initialization():
    """Initialize SymSpell by loading words and frequencies from the database."""
    db: Session = next(get_db())
    result = db.execute(
        select(MainDictionary.word, MainDictionary.frequency)).all()  # Fetch all words and their frequencies
    # Load words into SymSpell
    for word, frequency in result:
        sym_spell.create_dictionary_entry(word, frequency)  # Add each word with its frequency to SymSpell
    print("SymSpell loaded with words and frequencies from MainDictionary.")
