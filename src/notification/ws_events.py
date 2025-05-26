from uuid import UUID

from pydantic import ValidationError

from auth.services.friend import M2MFriendService
from managers import notification_ws_manager
from notification.schemas import (
    FriendRequestPayloadDTO,
    FriendResponsePayloadDTO,
    FriendEventDTO, LobbyInvitePayloadDTO, LobbyEventDTO,
)
from schemas import ErrorEventDTO
from unitofwork import IUnitOfWork


async def lobby_invite(
    ws_manager: notification_ws_manager, user_id: UUID, payload: dict, *args, **kwargs
):
    try:
        data = LobbyInvitePayloadDTO(**payload | {"inviter_id": user_id})
    except ValidationError:
        await ws_manager.send_to_user(
            user_id,
            ErrorEventDTO(
                event="error", data={"message": "Invalid invite payload"}
            ),
        )
    else:
        await ws_manager.send_to_user(
            data.invitee_id, LobbyEventDTO(event="lobby_invite", data=data)
        )


async def friend_request(
    ws_manager: notification_ws_manager, user_id: UUID, payload: dict, *args, **kwargs
) -> None:
    try:
        data = FriendRequestPayloadDTO(**payload | {"inviter_id": user_id})
    except ValidationError:
        await ws_manager.send_to_user(
            user_id,
            ErrorEventDTO(
                event="error",
                data={"message": "Invalid friend request payload"},
            ),
        )
    else:
        await ws_manager.send_to_user(
            data.invitee_id, FriendEventDTO(event="friend_request", data=data)
        )


async def friend_response(
    ws_manager: notification_ws_manager, user_id: UUID, payload: dict, uow: IUnitOfWork
):
    try:
        data = FriendResponsePayloadDTO(**payload | {"invitee_id": user_id})
    except ValidationError:
        await ws_manager.send_to_user(
            user_id,
            ErrorEventDTO(
                event="error",
                data={"message": "Invalid friend response payload"},
            ),
        )
    else:
        await M2MFriendService(uow).process_friend_request(data)
        await ws_manager.send_to_user(
            data.inviter_id, FriendEventDTO(event="friend_response", data=data)
        )


EVENT_MAP = {
    "lobby_invite": lobby_invite,
    "friend_request": friend_request,
    "friend_response": friend_response,
}
