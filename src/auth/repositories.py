from typing import Sequence

from auth import models
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

    async def get_friends(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> list[UserInfoDTO]:
        friends = await super().get_friends(**data)
        print(friends)
        return [UserInfoDTO.model_validate(friend) for friend in friends]
