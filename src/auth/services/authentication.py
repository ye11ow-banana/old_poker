from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm.exc import NoResultFound

from auth.exceptions import AuthenticationException
from auth.schemas import TokenDTO, UserInDBDTO, UserInfoDTO, UserInLoginDTO
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from unitofwork import IUnitOfWork


class IAuthenticationService(ABC):
    def __init__(self, uof: IUnitOfWork):
        self._uof: IUnitOfWork = uof
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @abstractmethod
    async def authenticate_user(self, data: UserInLoginDTO):
        raise NotImplementedError

    @abstractmethod
    async def get_current_user(self, token: str) -> UserInfoDTO:
        raise NotImplementedError

    async def _verify_password(
        self, plain_password: str, hashed_password: str
    ) -> None:
        try:
            is_password_verified = self._pwd_context.verify(
                plain_password, hashed_password
            )
        except UnknownHashError:
            raise ValueError("Incorrect password")
        if not is_password_verified:
            raise ValueError("Incorrect password")

    async def _get_db_user_by_username(
        self, username: str, **kwargs
    ) -> UserInDBDTO:
        return await self._uof.users.get(username=username, **kwargs)


class JWTAuthenticationService(IAuthenticationService):
    async def authenticate_user(self, user: UserInLoginDTO) -> TokenDTO:
        try:
            async with self._uof:
                db_user = await self._get_db_user_by_username(user.username)
            await self._verify_password(user.password, db_user.hashed_password)
        except (NoResultFound, ValueError):
            raise AuthenticationException("Incorrect username or password")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await self.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return TokenDTO(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str) -> UserInfoDTO:
        try:
            async with self._uof:
                db_user = await self._get_db_user_by_jwt(
                    token, returns=("id", "username")
                )
        except JWTError:
            raise AuthenticationException("Could not validate credentials")
        return db_user.to_user_info()

    @staticmethod
    async def create_access_token(
        data: dict, expires_delta: timedelta | None = None
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)
        expire = datetime.utcnow() + expires_delta
        data.update({"exp": expire})
        encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        return str(encoded_jwt)

    async def _get_db_user_by_jwt(self, token: str, **kwargs) -> UserInDBDTO:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError
        try:
            db_user = await self._get_db_user_by_username(username, **kwargs)
        except NoResultFound:
            raise JWTError
        return db_user
