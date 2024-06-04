import random
from typing import Sequence, Generator, Literal
from uuid import UUID

from auth.schemas import UserInfoDTO
from game.models import Suit
from game.schemas import (
    LobbyUserInfoDTO,
    GameInfoDTO,
    CardDTO,
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

    async def create_game(
        self, players: list[LobbyUserInfoDTO], create_game: bool
    ) -> GameInfoDTO | None:
        if not create_game:
            return
        async with self._uow:
            game = await self._uow.games.add(
                type="multiplayer",
                players_number=len(players),
            )
            for player in players:
                await self._uow.game_players.add(
                    game_id=game.id,
                    user_id=player.id,
                )
            await self.create_sets_with_cards(game.id, players)
            await self._uow.commit()
        return GameInfoDTO(
            id=game.id,
            players=[
                UserInfoDTO(id=player.id, username=player.username)
                for player in players
            ],
            created_at=game.created_at,
        )

    async def create_sets_with_cards(
        self,
        game_id: UUID,
        players: list[LobbyUserInfoDTO],
    ) -> None:
        circular_players_generator = self._get_circular_iterations(players)
        dealer = next(circular_players_generator)
        opening_player = next(circular_players_generator)
        is_current_round = True
        for set_name in self._generate_sets(len(players)):
            users_with_cards, used_cards = self._generate_cards_for_set(
                set_name, players
            )
            trump_suit, trump_value = self._pick_trump(set_name, used_cards)
            set_obj = await self._uow.sets.add(
                trump_suit=trump_suit,
                trump_value=trump_value,
                round_name=set_name,
                is_current_round=is_current_round,
                dealer_id=dealer.id,
                opening_player_id=opening_player.id,
                game_id=game_id,
            )
            is_current_round = False
            for user in users_with_cards:
                dealing = await self._uow.dealings.add(
                    user_id=user.id, set_id=set_obj.id
                )
                for card in user.cards:
                    await self._uow.cards.add(
                        dealing_id=dealing.id,
                        suit=card.suit,
                        value=card.value,
                    )
            dealer = opening_player
            opening_player = next(circular_players_generator)

    @staticmethod
    def _generate_cards_for_set(
        set_name: str, players: list[LobbyUserInfoDTO]
    ) -> tuple[list[UserCardListDTO], set[CardDTO]]:
        max_cards_per_player = (
            int(set_name) if set_name.isnumeric() else 36 // len(players)
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
                    id=player.id, username=player.username, cards=cards
                )
            )
        return users_with_cards, used_cards

    @staticmethod
    def _generate_sets(players_number: int) -> Sequence[str]:
        max_card_per_player = 36 // players_number
        sets = ["1"] * players_number
        sets += [str(_) for _ in range(2, max_card_per_player)]
        sets += [str(max_card_per_player)] * players_number
        sets += [str(_) for _ in range(max_card_per_player - 1, 2 - 1, -1)]
        sets += ["1"] * players_number
        sets += ["BR"] * players_number  # Blind Round
        sets += ["NTR"] * players_number  # No Trumps Round
        return sets

    @staticmethod
    def _get_circular_iterations(
        start_list: list[LobbyUserInfoDTO],
    ) -> Generator[LobbyUserInfoDTO, None, None]:
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
        set_name: str, used_cards: set[CardDTO]
    ) -> tuple[Literal["H", "D", "C", "S"] | None, int | None]:
        unused_cards = CARDS - used_cards
        if not unused_cards:
            return random.choice(["H", "D", "C", "S"]), None
        trump_card: CardDTO = random.choice(list(unused_cards))
        trump_suit = trump_card.suit
        trump_value = trump_card.value
        if set_name == "NTR" or (trump_suit == "S" and trump_value == 7):
            trump_suit = None
            trump_value = None
        return trump_suit, trump_value
