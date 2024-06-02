from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from auth.schemas import UserInfoDTO


class PlayersInSearchCountDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    count: int = Field(
        alias="playersInSearchCount",
        description="Number of players in search of a game",
    )


class LobbyIdDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class LobbyInfoDTO(LobbyIdDTO):
    leader_id: UUID


class LobbyUserInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    is_leader: bool


class GameInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    players: list[UserInfoDTO]
    created_at: datetime
