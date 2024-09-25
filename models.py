from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)  # Specify length for VARCHAR
    email = Column(String(100), unique=True, index=True)     # Specify length for email
    phone = Column(String(15), unique=False, index=True)     # Specify length for phone number
    password = Column(String(128))  # Assuming hashed password

class MainDictionary(Base):
    __tablename__ = "main_dictionary"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), unique=True, nullable=False)  # Specify length for word
    added_by_username = Column(String(100), ForeignKey("users.username"), nullable=True)  # Changed to username
    wordUniqueId = Column(String(255), unique=True)  # Specify length for unique identifier
    frequency = Column(Integer, default=1)  # Add frequency column with default value 1

class UserAddedWord(Base):
    __tablename__ = "user_added_words"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False)  # Specify length for word
    added_by_username = Column(String(100), ForeignKey("users.username"), nullable=True)  # Changed to username
    frequency = Column(Integer, default=1)

class Suggestion(Base):
    __tablename__ = "suggestions"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False)  # Specify length for word
    frequency = Column(Integer, default=0)
