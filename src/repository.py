from abc import ABC, abstractmethod

from sqlalchemy import select

from database import Base, async_session_maker


class IRepository(ABC):
    @abstractmethod
    async def get(self, field: str, value: str | int):
        raise NotImplementedError


class SQLAlchemyRepository(IRepository):
    model: Base | None = None

    async def get(self, field: str, value: str | int):
        if not self.model:
            raise NotImplementedError(
                "Model not defined in SQLAlchemyRepository"
            )
        async with async_session_maker() as session:
            stmt = select(self.model).where(
                getattr(self.model, field) == value
            )
            res = await session.execute(stmt)
            return res.scalar_one()
