from typing import Generic, TypeVar

from pydantic import BaseModel

S = TypeVar("S", bound=BaseModel)


class ResponseDTO(BaseModel, Generic[S]):
    data: S | list[S]


class ErrorResponseDTO(BaseModel, Generic[S]):
    error: S


class PydanticErrorResponseDTO(BaseModel):
    field: str
    message: str


class MessageErrorResponseDTO(BaseModel):
    message: str


class PaginationDTO(BaseModel, Generic[S]):
    page_count: int
    total_count: int
    data: list[S]
