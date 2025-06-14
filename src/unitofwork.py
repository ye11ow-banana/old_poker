from abc import ABC, abstractmethod

from auth.repositories import FriendshipRepository, UserRepository
from database import async_session_maker
from game.repositories import (
    CardRepository,
    DealingRepository,
    EntryRepository,
    GamePlayerRepository,
    GameRepository,
    GameWinnerRepository,
    LobbyPlayerRepository,
    LobbyRepository,
    RoundRepository,
)


class IUnitOfWork(ABC):
    users: UserRepository
    friendship: FriendshipRepository
    lobbies: LobbyRepository
    lobby_players: LobbyPlayerRepository
    games: GameRepository
    game_players: GamePlayerRepository
    game_winners: GameWinnerRepository
    rounds: RoundRepository
    dealings: DealingRepository
    cards: CardRepository
    entries: EntryRepository

    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class UnitOfWork(IUnitOfWork):
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self._session = self.session_factory()
        self.users = UserRepository(self._session)
        self.friendship = FriendshipRepository(self._session)
        self.lobbies = LobbyRepository(self._session)
        self.lobby_players = LobbyPlayerRepository(self._session)
        self.games = GameRepository(self._session)
        self.game_players = GamePlayerRepository(self._session)
        self.game_winners = GameWinnerRepository(self._session)
        self.rounds = RoundRepository(self._session)
        self.dealings = DealingRepository(self._session)
        self.cards = CardRepository(self._session)
        self.entries = EntryRepository(self._session)

    async def __aexit__(self, *args):
        await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
