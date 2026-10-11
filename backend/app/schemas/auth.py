from pydantic import BaseModel, Field

from .user import UserOut


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=20)


class LoginIn(BaseModel):
    username: str
    password: str


class RefreshIn(BaseModel):
    refreshToken: str


class TokenOut(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int
    user: UserOut
