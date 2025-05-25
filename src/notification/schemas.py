from typing import Literal

from pydantic import BaseModel


class FriendRequestPayload(BaseModel):
    inviter_id: str
    invitee_id: str


class FriendResponsePayload(FriendRequestPayload):
    response: Literal["ACCEPTED"]


class FriendEventDTO(BaseModel):
    event: Literal["friend_request", "friend_response"]
    data: FriendRequestPayload | FriendResponsePayload


class LobbyInvitePayload(BaseModel):
    inviter_id: str
    invitee_id: str
    lobby_id: str


class LobbyEventDTO(BaseModel):
    event: Literal["lobby_invite"]
    data: LobbyInvitePayload
