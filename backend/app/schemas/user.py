from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["admin", "user", "vip"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    username: str
    nickname: str
    email: str
    phone: str
    avatar: str | None
    role: Role
    isActive: bool = Field(default=True, validation_alias="is_active")
    createdAt: datetime = Field(validation_alias="created_at")


class ProfileUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)
    email: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=20)


class RoleUpdate(BaseModel):
    role: Role


class StatusUpdate(BaseModel):
    isActive: bool
