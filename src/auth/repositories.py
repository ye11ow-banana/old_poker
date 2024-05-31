from typing import Sequence
from uuid import UUID

from sqlalchemy import select, or_

from auth import models, Friendship
from auth.schemas import UserInDBDTO, UserInfoDTO
from repository import SQLAlchemyRepository


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
        stmt = (
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
        res = await self._session.execute(stmt)
        return [UserInfoDTO.model_validate(friend) for friend in res.all()]
