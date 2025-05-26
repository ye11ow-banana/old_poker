from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class FriendRequestPayloadDTO(BaseModel):
    inviter_id: UUID
    invitee_id: UUID


class FriendResponsePayloadDTO(FriendRequestPayloadDTO):
    response: Literal["ACCEPTED"]


class FriendEventDTO(BaseModel):
    event: Literal["friend_request", "friend_response"]
    data: FriendRequestPayloadDTO | FriendResponsePayloadDTO


class LobbyInvitePayloadDTO(BaseModel):
    inviter_id: UUID
    invitee_id: UUID
    lobby_id: UUID


class LobbyEventDTO(BaseModel):
    event: Literal["lobby_invite"]
    data: LobbyInvitePayloadDTO
