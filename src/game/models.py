import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UUID, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.util.preloaded import orm

from auth.models import User
from database import Base
from database import uuidpk, created_at


class GamePlayer(Base):
    __tablename__ = "game_players"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class GameWinner(Base):
    __tablename__ = "game_winners"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class GameType(enum.Enum):
    multiplayer = "multiplayer"
    single = "single"
    analysis = "analysis"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuidpk]
    type: Mapped[GameType]
    players_number: Mapped[int]
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[created_at]
    finished_at: Mapped[datetime | None]

    players: Mapped[list["User"]] = relationship(
        secondary="game_players", back_populates="games"
    )
    winners: Mapped[list["User"]] = relationship(
        "User", secondary="game_winners", back_populates="games_won"
    )

    @orm.validates("players_number")
    def validate_players_number(self, _, value: int) -> int:
        if not 2 <= value <= 36:
            raise ValueError(
                f"Players number should be between 2 and 36, got {value}"
            )
        return value

    @orm.validates("date_finished")
    def validate_date_finished(self, _, value: int) -> int:
        if self.is_finished and not value:
            raise ValueError("Date finished should be set for finished game")
        if self.finished_at < self.created_at:
            raise ValueError(
                "Date finished should be greater than date created"
            )
        return value

    @orm.validates("players")
    def validate_players(self, _, value: User) -> User:
        real_players_number = len(self.players)
        if real_players_number != self.players_number:
            raise ValueError(
                f"Players number should be equal to players number, got {real_players_number}"
            )
        return value

    @orm.validates("winners")
    def validate_winners(self, _, value: User) -> User:
        if not self.is_finished:
            raise ValueError(f"Game should be finished to set winners")
        if value not in self.players:
            raise ValueError(f"Winner should be in players")
        return value


class LobbyPlayer(Base):
    __tablename__ = "lobby_players"

    lobby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lobbies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Lobby(Base):
    __tablename__ = "lobbies"

    id: Mapped[uuidpk]
    created_at: Mapped[created_at]
    leader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    players: Mapped[list["User"]] = relationship(
        "User", secondary="lobby_players", back_populates="lobbies"
    )


class Suit(enum.Enum):
    hearts = "hearts"
    diamonds = "diamonds"
    clubs = "clubs"
    spades = "spades"


class Set(Base):
    __tablename__ = "sets"

    id: Mapped[uuidpk]
    trump_suit: Mapped[Suit] = mapped_column(nullable=False)
    round_name: Mapped[str] = mapped_column(nullable=False)
    dealer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
    )


class Dealing(Base):
    __tablename__ = "dealings"

    id: Mapped[uuidpk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sets.id", ondelete="CASCADE"),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "set_id", name="_user_set_uc"),
    )


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[uuidpk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sets.id", ondelete="CASCADE"),
    )
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    finished_at: Mapped[datetime | None]


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuidpk]
    value: Mapped[int] = mapped_column(nullable=False)
    suit: Mapped[Suit] = mapped_column(nullable=False)
    dealing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dealings.id", ondelete="CASCADE"),
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
    )

    @orm.validates("value")
    def validate_value(self, _, value: int) -> int:
        if not 6 <= value <= 14:
            raise ValueError(f"Value should be between 6 and 14, got {value}")
        return value
