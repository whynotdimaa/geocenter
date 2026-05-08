from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, UserProfile
from app.schemas import UserResponse, UpdateProfileRequest, ChangePasswordRequest, InternalUserResponse
from app.security import get_current_user_id, hash_password, verify_password

router = APIRouter()


async def get_user_or_404(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return user


async def get_profile(user_id: int, db: AsyncSession) -> UserProfile | None:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/users/me
    Повертає дані поточного авторизованого користувача з профілем.
    """
    user = await get_user_or_404(user_id, db)
    profile = await get_profile(user_id, db)

    response = UserResponse.model_validate(user)
    if profile:
        response.profile = profile
    return response


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UpdateProfileRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    PATCH /api/users/me
    Оновлення username, bio та налаштувань профілю.
    """
    user = await get_user_or_404(user_id, db)

    if data.username is not None:
        # Перевіряємо унікальність нового username
        existing = await db.execute(
            select(User).where(User.username == data.username, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Імʼя вже зайняте")
        user.username = data.username

    if data.bio is not None:
        user.bio = data.bio

    if data.profile:
        profile = await get_profile(user_id, db)
        if profile:
            if data.profile.language:
                profile.language = data.profile.language
            if data.profile.coord_units:
                profile.coord_units = data.profile.coord_units
            profile.dark_mode = data.profile.dark_mode
        else:
            db.add(UserProfile(
                user_id=user_id,
                language=data.profile.language,
                coord_units=data.profile.coord_units,
                dark_mode=data.profile.dark_mode,
            ))

    await db.commit()
    await db.refresh(user)

    profile = await get_profile(user_id, db)
    response = UserResponse.model_validate(user)
    if profile:
        response.profile = profile
    return response


@router.post("/me/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/users/me/change-password
    Зміна пароля. Потребує старий пароль для підтвердження.
    """
    user = await get_user_or_404(user_id, db)

    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Невірний поточний пароль")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()


@router.get("/internal/{user_id}", response_model=InternalUserResponse)
async def get_user_internal(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    GET /api/users/internal/{user_id}
    Внутрішній ендпоінт для інших мікросервісів.
    Повертає базові дані юзера без авторизації (доступний тільки всередині мережі Docker).
    """
    user = await get_user_or_404(user_id, db)
    return user
