from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


class GameInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    players: list[UserInfoDTO]
    created_at: datetime


class CardDTO(BaseModel):
    suit: Literal["H", "D", "C", "S"]
    value: int

    model_config = ConfigDict(frozen=True)


class UserCardDTO(CardDTO):
    id: UUID
    user_id: UUID
    entry_id: UUID | None = None

    model_config = ConfigDict(frozen=True)


class RoundInfoDTO(BaseModel):
    id: UUID
    trump_suit: Literal["H", "D", "C", "S"] | None = None
    trump_value: int | None = None
    round_name: str
    round_number: int | None = None
    is_current_round: bool = False
    dealer_id: UUID
    opening_player_id: UUID


class UserCardListDTO(UserInfoDTO):
    cards: list[CardDTO]


class FullCardInfoDTO(BaseModel):
    id: UUID
    suit: Literal["H", "D", "C", "S"]
    value: int
    user_id: UUID
    entry_id: UUID | None = None


class FullUserCardInfoDTO(UserInfoDTO):
    bid: int | None = None
    actual_bid: int | None = None
    score: int | None = None
    cards: list[FullCardInfoDTO]


class FlattenFullGameCardInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: UUID
    user_id: UUID
    username: str
    email: str
    elo: int
    created_at: datetime
    card_id: UUID
    suit: Literal["H", "D", "C", "S"]
    value: int
    entry_id: UUID | None = None
    trump_suit: Literal["H", "D", "C", "S"] | None = None
    trump_value: int | None = None
    opening_player_id: UUID
    bid: int | None = None
    actual_bid: int | None = None
    score: int | None = None


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


class GameIdPayloadDTO(BaseModel):
    id: UUID


class GameStartEventDTO(BaseModel):
    event: Literal["game_start"]
    data: GameIdPayloadDTO


class FullGameCardInfoEventDTO(BaseModel):
    event: Literal["full_game_card_info", "game_is_finished"]
    data: FullGameCardInfoDTO


class NewWatcherEventDTO(BaseModel):
    event: Literal["new_watcher"]
    data: list[UserInfoDTO]


class BidEventDTO(BaseModel):
    event: Literal["bid"]
    data: dict[str, UUID | int]
