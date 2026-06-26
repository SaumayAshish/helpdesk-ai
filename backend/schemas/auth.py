"""
Auth request schemas.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Email + password login."""

    email: EmailStr
    password: str = Field(..., min_length=1)
