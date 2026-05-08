from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123@localhost:5432/geocenter_analytics"
    LOCATIONS_SERVICE_URL: str = "http://localhost:8000"
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
