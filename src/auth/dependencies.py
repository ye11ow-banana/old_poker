from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request

from auth.exceptions import AuthenticationException
from auth.repositories import UserRepository
from auth.schemas import User
from auth.services.authentication import (
    IAuthenticationService,
    JWTAuthenticationService,
)


def authentication_service() -> IAuthenticationService:
    return JWTAuthenticationService(UserRepository())


def http_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


class JWT:
    async def __call__(
        self,
        request: Request,
        http_exception_: Annotated[HTTPException, Depends(http_exception)],
    ) -> str:
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise http_exception_
        return token


class AuthenticatedUser:
    async def __call__(
        self,
        http_exception_: Annotated[HTTPException, Depends(http_exception)],
        authentication_service_: Annotated[
            IAuthenticationService, Depends(authentication_service)
        ],
        token: Annotated[str, Depends(JWT())],
    ) -> User:
        try:
            user = await authentication_service_.get_current_user(token)
        except AuthenticationException:
            raise http_exception_
        return user
