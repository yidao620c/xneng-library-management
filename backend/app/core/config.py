import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    APP_NAME: str = "图书管理系统 API"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-9f2c1a7b")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    AVATAR_DIR: Path = UPLOAD_DIR / "avatars"
    COVER_DIR: Path = UPLOAD_DIR / "covers"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR.as_posix()}/library.db"

    MAX_AVATAR_SIZE: int = 100 * 1024  # 100K
    MAX_COVER_SIZE: int = 2 * 1024 * 1024  # 2M
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # 借阅规则
    LOAN_DAYS: int = 14
    MAX_ACTIVE_BORROWS: dict[str, int] = {"admin": 20, "vip": 10, "user": 5}

    def ensure_dirs(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        self.COVER_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
