"""
Database utilities for SQLite user management.
"""
import os
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Text, select, JSON, Integer

from api.auth_models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fitness_rag.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class UserDB(Base):
    """Database model for users."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Registration and Profile Fields
    picture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # User Preferences (stored as JSON)
    fitness_goals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    preferred_workout_types: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    workout_frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    available_equipment: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    dietary_restrictions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String, default="en")
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Registration Status
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    preferences_set: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # User Statistics
    total_queries: Mapped[int] = mapped_column(Integer, default=0)
    queries_this_month: Mapped[int] = mapped_column(Integer, default=0)
    favorite_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


async def init_db():
    """Initialize the database by creating tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_user_db(user_data: dict) -> UserDB:
    """Create a new user in the database."""
    async with async_session() as session:
        db_user = UserDB(**user_data)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user


def hash_password(password: str) -> str:
    """Hash a password using argon2 or bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def create_user_from_registration(registration_data: dict) -> UserDB:
    """Create a new user from registration data."""
    # Generate a unique ID for the user
    import uuid
    user_id = str(uuid.uuid4())

    user_data = {
        'id': user_id,
        'email': registration_data['email'],
        'name': registration_data['name'],
        'hashed_password': hash_password(registration_data['password']),
    }

    # Add profile data if provided (only include fields that exist in UserDB)
    if registration_data.get('profile') and hasattr(registration_data['profile'], 'dict'):
        profile_data = registration_data['profile'].dict(exclude_unset=True)
        # Filter to only include fields that exist in UserDB
        valid_profile_fields = {'bio', 'location', 'website', 'picture'}
        filtered_profile_data = {k: v for k, v in profile_data.items() if k in valid_profile_fields}
        user_data.update(filtered_profile_data)

    # Add preferences data if provided
    if registration_data.get('preferences') and hasattr(registration_data['preferences'], 'dict'):
        preferences_data = registration_data['preferences'].dict(exclude_unset=True)
        user_data.update(preferences_data)

    return await create_user_db(user_data)


async def get_user_by_email_for_auth(email: str) -> Optional[UserDB]:
    """Get user by email for authentication purposes."""
    async with async_session() as session:
        result = await session.execute(select(UserDB).where(UserDB.email == email))
        return result.scalar_one_or_none()


async def get_user_by_email(email: str) -> Optional[UserDB]:
    """Get user by email."""
    async with async_session() as session:
        result = await session.execute(select(UserDB).where(UserDB.email == email))
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: str) -> Optional[UserDB]:
    """Get user by ID."""
    async with async_session() as session:
        result = await session.get(UserDB, user_id)
        return result


async def update_user(user_id: str, update_data: dict) -> Optional[UserDB]:
    """Update user information."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            return user
        return None


async def delete_user(user_id: str) -> bool:
    """Delete a user from the database."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False


async def list_users(limit: int = 100, offset: int = 0) -> List[UserDB]:
    """List users with pagination."""
    async with async_session() as session:
        result = await session.execute(select(UserDB).offset(offset).limit(limit))
        return result.scalars().all()


async def update_user_profile(user_id: str, profile_data: dict) -> Optional[UserDB]:
    """Update user profile information."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            # Filter to only include fields that exist in UserDB
            valid_profile_fields = {'name', 'bio'}
            filtered_profile_data = {k: v for k, v in profile_data.items()
                                   if k in valid_profile_fields and v is not None}

            for key, value in filtered_profile_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            return user
        return None


async def update_user_preferences(user_id: str, preferences_data: dict) -> Optional[UserDB]:
    """Update user preferences."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            for key, value in preferences_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            user.preferences_set = True
            await session.commit()
            await session.refresh(user)
            return user
        return None


async def complete_user_registration(user_id: str) -> Optional[UserDB]:
    """Mark user registration as completed."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            user.is_registered = True
            user.registration_date = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            return user
        return None


async def get_user_stats(user_id: str) -> Optional[dict]:
    """Get user statistics."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            return {
                "total_queries": user.total_queries,
                "queries_this_month": user.queries_this_month,
                "favorite_topics": user.favorite_topics or [],
                "last_activity": user.last_activity,
                "account_created": user.created_at,
                "registration_completed": user.is_registered
            }
        return None


async def update_user_stats(user_id: str, stats_data: dict) -> Optional[UserDB]:
    """Update user statistics."""
    async with async_session() as session:
        user = await session.get(UserDB, user_id)
        if user:
            for key, value in stats_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            user.last_activity = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            return user
        return None


def user_db_to_model(db_user: UserDB) -> User:
    """Convert database user model to Pydantic model."""
    return User(
        id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


def user_db_to_profile_response(db_user: UserDB) -> dict:
    """Convert database user model to profile response with preferences and registration status."""
    from api.auth_models import UserPreferences, RegistrationStatus

    preferences = UserPreferences(
        fitness_goals=db_user.fitness_goals,
        experience_level=db_user.experience_level,
        preferred_workout_types=db_user.preferred_workout_types,
        workout_frequency=db_user.workout_frequency,
        available_equipment=db_user.available_equipment,
        dietary_restrictions=db_user.dietary_restrictions,
        notifications_enabled=db_user.notifications_enabled,
        email_updates=db_user.email_updates,
        language=db_user.language,
        timezone=db_user.timezone
    )

    registration_status = RegistrationStatus(
        is_registered=db_user.is_registered,
        profile_completed=db_user.profile_completed,
        preferences_set=db_user.preferences_set,
        email_verified=True,
        registration_date=db_user.registration_date,
        last_updated=db_user.updated_at
    )

    return {
        "user": User(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        ),
        "preferences": preferences,
        "registration_status": registration_status
    }
