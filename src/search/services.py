from abc import ABC, abstractmethod

from pydantic import BaseModel

from auth.schemas import UserInfoDTO
from schemas import PaginationDTO
from search.schemas import UserSearchDTO
from unitofwork import IUnitOfWork
from utils import Pagination


class ISearchService(ABC):
    def __init__(self, uow: IUnitOfWork, pagination: Pagination) -> None:
        self._uow: IUnitOfWork = uow
        self._pagination: Pagination = pagination

    @abstractmethod
    async def paginated_search(
        self, filter_obj: BaseModel
    ) -> PaginationDTO[list[BaseModel]]:
        raise NotImplementedError


class UserSearchService(ISearchService):
    async def paginated_search(
        self, filter_obj: UserSearchDTO
    ) -> PaginationDTO[UserInfoDTO]:
        async with self._uow:
            total_count = await self._uow.users.isearch_count(
                username=filter_obj.username
            )
            users = await self._uow.users.get_paginated_all(
                pagination=self._pagination,
                returns=("id", "username"),
                username=filter_obj.username,
            )
        return PaginationDTO[UserInfoDTO](
            page_count=self._pagination.get_page_count(total_count),
            total_count=total_count,
            data=users,
        )
