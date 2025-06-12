from abc import ABC
from uuid import UUID

from game.schemas import UserInfoDTO
from unitofwork import IUnitOfWork


class UserService(ABC):
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow

    async def get_users_by_ids(self, user_ids: list[UUID]) -> list[UserInfoDTO]:
        async with self._uow:
            return await self._uow.users.get_by_ids(user_ids)
