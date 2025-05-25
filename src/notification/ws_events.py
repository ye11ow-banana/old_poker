from pydantic import ValidationError

from auth.services.friend import M2MFriendService
from managers import WSConnectionManager
from notification.schemas import (
    FriendRequestPayload,
    FriendResponsePayload,
    FriendEventDTO, LobbyInvitePayload, LobbyEventDTO,
)
from schemas import ErrorEventDTO
from unitofwork import IUnitOfWork


async def lobby_invite(
    ws_manager: WSConnectionManager, user_id: str, payload: dict, *args, **kwargs
):
    try:
        data = LobbyInvitePayload(**payload | {"inviter_id": user_id})
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
    ws_manager: WSConnectionManager, user_id: str, payload: dict, *args, **kwargs
) -> None:
    try:
        data = FriendRequestPayload(**payload | {"inviter_id": user_id})
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
    ws_manager: WSConnectionManager, user_id: str, payload: dict, uow: IUnitOfWork
):
    try:
        data = FriendResponsePayload(**payload | {"invitee_id": user_id})
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
