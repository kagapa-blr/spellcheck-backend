from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(15), nullable=True, index=True)
    password = Column(String(128), nullable=False)  # Hashed password

    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', failed_attempts={self.failed_attempts}, "
            f"locked_until={self.locked_until})>"
        )


class MainDictionary(Base):
    __tablename__ = "main_dictionary"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), unique=True, nullable=False)
    added_by_username = Column(String(100), ForeignKey("users.username"), nullable=True)
    frequency = Column(Integer, default=1, nullable=False)
    def __repr__(self):
        return f"<MainDictionary(id={self.id}, word='{self.word}', frequency={self.frequency})>"


class UserAddedWord(Base):
    __tablename__ = "user_added_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False)
    frequency = Column(Integer, default=1, nullable=False)

    def __repr__(self):
        return f"<UserAddedWord(id={self.id}, word='{self.word}', frequency={self.frequency})>"


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False)
    frequency = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Suggestion(id={self.id}, word='{self.word}', frequency={self.frequency})>"
