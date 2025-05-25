from typing import Annotated

from fastapi import Depends, HTTPException, WebSocketException, status
from fastapi.requests import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.websockets import WebSocket

from auth.exceptions import AuthenticationException
from auth.schemas import UserInfoDTO
from auth.services.authentication import JWTAuthenticationService
from unitofwork import IUnitOfWork, UnitOfWork
from utils import Pagination

UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]


class _Pagination:
    async def __call__(self, page: int = 1) -> Pagination:
        return Pagination(page=page)


PaginationDep = Annotated[Pagination, Depends(_Pagination())]


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
    ) -> UserInfoDTO:
        try:
            user = await JWTAuthenticationService(uow).get_current_user(token)
        except AuthenticationException:
            raise http_exception
        return user


AuthenticatedUserDep = Annotated[UserInfoDTO, Depends(_AuthenticatedUser())]


def _ws_exception_1008() -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


ws_exception_1008_dep = Annotated[
    WebSocketException, Depends(_ws_exception_1008)
]


class _WSAuthenticatedUser:
    async def __call__(
        self,
        ws_exception: ws_exception_1008_dep,
        websocket: WebSocket,
        uow: UOWDep,
    ) -> UserInfoDTO:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        else:
            raise ws_exception
        try:
            user = await JWTAuthenticationService(uow).get_current_user(token)
        except AuthenticationException:
            raise ws_exception
        return user


WSAuthenticatedUserDep = Annotated[
    UserInfoDTO, Depends(_WSAuthenticatedUser())
]
