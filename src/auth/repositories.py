from auth.models import User
from typing import Sequence

from auth import models
from auth.schemas import UserInDB, UserInfo
from repository import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository):
    model = User
    model = models.User

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> UserInDB:
        user = await super().get(returns=returns, **data)
        return UserInDB.model_validate(user)
