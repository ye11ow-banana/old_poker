import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.util.preloaded import orm

from auth.models import User
from database import Base
from database import uuidpk, created_at


class UserGamePlayer(Base):
    __tablename__ = "players"

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


class UserGameWinner(Base):
    __tablename__ = "winners"

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
    multiplayer = "Multiplayer"
    single = "Single"
    analysis = "Analysis"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuidpk]
    type: Mapped[GameType]
    players_number: Mapped[int]
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[created_at]
    finished_at: Mapped[datetime | None]

    players: Mapped[list["User"]] = relationship(
        secondary="players", back_populates="games"
    )
    winners: Mapped[list["User"]] = relationship(
        secondary="winners", back_populates="games_won"
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
