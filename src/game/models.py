import enum
import uuid
from datetime import datetime

from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from auth.models import User
from database import Base, created_at, uuidpk


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
    MULTIPLAYER = "MULTIPLAYER"
    SINGLE = "SINGLE"
    ANALYSIS = "ANALYSIS"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuidpk]
    type: Mapped[GameType]
    players_number: Mapped[int]
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[created_at]
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    players: Mapped[list["User"]] = relationship(
        secondary="game_players", back_populates="games"
    )
    winners: Mapped[list["User"]] = relationship(
        "User", secondary="game_winners", back_populates="games_won"
    )

    @validates("players_number")
    def validate_players_number(self, _, value: int) -> int:
        if not 2 <= value <= 36:
            raise ValueError(
                f"Players number should be between 2 and 36, got {value}"
            )
        return value

    @validates("finished_at")
    def validate_finished_at(self, _, value: int) -> int:
        if self.is_finished and not value:
            raise ValueError("Date finished should be set for finished game")
        if self.finished_at < self.created_at:
            raise ValueError(
                "Date finished should be greater than date created"
            )
        return value

    @validates("winners")
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
    )
    players: Mapped[list["User"]] = relationship(
        "User", secondary="lobby_players", back_populates="lobbies"
    )


class Suit(enum.Enum):
    H = "H"
    D = "D"
    C = "C"
    S = "S"


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[uuidpk]
    trump_suit: Mapped[Suit] = mapped_column(nullable=True)
    trump_value: Mapped[int] = mapped_column(nullable=True)
    round_name: Mapped[str] = mapped_column(nullable=False)
    round_number: Mapped[int | None] = mapped_column(nullable=True)
    is_current_round: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    dealer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    opening_player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
    )

    @validates("trump_value")
    def validate_trump_value(self, _, value: int | None) -> int | None:
        if value is None:
            return value
        if not 6 <= value <= 14:
            raise ValueError(f"Value should be between 6 and 14, got {value}")
        return value


class Dealing(Base):
    __tablename__ = "dealings"

    id: Mapped[uuidpk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rounds.id", ondelete="CASCADE"),
    )
    bid: Mapped[int | None]
    actual_bid: Mapped[int | None]
    score: Mapped[int | None] = mapped_column(default=None, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "round_id", name="_user_round_uc"),
    )


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[uuidpk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rounds.id", ondelete="CASCADE"),
    )
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    finished_at: Mapped[datetime | None]


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuidpk]
    suit: Mapped[Suit] = mapped_column(nullable=False)
    value: Mapped[int] = mapped_column(nullable=False)
    dealing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dealings.id", ondelete="CASCADE"),
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=True,
    )

    @validates("value")
    def validate_value(self, _, value: int) -> int:
        if not 6 <= value <= 14:
            raise ValueError(f"Value should be between 6 and 14, got {value}")
        return value
