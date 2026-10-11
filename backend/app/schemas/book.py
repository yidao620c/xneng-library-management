from datetime import datetime

from pydantic import BaseModel, Field


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(default="", max_length=100)
    isbn: str = Field(min_length=1, max_length=20)
    publisher: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=5000)
    categoryId: int | None = None
    tags: str = Field(default="", max_length=255)
    totalCopies: int = Field(default=1, ge=1, le=999)
    availableCopies: int = Field(default=1, ge=0, le=999)


class BookUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(default="", max_length=100)
    isbn: str = Field(min_length=1, max_length=20)
    publisher: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=5000)
    categoryId: int | None = None
    tags: str = Field(default="", max_length=255)
    totalCopies: int = Field(ge=1, le=999)
    availableCopies: int = Field(ge=0, le=999)


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    publisher: str
    description: str
    categoryId: int | None
    categoryName: str | None
    cover: str | None
    tags: list[str]
    totalCopies: int
    availableCopies: int
    ratingAvg: float
    ratingCount: int
    createdAt: datetime

    model_config = {"from_attributes": True}


class CoverOut(BaseModel):
    cover: str
