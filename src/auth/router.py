from fastapi import APIRouter, HTTPException, status

from auth.exceptions import AuthenticationException, RegistrationException
from auth.schemas import TokenDTO, UserInCreateDTO, UserInfoDTO, UserInLoginDTO
from auth.services.authentication import JWTAuthenticationService
from auth.services.friend import M2MFriendService
from auth.services.registration import RegistrationService
from dependencies import AuthenticatedUserDep, UOWDep, http_exception_401_dep
from schemas import ResponseDTO

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    user: UserInLoginDTO,
    uow: UOWDep,
    http_exception: http_exception_401_dep,
) -> ResponseDTO[TokenDTO]:
    try:
        token = await JWTAuthenticationService(uow).authenticate_user(user)
    except AuthenticationException:
        raise http_exception
    return ResponseDTO[TokenDTO](data=token)


@router.get("/users/me")
async def get_current_user(
    user: AuthenticatedUserDep,
) -> ResponseDTO[UserInfoDTO]:
    return ResponseDTO[UserInfoDTO](data=user)


@router.post("/registration", status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserInCreateDTO, uow: UOWDep
) -> ResponseDTO[UserInfoDTO]:
    try:
        new_user = await RegistrationService(uow).register_user(user)
    except RegistrationException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[UserInfoDTO](data=new_user)


@router.get("/friends")
async def get_friends(
    user: AuthenticatedUserDep, uow: UOWDep
) -> ResponseDTO[list[UserInfoDTO]]:
    try:
        friends = await M2MFriendService(uow).get_friends(user)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[list[UserInfoDTO]](data=friends)
