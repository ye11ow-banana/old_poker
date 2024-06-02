from typing import Literal

from pydantic import BaseModel

from auth.schemas import UserInfoDTO, UserIdDTO


class NotificationDTO(BaseModel):
    type: Literal["friend_request"]
    data: list[UserInfoDTO] | UserInfoDTO


class UserIdFriendshipAnswerDTO(UserIdDTO):
    status: Literal["accept", "decline"]


class FriendNotificationDTO(BaseModel):
    type: Literal["friend_request", "friend_request_response"]
    data: UserIdFriendshipAnswerDTO | UserIdDTO
