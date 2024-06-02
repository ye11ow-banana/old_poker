from uuid import UUID

from auth.schemas import UserInfoDTO
from game.schemas import LobbyIdDTO
from unitofwork import IUnitOfWork


class LobbyService:
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow

    async def get_or_create_lobby(self, user: UserInfoDTO) -> LobbyIdDTO:
        async with self._uow:
            lobby = await self._uow.lobbies.get_last_or_create(
                returns=("id",), leader_id=user.id
            )
            await self._uow.commit()
        return lobby

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
                await self._uow.lobbies.remove_user(user.id)
            await self._uow.commit()
