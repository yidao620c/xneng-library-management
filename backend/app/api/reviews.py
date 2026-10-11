from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..db.database import get_db
from ..models import Book, Review, User
from ..schemas.common import Page
from ..schemas.review import ReviewIn, ReviewOut

router = APIRouter(tags=["评论"])


@router.get("/books/{book_id}/reviews", response_model=Page[ReviewOut])
def list_reviews(
    book_id: int,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    query = db.query(Review).filter(Review.book_id == book_id)
    total = query.count()
    reviews = (
        query.order_by(Review.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    items = [ReviewOut.model_validate(r) for r in reviews]
    return Page(items=items, total=total, page=page, size=size)


@router.post("/books/{book_id}/reviews", response_model=ReviewOut)
def create_review(
    book_id: int,
    data: ReviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    content = data.content.strip()
    if len(content) <= 5:
        raise HTTPException(status_code=400, detail="评论内容必须大于 5 个字")
    review = Review(book_id=book_id, user_id=user.id, rating=data.rating, content=content)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    if review.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能删除自己的评论")
    db.delete(review)
    db.commit()
    return {"detail": "评论已删除"}
