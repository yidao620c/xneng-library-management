from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)
    targetUserId: int | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    title: str
    content: str
    targetUserId: int | None = Field(default=None, validation_alias="target_user_id")
    targetUsername: str | None = None
    isRead: bool = False
    createdAt: datetime = Field(validation_alias="created_at")
