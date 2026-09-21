from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole

PASSWORD_MIN_LENGTH = 10


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)


class UserRegister(UserBase):
    """Public self-registration. Role is deliberately absent: every self-registered
    account is a student. Staff accounts are created by an admin."""

    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("password")
    @classmethod
    def enforce_password_policy(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("Password may not start or end with whitespace")
        if not any(c.isalpha() for c in value):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one number")
        return value


class UserCreateByAdmin(UserRegister):
    role: UserRole = UserRole.STUDENT
    is_active: bool = True


class UserUpdateByAdmin(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)


class UserPublic(BaseModel):
    """Everything a peer student is allowed to see about another user: a display
    name and a role. No email, no phone, no department."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    role: UserRole


class UserOut(UserPublic):
    """Full record. Returned only for the requesting user themselves, or to staff
    who legitimately need to contact the person."""

    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    department: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
