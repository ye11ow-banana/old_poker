from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from auth import models as auth_models
from game import models
from game.schemas import (
    LobbyInfoDTO,
    LobbyIdDTO,
    LobbyUserInfoDTO,
    FullGameCardInfoDTO,
)
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

    async def get_full_game_info(self, game_id: UUID) -> FullGameCardInfoDTO:
        query = (
            select(
                auth_models.User.id,
                auth_models.User.username,
                models.Card.id,
                models.Card.value,
                models.Card.suit,
                models.Card.entry_id,
                models.Set.trump_suit,
                models.Set.trump_value,
                models.Set.opening_player_id,
            )
            .join(
                models.Dealing, models.Dealing.user_id == auth_models.User.id
            )
            .join(models.Set, models.Dealing.set_id == models.Set.id)
            .join(models.Card, models.Card.dealing_id == models.Dealing.id)
            .filter(
                models.Set.game_id == game_id,
                models.Set.is_current_round == True,
            )
        )
        res = await self._session.execute(query)
        print(res.fetchall())
        1 / 0
        return FullGameCardInfoDTO.model_validate(res.fetchall())


class GamePlayerRepository(SQLAlchemyRepository):
    model = models.GamePlayer


class SetRepository(SQLAlchemyRepository):
    model = models.Set


class DealingRepository(SQLAlchemyRepository):
    model = models.Dealing


class CardRepository(SQLAlchemyRepository):
    model = models.Card
