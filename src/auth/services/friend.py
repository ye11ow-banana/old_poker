from abc import ABC, abstractmethod

from sqlalchemy.exc import IntegrityError

from auth.schemas import UserInfoDTO
from notification.schemas import FriendNotificationDTO
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
                ),
            )

    async def get_friend_requests(
        self, user: UserInfoDTO
    ) -> list[UserInfoDTO]:
        return await self._uow.users.get_possible_friends(
            user_id=user.id, returns=("id", "username"), status="REQUESTED"
        )

    async def process_friend_request(
        self, user: UserInfoDTO, data: FriendNotificationDTO
    ) -> None:
        if data.type == "friend_request":
            try:
                async with self._uow:
                    await self._uow.friendship.add(
                        left_user_id=user.id,
                        right_user_id=data.data.id,
                        status="REQUESTED",
                    )
                    await self._uow.commit()
            except IntegrityError:
                # Friendship already exists
                pass
        elif data.type == "friend_request_response":
            what_to_update = {
                "left_user_id": data.data.id,
                "right_user_id": user.id,
            }
            if data.data.status == "accept":
                async with self._uow:
                    await self._uow.friendship.update(
                        what_to_update, status="ACCEPTED"
                    )
                    await self._uow.commit()
            elif data.data.status == "decline":
                async with self._uow:
                    await self._uow.friendship.update(
                        what_to_update, status="DECLINED"
                    )
                    await self._uow.commit()
