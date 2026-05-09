from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import User, UserProfile, RefreshToken
from app.schemas import (
    RegisterRequest, LoginRequest,
    TokenResponse, RefreshRequest, AccessTokenResponse,
)
from app.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Реєстрація нового користувача.
    Автоматично створює UserProfile і повертає пару токенів.
    """
    # Перевірка унікальності email
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email вже зареєстрований")

    # Перевірка унікальності username
    existing_u = await db.execute(select(User).where(User.username == data.username))
    if existing_u.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Імʼя користувача вже зайняте")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()  # отримуємо user.id без commit

    # Авто-створення профілю
    profile = UserProfile(user_id=user.id)
    db.add(profile)

    # Інвалідуємо старі refresh токени цього юзера (щоб уникнути дублікатів)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )

    # Генеруємо токени
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    # Зберігаємо refresh токен в БД
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token=refresh, expires_at=expires))

    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Логін за email + password. Повертає access та refresh токени.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний email або пароль",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Акаунт деактивовано")

    # Інвалідуємо старі refresh токени цього юзера
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token=refresh, expires_at=expires))
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Оновлення access токена за допомогою refresh токена.
    Старий refresh токен інвалідується, новий access видається.
    """
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Очікується refresh токен")

    # Перевіряємо що токен не відкликаний
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == data.refresh_token,
            RefreshToken.is_revoked == False,
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=401, detail="Токен відкликаний або не існує")

    user_id = int(payload["sub"])
    new_access = create_access_token({"sub": str(user_id)})

    return AccessTokenResponse(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Логаут — відкликає refresh токен.
    """
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        await db.commit()


@router.post("/verify", response_model=dict)
async def verify_token(credentials: dict, db: AsyncSession = Depends(get_db)):
    """
    Внутрішній ендпоінт для інших сервісів — верифікує access токен
    і повертає дані юзера. Викликається через API Gateway.
    """
    token = credentials.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Токен не надано")

    payload = decode_token(token)
    user_id = int(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Користувача не знайдено")

    return {"id": user.id, "email": user.email, "username": user.username}
