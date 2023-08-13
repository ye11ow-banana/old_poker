from fastapi import APIRouter

from auth.dependencies import AuthenticatedUserDep, UOWDep, http_exception_dep
from auth.exceptions import AuthenticationException
from auth.dependencies import (
    AuthenticatedUserDep,
    UOWDep,
    http_exception_401_dep,
    request_data_dep,
)
from auth.exceptions import AuthenticationException, RegistrationException
from auth.services.authentication import JWTAuthenticationService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    data: request_data_dep,
    uow: UOWDep,
    http_exception: http_exception_401_dep,
):
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    try:
        token = await JWTAuthenticationService(uow).authenticate_user(
            username, password
        )
    except AuthenticationException:
        raise http_exception
    return create_response(token=token)


@router.get("/users/me/")
async def get_current_user(user: AuthenticatedUserDep):
    return user
