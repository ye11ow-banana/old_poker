from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInLogin(BaseModel):
    username: str
    hashed_password: str


class UserInfo(BaseModel):
    id: UUID
    username: str

    class Config:
        from_attributes = True
        from_attributes: bool = True


class UserInDB(BaseModel):
    id: UUID | None = None
    username: str | None = None
    hashed_password: str | None = None

    class Config:
        from_attributes: bool = True

    def to_user_info(self) -> UserInfo:
        return UserInfo(**self.model_dump())

    def to_user_in_login(self) -> UserInLogin:
        return UserInLogin(**self.model_dump())
