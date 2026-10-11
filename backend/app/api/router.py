from fastapi import APIRouter

from . import auth, books, borrows, categories, messages, reviews, stats, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(books.router)
api_router.include_router(reviews.router)
api_router.include_router(borrows.router)
api_router.include_router(messages.router)
api_router.include_router(stats.router)
