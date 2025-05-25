from fastapi import APIRouter

from auth.schemas import UserInfoDTO
from dependencies import PaginationDep, UOWDep, AuthenticatedUserDep
from schemas import PaginationDTO, ResponseDTO
from search.dependencies import UserSearchParamsDep
from search.services import UserSearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/users")
async def search_users(
    user: AuthenticatedUserDep,
    uow: UOWDep,
    search_params: UserSearchParamsDep,
    pagination: PaginationDep,
) -> ResponseDTO[PaginationDTO[UserInfoDTO]]:
    result = await UserSearchService(uow, pagination).paginated_search(
        search_params, current_user=user
    )
    return ResponseDTO[PaginationDTO[UserInfoDTO]](data=result)
