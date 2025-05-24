from typing import Annotated

from fastapi import Depends, status, WebSocketException
from fastapi.websockets import WebSocket

from auth.exceptions import AuthenticationException
from auth.schemas import UserInfoDTO
from auth.services.authentication import JWTAuthenticationService
from dependencies import UOWDep


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
