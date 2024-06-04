from __future__ import annotations

import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import UUID, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Base
from database import uuidpk, created_at

if TYPE_CHECKING:
    from game.models import Game, Lobby


class FriendshipStatus(enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


class Friendship(Base):
    __tablename__ = "friendships"

    status: Mapped[FriendshipStatus] = mapped_column(
        default=FriendshipStatus.REQUESTED
    )
    left_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    right_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuidpk]
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024), nullable=False
    )
    elo: Mapped[int] = mapped_column(default=1000, nullable=False)
    created_at: Mapped[created_at]

    friends: Mapped[list["User"]] = relationship(
        secondary="friendships",
        primaryjoin="User.id == foreign(Friendship.left_user_id)",
        secondaryjoin="User.id == foreign(Friendship.right_user_id)",
    )
    games: Mapped[list["Game"]] = relationship(
        secondary="game_players", back_populates="players"
    )
    games_won: Mapped[list["Game"]] = relationship(
        "Game", secondary="game_winners", back_populates="winners"
    )
    lobbies: Mapped[list["Lobby"]] = relationship(
        "Lobby", secondary="lobby_players", back_populates="players"
    )
