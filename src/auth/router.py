from fastapi import APIRouter, status, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect

from auth.dependencies import (
    AuthenticatedUserDep,
    UOWDep,
    http_exception_401_dep,
)
from auth.exceptions import AuthenticationException, RegistrationException
from auth.schemas import (
    UserInCreateDTO,
    UserInLoginDTO,
    TokenDTO,
    UserInfoDTO,
    UserIdDTO,
)
from auth.services.authentication import JWTAuthenticationService
from auth.services.friend import M2MFriendService
from auth.services.registration import RegistrationService
from game.dependencies import WSAuthenticatedUserDep
from game.schemas import LobbyInfoDTO
from game.services.lobby import LobbyService
from managers import ws_manager
from notification.schemas import (
    NotificationDTO,
    FriendNotificationDTO,
    GameInviteDTO,
)
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


@router.websocket("/ws/friends/add")
async def add_friend(
    websocket: WebSocket, user: WSAuthenticatedUserDep, uow: UOWDep
) -> None:
    """
    Websocket endpoint for adding friends.

    When a user sends a friend request, the server sends a notification to the recipient.
    The recipient can accept or reject the request.
    """
    await ws_manager.connect(websocket, user.id)
    friend_service = M2MFriendService(uow)
    requests = await friend_service.get_friend_requests(user)
    await ws_manager.send(
        user.id,
        ResponseDTO[NotificationDTO](
            data=NotificationDTO(type="friend_request", data=requests)
        ),
    )
    try:
        while True:
            data = await websocket.receive_json()
            dto = FriendNotificationDTO(**data)
            await friend_service.process_friend_request(user, dto)
            if dto.type == "friend_request_response":
                continue
            await ws_manager.send(
                dto.data.id,
                ResponseDTO[NotificationDTO](
                    data=NotificationDTO(type=dto.type, data=user)
                ),
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id)


@router.websocket("/ws/friends/invite")
async def invite_friend(
    websocket: WebSocket, user: WSAuthenticatedUserDep, uow: UOWDep
) -> None:
    await ws_manager.connect(websocket, user.id)
    try:
        while True:
            data = await websocket.receive_json()
            dto = UserIdDTO(**data)
            lobby = await LobbyService(uow).get_or_create_lobby(user)
            await ws_manager.send(
                dto.id,
                ResponseDTO[NotificationDTO](
                    data=NotificationDTO(
                        type="game_invite",
                        data=GameInviteDTO(lobby_id=lobby.id, user=user),
                    )
                ),
            )
            await ws_manager.send(
                user.id,
                ResponseDTO[LobbyInfoDTO](
                    data=LobbyInfoDTO(id=lobby.id, leader_id=user.id)
                ),
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id)
