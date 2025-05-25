from abc import ABC, abstractmethod

from auth.schemas import UserInfoDTO
from notification.schemas import FriendResponsePayload
from unitofwork import IUnitOfWork


class IFriendService(ABC):
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow

    @abstractmethod
    async def get_friends(self, user: UserInfoDTO) -> list[UserInfoDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_friend_requests(
        self, user: UserInfoDTO
    ) -> list[UserInfoDTO]:
        raise NotImplementedError


class M2MFriendService(IFriendService):
    """
    Service that provides access to friends of a user
    using a database M2M relationship.
    """

    async def get_friends(self, user: UserInfoDTO) -> list[UserInfoDTO]:
        async with self._uow:
            return await self._uow.users.get_all_friends(
                user_id=user.id,
                returns=(
                    "id",
                    "username",
                    "email",
                ),
            )

    async def get_friend_requests(
        self, user: UserInfoDTO
    ) -> list[UserInfoDTO]:
        return await self._uow.users.get_possible_friends(
            user_id=user.id, returns=("id", "username"), status="REQUESTED"
        )

    async def process_friend_request(
        self, data: FriendResponsePayload
    ) -> None:
        async with self._uow:
            if data.response == "ACCEPTED":
                try:
                    await self._uow.friendship.accept_friend_request(
                        user_id=data.inviter_id, friend_id=data.invitee_id
                    )
                except ValueError:
                    await self._uow.rollback()
                else:
                    await self._uow.commit()
