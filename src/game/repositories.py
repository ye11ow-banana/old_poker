from typing import Sequence
from uuid import UUID

from game import models
from game.schemas import LobbyInfoDTO, LobbyIdDTO
from repository import SQLAlchemyRepository


class LobbyRepository(SQLAlchemyRepository):
    model = models.Lobby

    async def get_last_or_create(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> LobbyIdDTO:
        return LobbyIdDTO.model_validate(
            await super().get_last_or_create(returns=returns, **data)
        )

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> LobbyInfoDTO:
        return LobbyInfoDTO.model_validate(
            await super().get(returns=returns, **data)
        )

    async def remove_user(self, user_id: UUID) -> None:
        pass
