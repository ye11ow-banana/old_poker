from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from auth import models as auth_models
from game import models
from game.schemas import (EntryIdDTO, FlattenFullGameCardInfoDTO, LobbyIdDTO,
                          LobbyInfoDTO, LobbyUserInfoDTO)
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

    async def get_full_game_info(
        self, game_id: UUID
    ) -> list[FlattenFullGameCardInfoDTO]:
        query = (
            select(
                models.Round.id,
                auth_models.User.id,
                auth_models.User.username,
                models.Card.id,
                models.Card.suit,
                models.Card.value,
                models.Card.entry_id,
                models.Round.trump_suit,
                models.Round.trump_value,
                models.Round.opening_player_id,
            )
            .join(
                models.Dealing, models.Dealing.user_id == auth_models.User.id
            )
            .join(models.Round, models.Dealing.round_id == models.Round.id)
            .join(models.Card, models.Card.dealing_id == models.Dealing.id)
            .filter(
                models.Round.game_id == game_id,
                models.Round.is_current_round == True,
            )
        )
        res = await self._session.execute(query)
        return [
            FlattenFullGameCardInfoDTO(
                round_id=player[0],
                user_id=player[1],
                username=player[2],
                card_id=player[3],
                suit=player[4].value if player[4] is not None else None,
                value=player[5],
                entry_id=player[6],
                trump_suit=player[7].value if player[7] is not None else None,
                trump_value=player[8],
                opening_player_id=player[9],
            )
            for player in res.fetchall()
        ]


class GamePlayerRepository(SQLAlchemyRepository):
    model = models.GamePlayer


class RoundRepository(SQLAlchemyRepository):
    model = models.Round

    async def make_new_current(self, /, game_id: UUID, round_id: UUID) -> None:
        query = (
            select(self.model.id)
            .filter_by(game_id=game_id, is_current_round=False)
            .order_by(self.model.round_number)
        )
        res = await self._session.execute(query)
        await self.update(
            {"id": res.first().id},
            is_current_round=True,
        )
        await self.update(
            {"id": round_id},
            is_current_round=False,
        )


class DealingRepository(SQLAlchemyRepository):
    model = models.Dealing


class CardRepository(SQLAlchemyRepository):
    model = models.Card


class EntryRepository(SQLAlchemyRepository):
    model = models.Entry

    async def get_or_create(
        self, round_id: UUID, owner_id: UUID
    ) -> EntryIdDTO:
        obj = await self.get_last(round_id=round_id)
        if obj is None:
            obj = await self.add(round_id=round_id, owner_id=owner_id)
        return EntryIdDTO.model_validate(obj)
