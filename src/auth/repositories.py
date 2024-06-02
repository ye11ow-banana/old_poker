from typing import Sequence, Literal
from uuid import UUID

from sqlalchemy import select, or_

from auth import models, Friendship
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


class FriendshipRepository(SQLAlchemyRepository):
    model = models.Friendship
