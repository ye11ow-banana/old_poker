from typing import Generic, TypeVar

from pydantic import BaseModel

S = TypeVar("S", bound=BaseModel)


class Response(BaseModel, Generic[S]):
    data: S


class ErrorResponse(BaseModel, Generic[S]):
    error: S


class PydanticErrorResponse(BaseModel):
    field: str
    message: str


class MessageErrorResponse(BaseModel):
    message: str
