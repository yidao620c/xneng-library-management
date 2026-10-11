from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.deps import get_current_admin
from ..db.database import get_db
from ..models import Book, Category, User
from ..schemas.category import CategoryIn, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["分类"])


def _out(db: Session, category: Category) -> CategoryOut:
    count = db.query(func.count(Book.id)).filter(Book.category_id == category.id).scalar() or 0
    out = CategoryOut.model_validate(category)
    out.bookCount = count
    return out


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.created_at.asc()).all()
    return [_out(db, c) for c in categories]


@router.post("", response_model=CategoryOut)
def create_category(
    data: CategoryIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    exists = db.query(Category).filter(Category.name == data.name.strip()).first()
    if exists:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    category = Category(name=data.name.strip(), description=data.description.strip())
    db.add(category)
    db.commit()
    db.refresh(category)
    return _out(db, category)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    name = data.name.strip()
    dup = db.query(Category).filter(Category.name == name, Category.id != category_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    category.name = name
    category.description = data.description.strip()
    db.commit()
    db.refresh(category)
    return _out(db, category)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    count = db.query(func.count(Book.id)).filter(Book.category_id == category_id).scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下还有 {count} 本图书，无法删除")
    db.delete(category)
    db.commit()
    return {"detail": "分类已删除"}
