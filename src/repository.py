from abc import ABC, abstractmethod
from typing import Sequence, Type

from sqlalchemy import select, func, Row
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base
from utils import Pagination


class IRepository(ABC):
    @abstractmethod
    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> Base:
        raise NotImplementedError

    @abstractmethod
    async def add(self, **insert_data) -> Base:
        raise NotImplementedError


class SQLAlchemyRepository(IRepository):
    model: Type[Base]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> Row[tuple]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = select(*[getattr(self.model, c) for c in returns]).filter_by(
            **data
        )
        res = await self._session.execute(query)
        return res.first()

    async def add(self, **insert_data) -> Base:
        new_model_object = self.model(**insert_data)
        self._session.add(new_model_object)
        await self._session.flush()
        return new_model_object

    async def get_total_count(self, **data: str | int) -> int:
        query = select(func.count())
        for key, value in data.items():
            column = getattr(self.model, key)
            query = query.filter(column.ilike(f"%{value}%"))
        result = await self._session.execute(query)
        return result.scalar()

    async def get_paginated_all(
        self,
        /,
        pagination: Pagination,
        returns: Sequence[str] | None = None,
        **data: str | int,
    ) -> Sequence[Row]:
        if returns is None:
            returns = [c.name for c in self.model.__table__.columns]
        query = select(*[getattr(self.model, c) for c in returns])
        for key, value in data.items():
            column = getattr(self.model, key)
            query = query.filter(column.ilike(f"%{value}%"))
        query = query.offset(pagination.get_offset()).limit(pagination.limit)
        result = await self._session.execute(query)
        return result.fetchall()
