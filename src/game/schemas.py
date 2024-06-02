from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


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
