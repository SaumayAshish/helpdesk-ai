"""
Authentication endpoints: register, login, refresh, me, change-password.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.deps import get_auth_service, get_current_active_user
from backend.core.config import settings
from backend.core.rate_limit import limiter
from backend.models.user import User
from backend.schemas.token import RefreshTokenRequest, TokenResponse
from backend.schemas.user import (
    PasswordChangeRequest,
    UserRegister,
    UserResponse,
)
from backend.services.auth_service import AuthService

router = APIRouter()


# =====================================================
# POST /auth/register
# =====================================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new account with the default 'employee' role. "
    f"Rate limited to {settings.RATE_LIMIT_REGISTER} per client IP.",
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(
    request: Request,
    payload: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = auth_service.register(payload)
    return UserResponse.from_orm_user(user)


# =====================================================
# POST /auth/login
# =====================================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    description=(
        "OAuth2-compatible login endpoint. "
        "Submit form fields: `username` (use email) and `password`. "
        "Returns an access token and a refresh token. "
        f"Rate limited to {settings.RATE_LIMIT_LOGIN} per client IP to slow "
        "down credential-stuffing / brute-force attempts."
    ),
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Note: We use email as the 'username' field for OAuth2 compatibility.
    The Swagger 'Authorize' button uses this exact contract.
    """
    user = auth_service.authenticate(form_data.username, form_data.password)
    return auth_service.issue_tokens(user)


# =====================================================
# POST /auth/refresh
# =====================================================
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.refresh_access_token(payload.refresh_token)


# =====================================================
# GET /auth/me
# =====================================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Returns profile of the authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.from_orm_user(current_user)


# =====================================================
# POST /auth/change-password
# =====================================================
@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change own password",
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    auth_service.change_password(
        current_user,
        payload.current_password,
        payload.new_password,
    )
    return None
