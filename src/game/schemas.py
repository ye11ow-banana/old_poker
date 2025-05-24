from datetime import datetime
from typing import Literal
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


class CardDTO(BaseModel):
    suit: Literal["H", "D", "C", "S"]
    value: int

    model_config = ConfigDict(frozen=True)


class UserCardListDTO(UserInfoDTO):
    cards: list[CardDTO]


class FullCardInfoDTO(BaseModel):
    id: UUID
    suit: Literal["H", "D", "C", "S"]
    value: int
    user_id: UUID
    entry_id: UUID | None = None


class FullUserCardInfoDTO(UserInfoDTO):
    cards: list[FullCardInfoDTO]


class FlattenFullGameCardInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: UUID
    user_id: UUID
    username: str
    card_id: UUID
    suit: Literal["H", "D", "C", "S"]
    value: int
    entry_id: UUID | None = None
    trump_suit: Literal["H", "D", "C", "S"] | None = None
    trump_value: int | None = None
    opening_player_id: UUID


class FullEntryCardInfoDTO(BaseModel):
    id: UUID
    cards: list[FullCardInfoDTO]


class FullGameCardInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: UUID
    users: list[FullUserCardInfoDTO]
    entry: FullEntryCardInfoDTO | None = None
    trump_suit: Literal["H", "D", "C", "S"] | None = None
    trump_value: int | None = None


class ProcessCardDTO(BaseModel):
    card_id: UUID
    owner_id: UUID
    round_id: UUID
    is_round_end: bool = False


class EntryIdDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class InvitePayload(BaseModel):
    inviter_id: str
    invitee_id: str
    lobby_id: str


class ReadyPayload(BaseModel):
    user_id: str
    lobby_id: str


class StartPayload(BaseModel):
    game_id: str
    lobby_id: str


class LobbyEventDTO(BaseModel):
    event: Literal["invite", "ready", "start"]
    data: dict
