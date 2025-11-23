from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

# Import database utilities
from api.database import get_user_by_id, get_user_by_email_for_auth, verify_password, user_db_to_model


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime


# Use HTTP Bearer for JWT tokens
security = HTTPBearer()

app = FastAPI()


async def get_user(user_id: str):
    """Get user from database by ID."""
    db_user = await get_user_by_id(user_id)
    if db_user:
        return user_db_to_model(db_user)
    return None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password."""
    user = await get_user_by_email_for_auth(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user