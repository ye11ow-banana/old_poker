from abc import ABC, abstractmethod
from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base


class IRepository(ABC):
    @abstractmethod
    async def get(self, **data: str | int):
        raise NotImplementedError


class SQLAlchemyRepository(IRepository):
    model: Type[Base] | None = None

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, **data: str | int):
        if not self.model:
            raise NotImplementedError(
                "Model not defined in SQLAlchemyRepository"
            )
        stmt = select(self.model).filter_by(**data)
        res = await self._session.execute(stmt)
        return res.scalar_one()
