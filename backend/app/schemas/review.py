from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewIn(BaseModel):
    rating: int = Field(default=0, ge=0, le=5)
    content: str = Field(min_length=1, max_length=2000)


class ReviewUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    avatar: str | None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    bookId: int = Field(validation_alias="book_id")
    user: ReviewUser
    rating: int
    content: str
    createdAt: datetime = Field(validation_alias="created_at")
