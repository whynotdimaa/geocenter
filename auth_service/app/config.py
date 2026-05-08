from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # База даних
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123@localhost:5432/geocenter_auth"

    # JWT
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = Settings()
