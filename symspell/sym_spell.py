from __future__ import annotations

from sqlalchemy.future import select
from sqlalchemy.orm import Session
from symspellpy import SymSpell

from config.database import get_db
from dbmodels.models import MainDictionary
from config.logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)


# Load words into SymSpell from the main dictionary
def symspell_initialization():
    """Initialize SymSpell by loading words and frequencies from the database."""
    global sym_spell
    
    try:
        logger.info("Starting SymSpell initialization...")
        db: Session = next(get_db())
        try:
            result = db.execute(
                select(MainDictionary.word, MainDictionary.frequency)).all()  # Fetch all words and their frequencies
            
            logger.info(f"Database query returned {len(result)} word entries")
            
            # Load words into SymSpell
            loaded_count = 0
            for word, frequency in result:
                sym_spell.create_dictionary_entry(word, frequency)  # Add each word with its frequency to SymSpell
                loaded_count += 1
            
            logger.info(f"SymSpell loaded {loaded_count} words into dictionary")
            logger.info(f"SymSpell internal word_count: {sym_spell.word_count}")
            logger.info(f"SymSpell has _deletes: {hasattr(sym_spell, '_deletes')}")
            
            if sym_spell.word_count == 0:
                logger.error("WARNING: SymSpell word_count is 0 after initialization!")
            else:
                logger.info(f"SymSpell initialized successfully with {sym_spell.word_count} words")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during SymSpell initialization: {str(e)}", exc_info=True)
        raise


def symspell_reinitialization():
    """Reinitialize SymSpell by creating a new instance and reloading words."""
    global sym_spell
    
    try:
        logger.info("Starting SymSpell reinitialization...")
        
        # Create a fresh SymSpell instance
        old_count = sym_spell.word_count
        sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        logger.info(f"Created new SymSpell instance (old count was {old_count}, new count is {sym_spell.word_count})")
        
        # Load words again
        symspell_initialization()
        logger.info(f"SymSpell reinitialization complete. Final word count: {sym_spell.word_count}")
    except Exception as e:
        logger.error(f"Error during SymSpell reinitialization: {str(e)}", exc_info=True)
        raise


def get_symspell_word_count() -> int:
    """Get the current number of words loaded in SymSpell (from SymSpell's internal count)."""
    try:
        # Get the current SymSpell instance (always gets latest after reload)
        current_sym_spell = get_sym_spell()
        actual_count = current_sym_spell.word_count
        logger.info(f"SymSpell actual word count (from SymSpell instance): {actual_count}")
        
        # Also check database for discrepancy detection
        try:
            db: Session = next(get_db())
            try:
                db_count = db.query(MainDictionary).count()
                if actual_count != db_count:
                    logger.warning(f"Discrepancy: SymSpell has {actual_count} words but database has {db_count}")
            finally:
                db.close()
        except Exception as db_err:
            logger.warning(f"Could not verify database count: {str(db_err)}")
        
        return actual_count
    except Exception as e:
        logger.error(f"Error getting SymSpell word count: {str(e)}")
        return 0


def get_sym_spell():
    """Get the current SymSpell instance (always returns the latest global instance).
    
    This function is needed because importing sym_spell directly at module load time
    caches a reference to the old instance. When reinitialization creates a new instance
    and reassigns the global, direct imports don't see the update. This function always
    returns the current global instance.
    """
    global sym_spell
    return sym_spell
