from auth.schemas import UserInfoDTO
from game.schemas import LobbyUserInfoDTO, GameInfoDTO
from unitofwork import IUnitOfWork


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
            await self._uow.commit()
        return GameInfoDTO(
            id=game.id,
            players=[
                UserInfoDTO(id=player.id, username=player.username)
                for player in players
            ],
            created_at=game.created_at,
        )
