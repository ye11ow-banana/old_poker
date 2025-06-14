import asyncio
import random
from datetime import UTC, datetime
from typing import Generator, Literal, Sequence
from uuid import UUID

from auth.schemas import UserInfoDTO
from game.exceptions import GameIsFinishedError
from game.models import Suit
from game.schemas import (
    CardDTO,
    FullCardInfoDTO,
    FullEntryCardInfoDTO,
    FullGameCardInfoDTO,
    FullUserCardInfoDTO,
    GameInfoDTO,
    ProcessCardDTO,
    UserCardDTO,
    UserCardListDTO,
)
from unitofwork import IUnitOfWork

CARDS = {
    CardDTO(suit=member.value, value=value)
    for value in range(6, 15)
    for member in Suit
}


class GameService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow: IUnitOfWork = uow

    async def process_card(self, card: ProcessCardDTO, game_id: UUID) -> None:
        async with self._uow:
            dealing = await self._uow.dealings.get(
                round_id=card.round_id,
                user_id=card.owner_id,
            )
            entry = await self._uow.entries.get_or_create(
                round_id=card.round_id,
                owner_id=card.owner_id,
            )
            dealing_cards = await self._uow.cards.get_cards_by_dealing_id(
                dealing_id=dealing.id,
            )
            entry_cards = await self._uow.cards.get_cards_by_entry_id(
                entry_id=entry.id,
            )
            card_orm = await self._uow.cards.get(
                id=card.card_id,
            )
            current_card = UserCardDTO(
                suit=card_orm.suit.value,
                value=card_orm.value,
                id=card_orm.id,
                user_id=card.owner_id,
                entry_id=entry.id,
            )
            round_ = await self._uow.rounds.get(
                id=card.round_id,
            )
            self._check_card_validity(
                card=current_card,
                dealing_cards=dealing_cards,
                entry_cards=entry_cards,
                trump_suit=round_.trump_suit,
            )
            await self._uow.cards.update(
                {"id": card.card_id},
                entry_id=entry.id,
            )
            owner_id = self._get_new_owner_id(
                card=current_card,
                entry_cards=entry_cards,
                trump_suit=round_.trump_suit,
            )
            await self._uow.entries.update(
                {"round_id": card.round_id},
                owner_id=owner_id,
            )
            if card.is_round_end:
                try:
                    await self._actualize_round(game_id, round_.id)
                    await self._uow.rounds.make_new_current(
                        game_id, card.round_id
                    )
                except GameIsFinishedError:
                    await self._finish_game(game_id, round_.id)
                    await self._uow.commit()
                    raise
            await self._uow.commit()

    async def get_full_game_info(self, game_id: UUID) -> FullGameCardInfoDTO:
        flatten_info_list = await self._uow.games.get_full_game_info(game_id)
        user_cards = []
        entry_cards = []
        for info in flatten_info_list:
            card = FullCardInfoDTO(
                id=info.card_id,
                suit=info.suit,
                value=info.value,
                user_id=info.user_id,
                entry_id=info.entry_id,
            )
            if info.entry_id is None:
                user_cards.append(card)
            else:
                entry_cards.append(card)
        user_ids = {user.user_id for user in flatten_info_list}
        return FullGameCardInfoDTO(
            round_id=flatten_info_list[0].round_id,
            users=[
                FullUserCardInfoDTO(
                    id=info.user_id,
                    username=info.username,
                    email=info.email,
                    elo=info.elo,
                    created_at=info.created_at,
                    bid=info.bid,
                    actual_bid=info.actual_bid,
                    score=info.score,
                    cards=[
                        card
                        for card in user_cards
                        if card.user_id == info.user_id
                    ],
                )
                for info in flatten_info_list
                if info.user_id in user_ids
            ],
            entry=FullEntryCardInfoDTO(
                id=entry_cards[0].entry_id,
                cards=entry_cards,
            )
            if entry_cards
            else None,
            trump_suit=flatten_info_list[0].trump_suit,
            trump_value=flatten_info_list[0].trump_value,
        )

    async def get_full_spectator_game_info(
        self, game_id: UUID
    ) -> FullGameCardInfoDTO:
        await asyncio.sleep(60 * 5)
        return await self.get_full_game_info(game_id)

    async def create_game(self, players: list[UserInfoDTO]) -> GameInfoDTO:
        async with self._uow:
            game = await self._uow.games.add(
                type="MULTIPLAYER",
                players_number=len(players),
            )
            for player in players:
                await self._uow.game_players.add(
                    game_id=game.id,
                    user_id=player.id,
                )
            await self.create_rounds_with_cards(game.id, players)
            await self._uow.commit()
        return GameInfoDTO(
            id=game.id,
            players=players,
            created_at=game.created_at,
        )

    async def create_rounds_with_cards(
        self,
        game_id: UUID,
        players: list[UserInfoDTO],
    ) -> None:
        circular_players_generator = self._get_circular_iterations(players)
        dealer = next(circular_players_generator)
        opening_player = next(circular_players_generator)
        is_current_round = True
        for index, round_name in enumerate(
            self._generate_rounds(len(players))
        ):
            users_with_cards, used_cards = self._generate_cards_for_round(
                round_name, players
            )
            trump_suit, trump_value = self._pick_trump(round_name, used_cards)
            round_obj = await self._uow.rounds.add(
                trump_suit=trump_suit,
                trump_value=trump_value,
                round_name=round_name,
                round_number=index + 1,
                is_current_round=is_current_round,
                dealer_id=dealer.id,
                opening_player_id=opening_player.id,
                game_id=game_id,
            )
            is_current_round = False
            for user in users_with_cards:
                dealing = await self._uow.dealings.add(
                    user_id=user.id, round_id=round_obj.id, score=0
                )
                for card in user.cards:
                    await self._uow.cards.add(
                        dealing_id=dealing.id,
                        suit=card.suit,
                        value=card.value,
                    )
            dealer = opening_player
            opening_player = next(circular_players_generator)

    async def is_player(self, user_id: UUID, game_id: UUID) -> bool:
        async with self._uow:
            return await self._uow.game_players.is_player(user_id, game_id)

    async def get_current_round_card_count(self, game_id: UUID) -> int:
        async with self._uow:
            game_info = await self.get_full_game_info(game_id)
        card_count = 0
        for user in game_info.users:
            card_count += len(user.cards)
        if game_info.entry:
            card_count += len(game_info.entry.cards)
        return card_count / len(game_info.users)

    async def bid(self, user_id: UUID, game_id: UUID, bid: int) -> None:
        async with self._uow:
            current_round = await self._uow.rounds.get_current_round(game_id)
            current_dealing = await self._uow.dealings.get_current_dealing(
                current_round.id, user_id
            )
            await self._uow.dealings.update(
                {"id": current_dealing.id},
                bid=bid,
            )
            await self._uow.commit()

    async def _finish_game(self, game_id: UUID, round_id: UUID) -> None:
        await self._uow.games.update(
            {"id": game_id},
            is_finished=True,
            finished_at=datetime.now(UTC),
        )
        await self._update_ratings(game_id, round_id)

    async def _update_ratings(self, game_id: UUID, round_id: UUID) -> None:
        dealings = await self._uow.dealings.get_all(round_id=round_id)
        max_score: int | None = None
        for dealing in dealings:
            if max_score is None or dealing.score > max_score:
                max_score = dealing.score
        for dealing in dealings:
            if dealing.score == max_score:
                await self._uow.game_winners.add(
                    game_id=game_id,
                    user_id=dealing.user_id,
                )
        for dealing in dealings:
            user = await self._uow.users.get(id=dealing.user_id)
            new_elo = user.elo + (dealing.score - max_score * 2 / 3) * 10
            await self._uow.users.update(
                {"id": user.id},
                elo=new_elo,
            )

    @staticmethod
    def _check_card_validity(
        card: UserCardDTO,
        dealing_cards: list[CardDTO],
        entry_cards: list[CardDTO],
        trump_suit: Literal["H", "D", "C", "S"] | None = None,
    ) -> bool:
        try:
            first_card = entry_cards[0]
        except IndexError:
            return True
        if card.suit != first_card.suit and card.suit != trump_suit:
            is_valid = True
            for dealing_card in dealing_cards:
                if (
                    dealing_card.suit == first_card.suit
                    or dealing_card.suit == trump_suit
                ):
                    is_valid = False
                    break
            return is_valid
        return True

    @staticmethod
    def _get_new_owner_id(
        card: UserCardDTO,
        entry_cards: list[CardDTO],
        trump_suit: Literal["H", "D", "C", "S"] | None = None,
    ) -> UUID:
        if not entry_cards:
            return card.user_id
        owner_card = card
        for entry_card in entry_cards:
            if (
                entry_card.suit == owner_card.suit
                and entry_card.value > owner_card.value
            ):
                owner_card = entry_card
            elif (
                entry_card.suit == trump_suit and owner_card.suit != trump_suit
            ):
                owner_card = entry_card
            elif (
                entry_card.suit == trump_suit and owner_card.suit == trump_suit
            ):
                if entry_card.value > owner_card.value:
                    owner_card = entry_card
        return owner_card.user_id

    async def _actualize_round(self, game_id: UUID, round_id: UUID) -> None:
        entries = await self._uow.entries.get_all(round_id=round_id)
        dealings = await self._uow.dealings.get_all(round_id=round_id)
        user_bid_map = {}
        for entry in entries:
            if entry.owner_id in user_bid_map:
                user_bid_map[entry.owner_id] += 1
            else:
                user_bid_map[entry.owner_id] = 1
        for dealing in dealings:
            if dealing.user_id in user_bid_map:
                actual_bid = user_bid_map[dealing.user_id]
            else:
                actual_bid = 0
            if actual_bid == dealing.bid and dealing.bid == 0:
                score_addition = 5
            elif actual_bid == dealing.bid:
                score_addition = actual_bid * 10
            elif actual_bid > dealing.bid:
                score_addition = actual_bid
            else:
                score_addition = (actual_bid - dealing.bid) * 10
            previous_round = await self._uow.rounds.get_previous_round(game_id)
            if previous_round is None:
                old_score = 0
            else:
                old_dealing = await self._uow.dealings.get(
                    round_id=previous_round.id,
                    user_id=dealing.user_id,
                )
                old_score = old_dealing.score if old_dealing else 0
                old_score = old_score if old_score is not None else 0
            score = old_score + score_addition
            await self._uow.dealings.update(
                {"id": dealing.id},
                actual_bid=actual_bid,
                score=score,
            )

    @staticmethod
    def _generate_cards_for_round(
        round_name: str, players: list[UserInfoDTO]
    ) -> tuple[list[UserCardListDTO], set[CardDTO]]:
        max_cards_per_player = (
            int(round_name) if round_name.isnumeric() else 36 // len(players)
        )
        users_with_cards: list[UserCardListDTO] = []
        used_cards: set[CardDTO] = set()
        for player in players:
            cards: list[CardDTO] = []
            for _ in range(max_cards_per_player):
                card: CardDTO = random.choice(list(CARDS - used_cards))
                cards.append(card)
                used_cards.add(card)
            users_with_cards.append(
                UserCardListDTO(
                    id=player.id,
                    username=player.username,
                    email=player.email,
                    elo=player.elo,
                    created_at=player.created_at,
                    cards=cards,
                )
            )
        return users_with_cards, used_cards

    @staticmethod
    def _generate_rounds(players_number: int) -> Sequence[str]:
        max_card_per_player = 36 // players_number
        rounds = ["1"] * players_number
        rounds += [str(_) for _ in range(2, max_card_per_player)]
        rounds += [str(max_card_per_player)] * players_number
        rounds += [str(_) for _ in range(max_card_per_player - 1, 2 - 1, -1)]
        rounds += ["1"] * players_number
        rounds += ["BR"] * players_number  # Blind Round
        rounds += ["NTR"] * players_number  # No Trumps Round
        return rounds

    @staticmethod
    def _get_circular_iterations(
        start_list: list[UserInfoDTO],
    ) -> Generator[UserInfoDTO, None, None]:
        """
        Iterates through start_list circularly, starting from a random element,
        and yields elements for each item in control_list.
        """
        start_index = random.randint(0, len(start_list) - 1)

        while True:
            for i in range(start_index, len(start_list)):
                yield start_list[i]
            for i in range(0, start_index):
                yield start_list[i]

    @staticmethod
    def _pick_trump(
        round_name: str, used_cards: set[CardDTO]
    ) -> tuple[Literal["H", "D", "C", "S"] | None, int | None]:
        unused_cards = CARDS - used_cards
        if not unused_cards:
            return random.choice(["H", "D", "C", "S"]), None
        trump_card: CardDTO = random.choice(list(unused_cards))
        trump_suit = trump_card.suit
        trump_value = trump_card.value
        if round_name == "NTR" or (trump_suit == "S" and trump_value == 7):
            trump_suit = None
            trump_value = None
        return trump_suit, trump_value
