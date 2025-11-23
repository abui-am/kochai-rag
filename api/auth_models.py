"""
Authentication models and schemas for email/password authentication.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class User(BaseModel):
    """User model for authenticated users."""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TokenData(BaseModel):
    """Model for JWT token payload data."""
    user_id: str = Field(..., description="User identifier")
    email: EmailStr = Field(..., description="User's email")
    exp: Optional[datetime] = Field(None, description="Token expiration time")


class AccessToken(BaseModel):
    """Model for access token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LoginCredentials(BaseModel):
    """Model for login credentials."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseModel):
    """Response model for login endpoint."""
    message: str = Field(..., description="Login status message")
    user: User = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class AuthError(BaseModel):
    """Model for authentication errors."""
    error: str = Field(..., description="Error type")
    error_description: str = Field(..., description="Detailed error description")


class ValidationError(BaseModel):
    """Model for validation errors."""
    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(..., description="Validation error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Validation details")


# Registration and Profile Management Models
class UserProfileUpdate(BaseModel):
    """Model for updating user profile information."""
    name: Optional[str] = Field(None, description="User's full name")
    picture: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, description="User's bio or description")
    location: Optional[str] = Field(None, description="User's location")
    website: Optional[str] = Field(None, description="User's website URL")


class UserPreferences(BaseModel):
    """Model for user preferences and settings."""
    fitness_goals: Optional[list] = Field(None, description="Fitness goals (e.g., ['muscle_gain', 'weight_loss'])")
    experience_level: Optional[str] = Field(None, description="Fitness experience level (beginner, intermediate, advanced)")
    preferred_workout_types: Optional[list] = Field(None, description="Preferred workout types")
    workout_frequency: Optional[str] = Field(None, description="Workout frequency per week")
    available_equipment: Optional[list] = Field(None, description="Available fitness equipment")
    dietary_restrictions: Optional[list] = Field(None, description="Dietary restrictions or preferences")
    notifications_enabled: bool = Field(default=True, description="Whether to enable notifications")
    email_updates: bool = Field(default=True, description="Whether to receive email updates")
    language: str = Field(default="en", description="Preferred language")
    timezone: Optional[str] = Field(None, description="User's timezone")


class RegistrationStatus(BaseModel):
    """Model for tracking user registration status."""
    is_registered: bool = Field(..., description="Whether user has completed registration")
    profile_completed: bool = Field(default=False, description="Whether profile is completed")
    preferences_set: bool = Field(default=False, description="Whether preferences are set")
    email_verified: bool = Field(default=True, description="Whether email is verified")
    registration_date: Optional[datetime] = Field(None, description="Date of registration")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class UserRegistration(BaseModel):
    """Model for new user registration."""
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    password: str = Field(..., description="User's password", min_length=8)
    profile: Optional[UserProfileUpdate] = Field(None, description="Profile information")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")


class RegistrationRequest(BaseModel):
    """Request model for user registration (authenticated users)."""
    profile: Optional[UserProfileUpdate] = Field(None, description="Profile information to update")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences to set")


class RegistrationResponse(BaseModel):
    """Response model for registration endpoints."""
    message: str = Field(..., description="Registration status message")
    user: User = Field(..., description="Updated user information")
    registration_status: RegistrationStatus = Field(..., description="Current registration status")
    requires_completion: bool = Field(..., description="Whether registration requires completion")


class ProfileResponse(BaseModel):
    """Response model for profile endpoints."""
    user: User = Field(..., description="User profile information")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")
    registration_status: RegistrationStatus = Field(..., description="Registration status")


class UserStats(BaseModel):
    """Model for user statistics and activity."""
    total_queries: int = Field(default=0, description="Total number of queries made")
    queries_this_month: int = Field(default=0, description="Queries made this month")
    favorite_topics: list = Field(default_factory=list, description="Most queried topics")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    account_created: datetime = Field(..., description="Account creation date")
    registration_completed: bool = Field(default=False, description="Whether registration is completed")
