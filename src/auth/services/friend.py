from abc import ABC, abstractmethod

from auth.schemas import UserInfoDTO
from unitofwork import IUnitOfWork


class IFriendService(ABC):
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow

    @abstractmethod
    async def get_friends(self, user: UserInfoDTO) -> list[UserInfoDTO]:
        raise NotImplementedError


class M2MFriendService(IFriendService):
    """
    Service that provides access to friends of a user
    using a database M2M relationship.
    """

    async def get_friends(self, user: UserInfoDTO) -> list[UserInfoDTO]:
        async with self._uow:
            return await self._uow.users.get_friends(id=str(user.id))
