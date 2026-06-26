"""
Authentication business logic.

Orchestrates: validation, password hashing, token issuance.
Endpoints are thin wrappers around this service.
"""

from loguru import logger
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from backend.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.models.user import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.token import TokenResponse
from backend.schemas.user import UserRegister


class AuthService:
    """Encapsulates authentication workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    # =====================================================
    # Registration
    # =====================================================
    def register(self, data: UserRegister) -> User:
        """
        Register a new user with the default 'employee' role.

        Raises:
            ConflictException: If email or username already taken.
        """
        email = data.email.lower()
        username = data.username.lower()

        if self.user_repo.email_exists(email):
            raise ConflictException(f"Email '{email}' is already registered")
        if self.user_repo.username_exists(username):
            raise ConflictException(f"Username '{username}' is already taken")

        # Default new users to "employee" role
        role = self.user_repo.get_role_by_name("employee")
        if not role:
            raise NotFoundException("Default role 'employee' not configured")

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role_id=role.id,
            department_id=None,
            is_active=True,
        )
        self.user_repo.add(user)
        self.user_repo.commit()
        self.db.refresh(user)

        logger.info(f"New user registered: id={user.id} email={user.email}")
        return user

    # =====================================================
    # Login
    # =====================================================
    def authenticate(self, email: str, password: str) -> User:
        """
        Verify credentials and return the user.

        Raises:
            UnauthorizedException: On invalid credentials or inactive user.
        """
        user = self.user_repo.get_by_email(email.lower())

        # Constant-time response: always run bcrypt even if user not found
        # (prevents timing attacks that reveal which emails exist)
        if not user:
            # Dummy verify to consume similar CPU time
            verify_password(password, "\$2b$12$" + "x" * 53)
            logger.warning(f"Login failed: email not found: {email}")
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: bad password for user_id={user.id}")
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            logger.warning(f"Login blocked: inactive user_id={user.id}")
            raise UnauthorizedException("Account is disabled")

        self.user_repo.update_last_login(user)
        self.user_repo.commit()
        logger.info(f"Login successful: user_id={user.id}")
        return user

    # =====================================================
    # Token issuance
    # =====================================================
    def issue_tokens(self, user: User) -> TokenResponse:
        """Create access + refresh tokens for a user."""
        extra = {"role": user.role.name, "username": user.username}
        access = create_access_token(user.id, extra_claims=extra)
        refresh = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # =====================================================
    # Refresh
    # =====================================================
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new access token from a valid refresh token.

        Raises:
            UnauthorizedException: If refresh token invalid/expired.
        """
        payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        user_id = int(payload["sub"])

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User no longer valid")

        return self.issue_tokens(user)

    # =====================================================
    # Get current user from access token
    # =====================================================
    def get_user_from_token(self, token: str) -> User:
        """Decode access token and load the user."""
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
        user_id = int(payload["sub"])

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled")
        return user
