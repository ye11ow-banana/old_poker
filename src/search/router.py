from fastapi import APIRouter

from auth.dependencies import AuthenticatedUserDep
from auth.schemas import UserInfoDTO
from dependencies import UOWDep, PaginationDep
from schemas import ResponseDTO, PaginationDTO
from search.dependencies import UserSearchParamsDep
from search.services import UserSearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/users")
async def search_users(
    _: AuthenticatedUserDep,
    uow: UOWDep,
    search_params: UserSearchParamsDep,
    pagination: PaginationDep,
) -> ResponseDTO[PaginationDTO[UserInfoDTO]]:
    result = await UserSearchService(uow, pagination).paginated_search(
        search_params
    )
    return ResponseDTO[PaginationDTO[UserInfoDTO]](data=result)
