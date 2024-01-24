import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInLogin(BaseModel):
    username: str
    hashed_password: str


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


class UserInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    username: str | None = None
    hashed_password: str | None = None

    def to_user_info(self) -> UserInfo:
        return UserInfo(**self.model_dump())

    def to_user_in_login(self) -> UserInLogin:
        return UserInLogin(**self.model_dump())


class UserInCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6)
    repeat_password: str

    @field_validator("username")
    def username_has_no_invalid_symbols(cls, username: str) -> str:
        match = re.search(r"^[a-zA-Z0-9_-]+$", username)
        if match is None:
            raise ValueError("Username has invalid symbols")
        return username

    @field_validator("repeat_password")
    def check_passwords_match(
        cls, repeat_password: str, info: ValidationInfo
    ) -> str:
        if repeat_password != info.data.get("password", ""):
            raise ValueError("Passwords do not match")
        return repeat_password
