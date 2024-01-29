from fastapi import APIRouter, status, HTTPException

from auth.dependencies import (
    AuthenticatedUserDep,
    UOWDep,
    http_exception_401_dep,
)
from auth.exceptions import AuthenticationException, RegistrationException
from auth.schemas import UserInCreate, UserInLogin, Token, UserInfo
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from schemas import Response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    user: UserInLogin,
    uow: UOWDep,
    http_exception: http_exception_401_dep,
) -> Response[Token]:
    try:
        token = await JWTAuthenticationService(uow).authenticate_user(user)
    except AuthenticationException:
        raise http_exception
    return Response[Token](data=token)


@router.get("/users/me")
async def get_current_user(user: AuthenticatedUserDep) -> Response[UserInfo]:
    return Response[UserInfo](data=user)


@router.post("/registration", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserInCreate, uow: UOWDep) -> Response[UserInfo]:
    try:
        new_user = await RegistrationService(uow).register_user(user)
    except RegistrationException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return Response[UserInfo](data=new_user)
