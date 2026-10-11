from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base

# 状态: borrowed 借阅中 / returning 归还待确认 / returned 已归还
BORROW_STATUS = ("borrowed", "returning", "returned")


class Borrow(Base):
    __tablename__ = "borrows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="borrowed", index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    reminded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)

    user = relationship("User", lazy="joined")
    book = relationship("Book", lazy="joined")
