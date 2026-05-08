import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """
    Верифікує JWT через Auth Service.
    Analytics Service не знає SECRET_KEY — делегує перевірку.
    """
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/api/auth/verify",
                json={"token": token},
                timeout=5.0,
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth Service недоступний",
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = response.json()
    return data["id"]
