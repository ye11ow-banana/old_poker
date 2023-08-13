from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from auth.exceptions import RegistrationException
from auth.schemas import UserInCreate, UserInfo
from unitofwork import IUnitOfWork


class RegistrationService:
    def __init__(self, uow: IUnitOfWork):
        self._uof: IUnitOfWork = uow
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def register_user(self, user: UserInCreate) -> UserInfo:
        hashed_password = await self._hash_password(user.password)
        try:
            async with self._uof:
                new_user = await self._create_user(
                    user.username, hashed_password
                )
                await self._uof.commit()
        except IntegrityError:
            raise RegistrationException(
                "User with this username already exists"
            )
        return new_user

    async def _create_user(self, username: str, password: str) -> UserInfo:
        return await self._uof.users.add(
            username=username, hashed_password=password
        )

    async def _hash_password(self, plain_password: str) -> str:
        return self._pwd_context.hash(plain_password)
