from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from game import models
from game.schemas import LobbyInfoDTO, LobbyIdDTO, LobbyUserInfoDTO
from repository import SQLAlchemyRepository


class LobbyRepository(SQLAlchemyRepository):
    model = models.Lobby

    async def get_last_or_create(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> LobbyIdDTO:
        return LobbyIdDTO.model_validate(
            await super().get_last_or_create(returns=returns, **data)
        )

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> LobbyInfoDTO:
        return LobbyInfoDTO.model_validate(
            await super().get(returns=returns, **data)
        )

    async def get_players_in_lobby(
        self, /, lobby_id: UUID
    ) -> list[LobbyUserInfoDTO]:
        query = (
            select(models.User.id, models.User.username, self.model.leader_id)
            .join(
                models.LobbyPlayer,
                models.User.id == models.LobbyPlayer.user_id,
            )
            .join(models.Lobby, models.Lobby.id == models.LobbyPlayer.lobby_id)
            .where(self.model.id == lobby_id)
        )
        res = await self._session.execute(query)
        return [
            LobbyUserInfoDTO(
                id=player.id,
                username=player.username,
                is_leader=player.leader_id == player.id,
            )
            for player in res.fetchall()
        ]


class LobbyPlayerRepository(SQLAlchemyRepository):
    model = models.LobbyPlayer


class GameRepository(SQLAlchemyRepository):
    model = models.Game


class GamePlayerRepository(SQLAlchemyRepository):
    model = models.GamePlayer


class SetRepository(SQLAlchemyRepository):
    model = models.Set


class DealingRepository(SQLAlchemyRepository):
    model = models.Dealing


class CardRepository(SQLAlchemyRepository):
    model = models.Card
