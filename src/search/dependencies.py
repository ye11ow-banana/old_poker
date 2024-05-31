from typing import Annotated

from fastapi import Depends

from search.schemas import UserSearchDTO


class _UserSearch:
    async def __call__(self, username: str) -> UserSearchDTO:
        return UserSearchDTO(username=username)


UserSearchParamsDep = Annotated[UserSearchDTO, Depends(_UserSearch())]
