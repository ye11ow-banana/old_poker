from typing import Annotated

from fastapi import Depends, status, WebSocketException
from fastapi.websockets import WebSocket

from auth.exceptions import AuthenticationException
from auth.schemas import UserInfo
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
    ) -> UserInfo:
        try:
            token = websocket.query_params["token"]
        except KeyError:
            raise ws_exception
        try:
            user = await JWTAuthenticationService(uow).get_current_user(token)
        except AuthenticationException:
            raise ws_exception
        return user


WSAuthenticatedUserDep = Annotated[UserInfo, Depends(_WSAuthenticatedUser())]
