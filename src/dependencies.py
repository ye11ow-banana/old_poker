from typing import Annotated

from fastapi import Depends

from unitofwork import IUnitOfWork, UnitOfWork
from utils import Pagination

UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]


class _Pagination:
    async def __call__(self, page: int = 1) -> Pagination:
        return Pagination(page=page)


PaginationDep = Annotated[Pagination, Depends(_Pagination())]
