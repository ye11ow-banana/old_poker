from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from auth import models as auth_models
from auth.schemas import UserInfoDTO
from game import models
from game.exceptions import GameIsFinishedError
from game.schemas import (
    CardDTO,
    EntryIdDTO,
    FlattenFullGameCardInfoDTO,
    LobbyIdDTO,
    LobbyInfoDTO,
    RoundInfoDTO,
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
    ) -> list[UserInfoDTO]:
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
            UserInfoDTO(
                id=player.id,
                username=player.username,
                email=player.email,
                elo=player.elo,
                created_at=player.created_at,
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
                auth_models.User.email,
                auth_models.User.elo,
                auth_models.User.created_at,
                models.Card.id,
                models.Card.suit,
                models.Card.value,
                models.Card.entry_id,
                models.Round.trump_suit,
                models.Round.trump_value,
                models.Round.opening_player_id,
                models.Dealing.bid,
                models.Dealing.actual_bid,
                models.Dealing.score,
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
                email=player[3],
                elo=player[4],
                created_at=player[5],
                card_id=player[6],
                suit=player[7].value if player[7] is not None else None,
                value=player[8],
                entry_id=player[9],
                trump_suit=player[10].value
                if player[10] is not None
                else None,
                trump_value=player[11],
                opening_player_id=player[12],
                bid=player[13],
                actual_bid=player[14],
                score=player[15],
            )
            for player in res.fetchall()
        ]


class GamePlayerRepository(SQLAlchemyRepository):
    model = models.GamePlayer

    async def is_player(self, /, user_id: UUID, game_id: UUID) -> bool:
        query = (
            select(self.model)
            .filter_by(user_id=user_id, game_id=game_id)
            .limit(1)
        )
        res = await self._session.execute(query)
        return res.scalar() is not None


class GameWinnerRepository(SQLAlchemyRepository):
    model = models.GameWinner


class RoundRepository(SQLAlchemyRepository):
    model = models.Round

    async def make_new_current(self, /, game_id: UUID, round_id: UUID) -> None:
        query = select(self.model.round_number).filter_by(id=round_id)
        current_round_number = (
            await self._session.execute(query)
        ).scalar_one()
        query = (
            select(self.model.id)
            .filter_by(
                game_id=game_id,
                is_current_round=False,
                round_number=current_round_number + 1,
            )
            .order_by(self.model.round_number)
        )
        res = await self._session.execute(query)
        new_current_round = res.first()
        await self.update(
            {"id": round_id},
            is_current_round=False,
        )
        if new_current_round is None:
            raise GameIsFinishedError
        else:
            await self.update(
                {"id": new_current_round.id},
                is_current_round=True,
            )

    async def get_current_round(self, /, game_id: UUID) -> models.Round | None:
        query = (
            select(self.model)
            .filter_by(game_id=game_id, is_current_round=True)
            .limit(1)
        )
        res = await self._session.execute(query)
        return res.scalar_one_or_none()

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> RoundInfoDTO:
        round_ = await super().get(returns=returns, **data)
        return RoundInfoDTO(
            id=round_.id,
            trump_suit=round_.trump_suit.value if round_.trump_suit else None,
            trump_value=round_.trump_value if round_.trump_value else None,
            round_name=round_.round_name,
            round_number=round_.round_number,
            is_current_round=round_.is_current_round,
            dealer_id=round_.dealer_id,
            opening_player_id=round_.opening_player_id,
        )

    async def get_previous_round(
        self, /, game_id: UUID
    ) -> models.Round | None:
        query = (
            select(self.model)
            .filter_by(game_id=game_id, is_current_round=False)
            .order_by(self.model.round_number.desc())
            .limit(1)
        )
        res = await self._session.execute(query)
        return res.scalar_one_or_none()


class DealingRepository(SQLAlchemyRepository):
    model = models.Dealing

    async def get_current_dealing(
        self, /, round_id: UUID, user_id: UUID
    ) -> models.Dealing | None:
        query = (
            select(self.model)
            .filter_by(round_id=round_id, user_id=user_id)
            .limit(1)
        )
        res = await self._session.execute(query)
        return res.scalar_one_or_none()


class CardRepository(SQLAlchemyRepository):
    model = models.Card

    async def get_cards_by_entry_id(self, /, entry_id: UUID) -> list[CardDTO]:
        cards = await self.get_all(entry_id=entry_id)
        return [
            CardDTO(
                suit=card.suit.value if card.suit else None,
                value=card.value,
            )
            for card in cards
        ]

    async def get_cards_by_dealing_id(
        self, /, dealing_id: UUID
    ) -> list[CardDTO]:
        cards = await self.get_all(dealing_id=dealing_id)
        return [
            CardDTO(
                suit=card.suit.value if card.suit else None,
                value=card.value,
            )
            for card in cards
        ]


class EntryRepository(SQLAlchemyRepository):
    model = models.Entry

    async def get_or_create(
        self, round_id: UUID, owner_id: UUID
    ) -> EntryIdDTO:
        obj = await self.get_last(round_id=round_id)
        if obj is None:
            obj = await self.add(round_id=round_id, owner_id=owner_id)
        return EntryIdDTO.model_validate(obj)
