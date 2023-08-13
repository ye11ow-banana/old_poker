from json import JSONDecodeError
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request

from auth.exceptions import AuthenticationException
from auth.schemas import UserInfo
from auth.services.authentication import JWTAuthenticationService
from unitofwork import IUnitOfWork, UnitOfWork

UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]


def _http_exception_401() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


http_exception_401_dep = Annotated[HTTPException, Depends(_http_exception_401)]


class _JWT:
    async def __call__(
        self, request: Request, http_exception: http_exception_401_dep
    ) -> str:
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise http_exception
        return token


JWTDep = Annotated[str, Depends(_JWT())]


class _AuthenticatedUser:
    async def __call__(
        self,
        http_exception: http_exception_401_dep,
        token: JWTDep,
        uow: UOWDep,
    ) -> UserInfo:
        try:
            user = await JWTAuthenticationService(uow).get_current_user(token)
        except AuthenticationException:
            raise http_exception
        return user


AuthenticatedUserDep = Annotated[UserInfo, Depends(_AuthenticatedUser())]


async def _request_data(request: Request) -> dict:
    try:
        return dict(await request.json())
    except JSONDecodeError:
        return {}


request_data_dep = Annotated[dict, Depends(_request_data)]
