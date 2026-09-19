import enum
import uuid
from datetime import date, datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.checkin_rules import Feeling, Need, SuggestedPath, TimeOfDay
from db.models.core import ConsentType, DataRequestStatus, DataRequestType
from db.models.core import (
    ActivityStatus,
    ActivityTopic,
    PresenceFeedback,
    TrustedContactRelationship,
    TrustedContactScenario,
    MeetupCategory,
    RSVPStatus,
)

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


class MatchingActivityType(enum.StrEnum):
    STUDY = "study"
    CODING = "coding"
    READING = "reading"
    WRITING = "writing"
    QUIET_WORK = "quiet_work"


class MatchingProfileRequest(BaseModel):
    """Student-selected compatibility signals; region/language stay private."""

    course: str | None = Field(default=None, max_length=120)
    year: int | None = Field(default=None, ge=1, le=12)
    interests: list[str] = Field(default_factory=list, max_length=12)
    activity_types: list[MatchingActivityType] = Field(default_factory=list, max_length=5)
    region: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=80)

    @field_validator("course", "region", "language")
    @classmethod
    def trim_optional_values(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("interests")
    @classmethod
    def normalize_interests(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value if item.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("interests cannot contain duplicates")
        if any(len(item) > 40 for item in normalized):
            raise ValueError("each interest must be 40 characters or fewer")
        return normalized

    @field_validator("activity_types")
    @classmethod
    def activity_types_are_unique(cls, value: list[MatchingActivityType]) -> list[MatchingActivityType]:
        if len(value) != len(set(value)):
            raise ValueError("activity_types cannot contain duplicates")
        return value

    @model_validator(mode="after")
    def requires_a_public_signal(self) -> "MatchingProfileRequest":
        if not self.interests and not self.activity_types and not self.course and self.year is None:
            raise ValueError("add at least one matching signal")
        return self


class MatchingProfileResponse(MatchingProfileRequest):
    pass


class MatchingCandidateInternal(BaseModel):
    """Only core-api -> matching-service may receive this contract."""

    user_id: uuid.UUID
    display_name: str | None
    course: str | None
    year: int | None
    interests: list[str]
    activity_types: list[MatchingActivityType]
    # Weight-only fields. matching-service must never relay either to its UI.
    region: str | None
    language: str | None


class MatchingCandidatePoolResponse(BaseModel):
    requester: MatchingCandidateInternal
    candidates: list[MatchingCandidateInternal]


class DataRequestCreate(BaseModel):
    request_type: DataRequestType
    notes: str | None = Field(default=None, max_length=200)


class DataRequestResponse(BaseModel):
    id: uuid.UUID
    request_type: DataRequestType
    status: DataRequestStatus
    created_at: datetime
    completed_at: datetime | None
    notes: str | None = None


class JournalEntryCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class JournalEntryResponse(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    updated_at: datetime


class JournalExportResponse(BaseModel):
    """A user's complete, decrypted private journal export."""
    entries: list[JournalEntryResponse]


class JournalComparisonResponse(BaseModel):
    window_days: int
    narrative: str


class RealLifeIndicatorResponse(BaseModel):
    key: str
    sentence: str


class ResourceOpenResponse(BaseModel):
    destination: str
    action_type: str


class ProfessionalResourceUpsert(BaseModel):
    """Editor-only input; the API turns updates into a new version."""

    resource_key: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9-]+$")
    region: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=160)
    summary: str = Field(min_length=10, max_length=2000)
    contact_label: str | None = Field(default=None, max_length=120)
    contact_value: str | None = Field(default=None, max_length=240)
    contact_uri: str | None = Field(default=None, max_length=500)
    booking_steps: list[str] = Field(default_factory=list, max_length=8)
    what_to_expect: str | None = Field(default=None, max_length=2000)
    opening_lines: list[str] = Field(default_factory=list, max_length=6)
    last_verified_at: date | None = None

    @field_validator("contact_uri")
    @classmethod
    def contact_uri_is_safe_destination(cls, value: str | None) -> str | None:
        if value is None:
            return value
        # This value is later used as a browser navigation target after the
        # student's explicit action.  Do not let a directory editor turn it
        # into a script/data URL.
        if urlparse(value).scheme not in {"https", "tel", "mailto"}:
            raise ValueError("contact_uri must use https, tel, or mailto")
        return value


class ProfessionalResourceResponse(ProfessionalResourceUpsert):
    id: uuid.UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


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
    time_of_day: str
    created_at: datetime


class CheckInSubmitResponse(BaseModel):
    checkin: CheckInResponse
    routing: RoutingResultResponse


class TinyActionRung(BaseModel):
    id: uuid.UUID
    difficulty_level: int
    title: str
    description: str
    # A generated message when an owned check-in was supplied; otherwise the
    # existing static Phase 4 description.  The UI has one stable field and
    # never has to know whether an inference call succeeded.
    voice_message: str


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


class ActivityCreateRequest(BaseModel):
    """Fixed topics avoid opening an unmoderated free-text surface in Phase 9."""

    topic: ActivityTopic
    starts_at: datetime | None = None

    @field_validator("starts_at")
    @classmethod
    def scheduled_time_has_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("starts_at must include a timezone")
        return value


class ActivityResponse(BaseModel):
    id: uuid.UUID
    topic: ActivityTopic
    status: ActivityStatus
    starts_at: datetime | None
    ends_at: datetime | None
    room_id: uuid.UUID
    headcount: int = Field(ge=0)
    is_open: bool


class PresenceTokenResponse(BaseModel):
    room_id: uuid.UUID
    websocket_token: str
    expires_at: datetime
    headcount: int = Field(ge=0)


class PresenceFeedbackRequest(BaseModel):
    feedback: PresenceFeedback | None = None


class TrustedContactChannel(enum.StrEnum):
    SMS = "sms"
    EMAIL = "email"


class TrustedContactCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    relationship: TrustedContactRelationship
    channel: TrustedContactChannel
    contact_value: str = Field(min_length=3, max_length=320)
    allowed_scenarios: list[TrustedContactScenario] = Field(min_length=1, max_length=4)

    @field_validator("display_name")
    @classmethod
    def display_name_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name cannot be blank")
        return value

    @field_validator("allowed_scenarios")
    @classmethod
    def scenario_scopes_are_unique(cls, value: list[TrustedContactScenario]) -> list[TrustedContactScenario]:
        if len(set(value)) != len(value):
            raise ValueError("allowed_scenarios cannot contain duplicates")
        return value

    @model_validator(mode="after")
    def destination_matches_channel(self) -> "TrustedContactCreate":
        value = self.contact_value.strip()
        if self.channel == TrustedContactChannel.EMAIL:
            if "@" not in value or value.startswith("@") or value.endswith("@"):
                raise ValueError("contact_value must be an email address for email contacts")
        elif sum(char.isdigit() for char in value) < 7:
            raise ValueError("contact_value must include at least seven digits for SMS contacts")
        self.contact_value = value
        return self


class TrustedContactResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    relationship: TrustedContactRelationship
    channel: TrustedContactChannel
    allowed_scenarios: list[TrustedContactScenario]
    created_at: datetime
    updated_at: datetime


class TrustedOutreachRequest(BaseModel):
    scenario: TrustedContactScenario


class TrustedOutreachResponse(BaseModel):
    """A client navigation target created only after a student's explicit tap."""

    destination: str
    contact_name: str


class VenueResponse(BaseModel):
    id: str
    name: str
    category: str
    map_url: str


class ActivityMeetupCreateRequest(BaseModel):
    # A venue must be selected by ID from the server-owned catalogue. Forbid
    # rather than silently discard unknown fields so a caller cannot claim an
    # address/name/map URL was accepted by this endpoint.
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    category: MeetupCategory
    venue_id: str = Field(min_length=2, max_length=160)
    starts_at: datetime
    max_participants: int = Field(ge=2, le=100)

    @field_validator("starts_at")
    @classmethod
    def meetup_time_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("starts_at must include a timezone")
        return value


class ActivityMeetupResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: MeetupCategory
    venue_name: str
    venue_map_url: str
    starts_at: datetime
    max_participants: int
    joining_count: int
    maybe_count: int
    my_rsvp: RSVPStatus | None


class ActivityRSVPRequest(BaseModel):
    status: RSVPStatus


class AreaPreferenceRequest(BaseModel):
    # This is processed into a coarse cell immediately and never persisted.
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    enabled: bool

    @model_validator(mode="after")
    def enabled_preference_needs_coordinates(self) -> "AreaPreferenceRequest":
        # Coordinates may arrive only for the one-way, in-memory conversion
        # to a server-owned area cell. Disabling deletes the stored cell and
        # therefore deliberately accepts no coordinates at all.
        if self.enabled and (self.latitude is None or self.longitude is None):
            raise ValueError("latitude and longitude are required when enabling activity alerts")
        return self


class AreaPreferenceResponse(BaseModel):
    enabled: bool
    has_area: bool
