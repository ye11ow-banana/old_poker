from typing import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from auth import Friendship, models
from auth.models import FriendshipStatus
from auth.schemas import UserInDBDTO, UserInfoDTO
from repository import SQLAlchemyRepository
from utils import Pagination


class UserRepository(SQLAlchemyRepository):
    model = models.User

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> UserInDBDTO:
        user = await super().get(returns=returns, **data)
        return UserInDBDTO.model_validate(user)

    async def add(self, **insert_data) -> UserInfoDTO:
        created_user = await super().add(**insert_data)
        return UserInfoDTO.model_validate(created_user)

    async def get_all_friends(
        self,
        /,
        user_id: UUID,
        returns: Sequence[str] | None = None,
    ) -> list[UserInfoDTO]:
        """
        Get all friends of a user by user_id.
        """
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = (
            select(*[getattr(self.model, c) for c in returns])
            .join(
                Friendship,
                or_(
                    self.model.id == Friendship.right_user_id,
                    self.model.id == Friendship.left_user_id,
                ),
            )
            .filter(
                or_(
                    Friendship.left_user_id == user_id,
                    Friendship.right_user_id == user_id,
                ),
                self.model.id != user_id,
            )
        )
        res = await self._session.execute(query)
        return [UserInfoDTO.model_validate(friend) for friend in res.all()]

    async def get_paginated_all(
        self,
        /,
        pagination: Pagination,
        returns: Sequence[str] | None = None,
        **data: str | int,
    ) -> list[UserInfoDTO]:
        users = await super().get_paginated_all(pagination, returns, **data)
        return [UserInfoDTO.model_validate(user) for user in users]

    async def get_possible_friends(
        self,
        /,
        user_id: UUID,
        returns: Sequence[str] | None = None,
        **data: str | int | UUID,
    ) -> list[UserInfoDTO]:
        """
        Get all possible friends of a user by user_id.

        Possible friends are users who are not friends yet with the user and are not the user.
        They are waiting for the user to accept friendship.
        """
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = (
            select(*[getattr(self.model, c) for c in returns])
            .join(
                Friendship,
                self.model.id == Friendship.left_user_id,
            )
            .filter(Friendship.right_user_id == user_id)
            .filter_by(**data)
        )
        res = await self._session.execute(query)
        return [UserInfoDTO.model_validate(friend) for friend in res.all()]

    async def get_by_ids(self, ids: Sequence[UUID]) -> list[UserInfoDTO]:
        query = select(self.model).where(self.model.id.in_(ids))
        res = await self._session.execute(query)
        return [
            UserInfoDTO.model_validate(user) for user in res.scalars().all()
        ]


class FriendshipRepository(SQLAlchemyRepository):
    model = models.Friendship

    async def accept_friend_request(self, /, user_id: UUID, friend_id: UUID) -> None:
        try:
            await self.add(
                left_user_id=user_id,
                right_user_id=friend_id,
                status=FriendshipStatus.ACCEPTED,
            )
        except IntegrityError:
            raise ValueError(
                f"Friendship between {user_id} and {friend_id} already exists."
            )
