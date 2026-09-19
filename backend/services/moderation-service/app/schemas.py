import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from db.models.moderation import CommunityReportCategory, CommunityRoomTopic, ModerationReviewStatus

GUIDELINES_VERSION = "community-guidelines-v1"


class RoomCreateRequest(BaseModel):
    user_id: uuid.UUID
    topic: CommunityRoomTopic


class RoomResponse(BaseModel):
    id: uuid.UUID
    topic: CommunityRoomTopic
    created_at: datetime


class GuidelinesAcceptanceRequest(BaseModel):
    user_id: uuid.UUID
    guidelines_version: str = Field(default=GUIDELINES_VERSION, pattern="^community-guidelines-v1$")


class PostCreateRequest(BaseModel):
    user_id: uuid.UUID
    body: str = Field(min_length=1, max_length=1200)
    guidelines_version: str = Field(default=GUIDELINES_VERSION, pattern="^community-guidelines-v1$")


class PostResponse(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime


class PostSubmitResponse(BaseModel):
    post: PostResponse | None
    held_for_review: bool
    safety_flag_level: str


class ReportCreateRequest(BaseModel):
    user_id: uuid.UUID
    category: CommunityReportCategory


class ReviewEventResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    room_id: uuid.UUID
    body: str
    reasons: list[str]
    self_harm_level: str
    review_status: ModerationReviewStatus
    created_at: datetime


class ReviewDecisionRequest(BaseModel):
    reviewer_ref: uuid.UUID
    decision: ModerationReviewStatus


class ContentScreenRequest(BaseModel):
    user_id: uuid.UUID
    text: str = Field(min_length=1, max_length=2400)
    source: str = Field(pattern="^(community_post|activity_meetup)$")


class ContentScreenResponse(BaseModel):
    held: bool
    reasons: list[str]
    safety_flag_level: str
