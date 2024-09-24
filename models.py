from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=False, index=True)
    password = Column(String)

class MainDictionary(Base):  # Renamed from Word to MainDictionary
    __tablename__ = "main_dictionary"  # Update the table name as well
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    wordUniqueId = Column(String, unique=True)

class UserAddedWord(Base):
    __tablename__ = "user_added_words"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    frequency = Column(Integer, default=1)

class Suggestion(Base):
    __tablename__ = "suggestions"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    frequency = Column(Integer, default=0)
