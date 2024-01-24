from fastapi import APIRouter, status
from pydantic import ValidationError

from auth.dependencies import (
    AuthenticatedUserDep,
    UOWDep,
    http_exception_401_dep,
    request_data_dep,
)
from auth.exceptions import AuthenticationException, RegistrationException
from auth.schemas import UserInCreate
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from utils import PydanticConvertor, create_http_exception, create_response

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


@router.get("/users/me")
async def get_current_user(user: AuthenticatedUserDep):
    return create_response(user=user)


@router.post("/registration", status_code=status.HTTP_201_CREATED)
async def register_user(data: request_data_dep, uow: UOWDep):
    try:
        user = UserInCreate(**data)
    except ValidationError as e:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            errors=PydanticConvertor().convert_errors(e),
        )
    try:
        new_user = await RegistrationService(uow).register_user(user)
    except RegistrationException as e:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            errors=[dict(field="all", message=str(e))],
        )
    return create_response(user=new_user)
