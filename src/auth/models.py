from uuid import uuid4

from sqlalchemy import UUID, Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

friends_association_table = Table(
    "friendships",
    Base.metadata,
    Column("left_user_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("right_user_id", UUID(as_uuid=True), ForeignKey("users.id")),
)


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    elo = Column(Integer, default=1000, nullable=False)
    friends = relationship(
        "User",
        secondary=friends_association_table,
        primaryjoin="id==friends_association_table.c.left_user_id",
        secondaryjoin="id==friends_association_table.c.right_user_id",
        backref="friends",
    )
