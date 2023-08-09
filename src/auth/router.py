from fastapi import APIRouter

from auth.dependencies import AuthenticatedUserDep, UOWDep, http_exception_dep
from auth.exceptions import AuthenticationException
from auth.services.authentication import JWTAuthenticationService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    username: str,
    password: str,
    uow: UOWDep,
    http_exception: http_exception_dep,
):
    try:
        token = await JWTAuthenticationService(uow).authenticate_user(
            username, password
        )
    except AuthenticationException:
        raise http_exception
    return token


@router.get("/users/me/")
async def get_current_user(user: AuthenticatedUserDep):
    return user
