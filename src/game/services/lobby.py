from uuid import UUID

from sqlalchemy.exc import IntegrityError

from auth.schemas import UserInfoDTO
from game.schemas import LobbyIdDTO, LobbyUserInfoDTO
from unitofwork import IUnitOfWork


class LobbyService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow: IUnitOfWork = uow

    async def create_lobby(self, user: UserInfoDTO) -> LobbyIdDTO:
        async with self._uow:
            lobby = await self._uow.lobbies.add(leader_id=user.id)
            await self._uow.lobby_players.add(
                lobby_id=lobby.id, user_id=user.id
            )
            await self._uow.commit()
        return LobbyIdDTO.model_validate(lobby)

    async def remove_user_from_lobby(
        self, user: UserInfoDTO, lobby_id: UUID
    ) -> None:
        async with self._uow:
            lobby = await self._uow.lobbies.get(
                returns=("id", "leader_id"), id=lobby_id
            )
            if lobby.leader_id == user.id:
                await self._uow.lobbies.remove(id=lobby_id)
            else:
                await self._uow.lobby_players.remove(
                    lobby_id=lobby_id, user_id=user.id
                )
            await self._uow.commit()

    async def add_user_to_lobby(
        self, user: UserInfoDTO, lobby_id: UUID
    ) -> None:
        try:
            async with self._uow:
                await self._uow.lobby_players.add(
                    lobby_id=lobby_id, user_id=user.id
                )
                await self._uow.commit()
        except IntegrityError as e:
            raise ValueError(str(e))

    async def get_players_in_lobby(
        self, lobby_id: UUID
    ) -> list[LobbyUserInfoDTO]:
        return await self._uow.lobbies.get_players_in_lobby(lobby_id=lobby_id)
