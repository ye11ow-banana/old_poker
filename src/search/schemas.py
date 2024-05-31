from pydantic import BaseModel


class UserSearchDTO(BaseModel):
    username: str
