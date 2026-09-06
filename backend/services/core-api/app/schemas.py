import enum
import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.checkin_rules import Feeling, Need, SuggestedPath, TimeOfDay
from db.models.core import ConsentType, DataRequestStatus, DataRequestType

MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=200)


class RegisterResponse(BaseModel):
    user_id: uuid.UUID


class VerifyCredentialsRequest(BaseModel):
    email: EmailStr
    password: str


class UserStateResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    age_verified: bool
    pseudonymous_display_name: str | None
    created_at: datetime


class AgeVerificationRequest(BaseModel):
    date_of_birth: date

    @field_validator("date_of_birth")
    @classmethod
    def not_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class AgeVerificationResponse(BaseModel):
    age_verified: bool
    minimum_age: int = 18


class DisplayNameRequest(BaseModel):
    # Empty string and null both mean "no display name set" (anonymous).
    pseudonymous_display_name: str | None = Field(default=None, max_length=60)


class ConsentUpsertRequest(BaseModel):
    consent_type: ConsentType
    granted: bool


class ConsentStateResponse(BaseModel):
    consent_type: ConsentType
    granted: bool
    updated_at: datetime | None


class PrivacySettingsRequest(BaseModel):
    profile_visible_in_matching: bool
    display_name_visible_in_rooms: bool


class PrivacySettingsResponse(PrivacySettingsRequest):
    updated_at: datetime


class DataRequestCreate(BaseModel):
    request_type: DataRequestType


class DataRequestResponse(BaseModel):
    id: uuid.UUID
    request_type: DataRequestType
    status: DataRequestStatus
    created_at: datetime
    completed_at: datetime | None


class CheckInCreateRequest(BaseModel):
    feelings: list[Feeling] = Field(min_length=1, max_length=len(Feeling))
    stated_need: Need
    time_of_day: TimeOfDay


class RoutingResultResponse(BaseModel):
    path: SuggestedPath
    reason: str


class CheckInResponse(BaseModel):
    id: uuid.UUID
    feelings: list[str]
    stated_need: str | None
    created_at: datetime


class CheckInSubmitResponse(BaseModel):
    checkin: CheckInResponse
    routing: RoutingResultResponse


class TinyActionRung(BaseModel):
    id: uuid.UUID
    difficulty_level: int
    title: str
    description: str


class SuggestionResponse(BaseModel):
    ladder: list[TinyActionRung]  # ordered easiest (1) to hardest (3)
    suggested_attempt_id: uuid.UUID


class ActionAttemptStatusIn(enum.StrEnum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REDUCED = "reduced"


class ActionAttemptCreateRequest(BaseModel):
    tiny_action_id: uuid.UUID
    status: ActionAttemptStatusIn
    related_checkin_id: uuid.UUID | None = None


class ActionAttemptResponse(BaseModel):
    id: uuid.UUID
    tiny_action_id: uuid.UUID
    status: str
    related_checkin_id: uuid.UUID | None
    created_at: datetime


class ActionAttemptSubmitResponse(BaseModel):
    attempt: ActionAttemptResponse
    show_support_nudge: bool
