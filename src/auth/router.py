from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import (
    AuthenticatedUser,
    authentication_service,
    http_exception,
)
from auth.exceptions import AuthenticationException
from auth.schemas import User
from auth.services.authentication import IAuthenticationService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    username: str,
    password: str,
    http_exception_: Annotated[HTTPException, Depends(http_exception)],
    authentication_service_: Annotated[
        IAuthenticationService, Depends(authentication_service)
    ],
):
    try:
        token = await authentication_service_.authenticate_user(
            username, password
        )
    except AuthenticationException:
        raise http_exception_
    return token


@router.get("/users/me/")
async def get_current_user(
    user: Annotated[User, Depends(AuthenticatedUser())]
):
    return user
