from abc import ABC, abstractmethod
from typing import Sequence, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base


class IRepository(ABC):
    @abstractmethod
    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> Base:
        raise NotImplementedError


class SQLAlchemyRepository(IRepository):
    model: Type[Base]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> Base:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        stmt = select(*[getattr(self.model, c) for c in returns]).filter_by(
            **data
        )
        res = await self._session.execute(stmt)
        return res.first()

    async def add(self, **insert_data) -> Base:
        new_model_object = self.model(**insert_data)
        self._session.add(new_model_object)
        await self._session.flush()
        return new_model_object
