from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    UUID,
    Column,
    Integer,
    DateTime,
    Boolean,
    Table,
    ForeignKey,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.util.preloaded import orm

from auth.models import User
from database import Base


class GameType:
    multiplayer = "Multiplayer"
    single = "Single"
    analysis = "Analysis"


winners_association_table = Table(
    "winners_association_table",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
)

players_association_table = Table(
    "players_association_table",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    type: Mapped[GameType]
    players_number: Mapped[int]
    is_finished: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    date_created: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    date_finished: Mapped[datetime | None]

    players = relationship(
        "User", secondary=players_association_table, back_populates="games"
    )
    winners = relationship(
        "User", secondary=winners_association_table, back_populates="games_won"
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
        if self.date_finished < self.date_created:
            raise ValueError(
                "Date finished should be greater than date created"
            )
        return value

    @orm.validates("players")
    def validate_players(self, _, value: User) -> int:
        real_players_number = len(self.players)
        if real_players_number != self.players_number:
            raise ValueError(
                f"Players number should be equal to players number, got {real_players_number}"
            )
        return value

    @orm.validates("winners")
    def validate_winners(self, _, value: User) -> int:
        if not self.is_finished:
            raise ValueError(f"Game should be finished to set winners")
        if value not in self.players:
            raise ValueError(f"Winner should be in players")
        return value
