from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from auth.schemas import UserInfoDTO, UserIdDTO


class GameInviteDTO(BaseModel):
    lobby_id: UUID
    user: UserInfoDTO


class NotificationDTO(BaseModel):
    type: Literal["friend_request", "game_invite"]
    data: list[UserInfoDTO] | UserInfoDTO | GameInviteDTO


class UserIdFriendshipAnswerDTO(UserIdDTO):
    status: Literal["accept", "decline"]


class FriendNotificationDTO(BaseModel):
    type: Literal["friend_request", "friend_request_response"]
    data: UserIdFriendshipAnswerDTO | UserIdDTO
