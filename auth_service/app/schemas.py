from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


# ── Register ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    password2: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль має бути мінімум 8 символів")
        return v

    @field_validator("password2")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Паролі не співпадають")
        return v


# ── Login ─────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Tokens ────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Profile ───────────────────────────────────────────────
class UserProfileSchema(BaseModel):
    language: str = "uk"
    coord_units: str = "decimal"
    dark_mode: bool = False

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    bio: str
    avatar: str | None
    is_email_verified: bool
    created_at: datetime
    profile: UserProfileSchema | None = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    username: str | None = None
    bio: str | None = None
    profile: UserProfileSchema | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    new_password2: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль має бути мінімум 8 символів")
        return v

    @field_validator("new_password2")
    @classmethod
    def new_passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Паролі не співпадають")
        return v


# ── Internal (для інших сервісів) ─────────────────────────
class InternalUserResponse(BaseModel):
    """Спрощена схема для міжсервісної комунікації."""
    id: int
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
