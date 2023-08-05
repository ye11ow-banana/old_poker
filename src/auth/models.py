from sqlalchemy import Column, UUID, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
