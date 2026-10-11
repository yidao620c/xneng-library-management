from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BorrowIn(BaseModel):
    bookId: int


class BorrowBookBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    cover: str | None


class BorrowUserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str


class BorrowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    userId: int = Field(validation_alias="user_id")
    user: BorrowUserBrief
    bookId: int = Field(validation_alias="book_id")
    book: BorrowBookBrief
    status: str
    overdue: bool = False
    borrowedAt: datetime = Field(validation_alias="borrowed_at")
    dueDate: datetime = Field(validation_alias="due_date")
    returnedAt: datetime | None = Field(default=None, validation_alias="returned_at")
    remindedAt: datetime | None = Field(default=None, validation_alias="reminded_at")
