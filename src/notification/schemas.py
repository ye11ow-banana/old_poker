from typing import Literal

from pydantic import BaseModel


class FriendRequestPayloadDTO(BaseModel):
    inviter_id: str
    invitee_id: str


class FriendResponsePayloadDTO(FriendRequestPayloadDTO):
    response: Literal["ACCEPTED"]


class FriendEventDTO(BaseModel):
    event: Literal["friend_request", "friend_response"]
    data: FriendRequestPayloadDTO | FriendResponsePayloadDTO


class LobbyInvitePayloadDTO(BaseModel):
    inviter_id: str
    invitee_id: str
    lobby_id: str


class LobbyEventDTO(BaseModel):
    event: Literal["lobby_invite"]
    data: LobbyInvitePayloadDTO
