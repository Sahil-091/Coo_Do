import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ActivityType(enum.StrEnum):
    STUDY = "study"
    CODING = "coding"
    READING = "reading"
    WRITING = "writing"
    QUIET_WORK = "quiet_work"


class InternalCandidate(BaseModel):
    user_id: uuid.UUID
    display_name: str | None
    course: str | None
    year: int | None
    interests: list[str]
    activity_types: list[ActivityType]
    region: str | None
    language: str | None


class CandidatePool(BaseModel):
    requester: InternalCandidate
    candidates: list[InternalCandidate]


class MatchCandidateResponse(BaseModel):
    user_id: uuid.UUID
    display_name: str | None
    course: str | None
    year: int | None
    shared_interests: list[str]
    shared_activity_types: list[ActivityType]
    same_course: bool
    same_year: bool
    compatibility_reason: str


class CreateMatchRequest(BaseModel):
    user_id: uuid.UUID
    target_user_id: uuid.UUID


class MatchResponse(BaseModel):
    id: uuid.UUID
    status: str
    requested_by_user_id: uuid.UUID
    created_at: datetime


class RespondToMatchRequest(BaseModel):
    user_id: uuid.UUID
    decision: str = Field(pattern="^(accepted|declined)$")


class BlockUserRequest(BaseModel):
    user_id: uuid.UUID
    target_user_id: uuid.UUID


class ReportCategory(enum.StrEnum):
    DATING_OR_ROMANTIC_APPROACH = "dating_or_romantic_approach"
    HARASSMENT = "harassment"
    SAFETY_CONCERN = "safety_concern"
    OTHER = "other"


class ReportUserRequest(BlockUserRequest):
    category: ReportCategory


    @field_validator("target_user_id")
    @classmethod
    def target_is_not_reporter(cls, value: uuid.UUID, info):
        if value == info.data.get("user_id"):
            raise ValueError("you cannot report yourself")
        return value
