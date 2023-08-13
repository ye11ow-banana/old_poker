from uuid import uuid4

from sqlalchemy import UUID, Column, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
