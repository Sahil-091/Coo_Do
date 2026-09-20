"""Phase 9 virtual activities and anonymous Presence Mode headcounts.

The HTTP routes remain behind the Next.js internal boundary. The one public
surface is the WebSocket endpoint, and it accepts only a short-lived,
server-signed room token. It never sends identities, messages, media, or
location data to another participant.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas import (
    ActivityCreateRequest,
    ActivityResponse,
    PresenceFeedbackRequest,
    PresenceTokenResponse,
)
from app.security import verify_internal_secret
from db.models.core import Activity, ActivityParticipant, ActivityStatus, PresenceRoom, User

router = APIRouter(prefix="/internal/users", tags=["activities"], dependencies=[Depends(verify_internal_secret)])
# Browsers cannot safely hold the internal shared secret. This separate router
# is intentionally public only for the signed, short-lived WebSocket token.
websocket_router = APIRouter(prefix="/internal/users", tags=["activities"])

MAX_CREATED_PER_HOUR = 3
MAX_JOIN_TOKENS_PER_HOUR = 12
PRESENCE_TOKEN_LIFETIME = timedelta(minutes=5)


class PresenceManager:
    """In-process WebSocket fan-out that exposes only a room's headcount.

    Phase 9's single core-api deployment needs no separate real-time service.
    Before scaling core-api horizontally, replace this with a shared presence
    adapter; the database remains free of participant identity exposure.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, dict[uuid.UUID, set[WebSocket]]] = defaultdict(lambda: defaultdict(set))
        self._join_tokens: dict[uuid.UUID, deque[float]] = defaultdict(deque)

    def allow_join_token(self, user_id: uuid.UUID) -> bool:
        now = time.monotonic()
        bucket = self._join_tokens[user_id]
        cutoff = now - 3600
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= MAX_JOIN_TOKENS_PER_HOUR:
            return False
        bucket.append(now)
        return True

    def headcount(self, room_id: uuid.UUID) -> int:
        return len(self._connections.get(room_id, {}))

    async def connect(self, room_id: uuid.UUID, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[room_id][user_id].add(websocket)
        await self.broadcast_headcount(room_id)

    async def disconnect(self, room_id: uuid.UUID, user_id: uuid.UUID, websocket: WebSocket) -> None:
        users = self._connections.get(room_id)
        if users is None:
            return
        sockets = users.get(user_id)
        if sockets is not None:
            sockets.discard(websocket)
            if not sockets:
                del users[user_id]
        if not users:
            self._connections.pop(room_id, None)
        await self.broadcast_headcount(room_id)

    async def broadcast_headcount(self, room_id: uuid.UUID) -> None:
        payload = json.dumps({"type": "headcount", "count": self.headcount(room_id)})
        stale: list[tuple[uuid.UUID, WebSocket]] = []
        for user_id, sockets in list(self._connections.get(room_id, {}).items()):
            for socket in list(sockets):
                try:
                    await socket.send_text(payload)
                except RuntimeError:
                    stale.append((user_id, socket))
        for user_id, socket in stale:
            self._connections[room_id][user_id].discard(socket)


presence_manager = PresenceManager()


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _issue_token(user_id: uuid.UUID, room_id: uuid.UUID) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + PRESENCE_TOKEN_LIFETIME
    payload = {"user_id": str(user_id), "room_id": str(room_id), "exp": int(expires_at.timestamp()), "nonce": secrets.token_urlsafe(12)}
    encoded = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(settings.internal_shared_secret.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_b64_encode(signature)}", expires_at


def _verify_token(token: str, expected_room_id: uuid.UUID) -> uuid.UUID | None:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(settings.internal_shared_secret.encode(), encoded.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, _b64_decode(supplied_signature)):
            return None
        payload = json.loads(_b64_decode(encoded))
        if payload["room_id"] != str(expected_room_id) or int(payload["exp"]) < int(time.time()):
            return None
        return uuid.UUID(payload["user_id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _get_user(db: Session, user_id: uuid.UUID) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")


def _activity_response(activity: Activity, room: PresenceRoom) -> ActivityResponse:
    return ActivityResponse(id=activity.id, topic=activity.topic, status=activity.status, starts_at=activity.starts_at, ends_at=activity.ends_at, room_id=room.id, headcount=presence_manager.headcount(room.id), is_open=room.is_open)


def _start_due_activities(db: Session) -> None:
    """Promote scheduled virtual rooms on demand; no background scheduler needed."""
    now = datetime.now(UTC)
    db.query(Activity).filter(
        Activity.status == ActivityStatus.SCHEDULED,
        Activity.starts_at.is_not(None),
        Activity.starts_at <= now,
    ).update({Activity.status: ActivityStatus.LIVE}, synchronize_session=False)
    db.commit()


@router.get("/{user_id}/activities", response_model=list[ActivityResponse])
def list_activities(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ActivityResponse]:
    _get_user(db, user_id)
    _start_due_activities(db)
    rows = db.query(Activity, PresenceRoom).join(PresenceRoom, PresenceRoom.activity_id == Activity.id).filter(Activity.status.in_((ActivityStatus.LIVE, ActivityStatus.SCHEDULED)), PresenceRoom.is_open).order_by(Activity.starts_at.is_(None).desc(), Activity.starts_at.asc(), Activity.created_at.desc()).all()
    return [_activity_response(activity, room) for activity, room in rows]


@router.post("/{user_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(user_id: uuid.UUID, payload: ActivityCreateRequest, db: Session = Depends(get_db)) -> ActivityResponse:
    _get_user(db, user_id)
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    creations = db.query(Activity).filter(Activity.creator_user_id == user_id, Activity.created_at >= cutoff).count()
    if creations >= MAX_CREATED_PER_HOUR:
        raise HTTPException(status_code=429, detail="You can create up to three rooms an hour. Try again later.")

    starts_at = payload.starts_at
    scheduled = starts_at is not None and starts_at > datetime.now(UTC) + timedelta(minutes=1)
    activity = Activity(creator_user_id=user_id, topic=payload.topic, status=ActivityStatus.SCHEDULED if scheduled else ActivityStatus.LIVE, starts_at=starts_at)
    db.add(activity)
    db.flush()
    room = PresenceRoom(activity_id=activity.id)
    db.add(room)
    db.commit()
    db.refresh(activity)
    db.refresh(room)
    return _activity_response(activity, room)


@router.post("/{user_id}/activities/{activity_id}/presence-token", response_model=PresenceTokenResponse)
def create_presence_token(user_id: uuid.UUID, activity_id: uuid.UUID, db: Session = Depends(get_db)) -> PresenceTokenResponse:
    _get_user(db, user_id)
    _start_due_activities(db)
    row = db.query(Activity, PresenceRoom).join(PresenceRoom, PresenceRoom.activity_id == Activity.id).filter(Activity.id == activity_id, PresenceRoom.is_open, Activity.status == ActivityStatus.LIVE).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="That virtual room is not available.")
    if not presence_manager.allow_join_token(user_id):
        raise HTTPException(status_code=429, detail="You've joined several rooms recently. Please try again later.")
    _, room = row
    token, expires_at = _issue_token(user_id, room.id)
    return PresenceTokenResponse(room_id=room.id, websocket_token=token, expires_at=expires_at, headcount=presence_manager.headcount(room.id))


@router.put("/{user_id}/activities/{activity_id}/presence-feedback", status_code=status.HTTP_204_NO_CONTENT)
def save_presence_feedback(user_id: uuid.UUID, activity_id: uuid.UUID, payload: PresenceFeedbackRequest, db: Session = Depends(get_db)) -> None:
    _get_user(db, user_id)
    participant = db.query(ActivityParticipant).filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id).one_or_none()
    if participant is None:
        raise HTTPException(status_code=404, detail="Join the room before sharing feedback.")
    participant.feedback = payload.feedback
    db.commit()


def _record_join(room_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Persist minimal private attendance only after a WebSocket truly opens."""
    from db.base import SessionLocal

    with SessionLocal() as db:
        room = db.get(PresenceRoom, room_id)
        if room is None or not room.is_open:
            return
        participant = db.query(ActivityParticipant).filter(ActivityParticipant.activity_id == room.activity_id, ActivityParticipant.user_id == user_id).one_or_none()
        now = datetime.now(UTC)
        if participant is None:
            db.add(ActivityParticipant(activity_id=room.activity_id, user_id=user_id, last_joined_at=now))
        else:
            participant.join_count += 1
            participant.last_joined_at = now
            participant.left_at = None
        db.commit()


def _record_leave(room_id: uuid.UUID, user_id: uuid.UUID) -> None:
    from db.base import SessionLocal

    with SessionLocal() as db:
        room = db.get(PresenceRoom, room_id)
        if room is None:
            return
        participant = db.query(ActivityParticipant).filter(ActivityParticipant.activity_id == room.activity_id, ActivityParticipant.user_id == user_id).one_or_none()
        if participant is not None:
            participant.left_at = datetime.now(UTC)
            db.commit()


@websocket_router.websocket("/presence-rooms/{room_id}/ws")
async def presence_websocket(websocket: WebSocket, room_id: uuid.UUID, token: str = Query(...)) -> None:
    """A token-protected, count-only WebSocket; no participant identity leaks."""
    user_id = _verify_token(token, room_id)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await presence_manager.connect(room_id, user_id, websocket)
    _record_join(room_id, user_id)
    try:
        while True:
            # Ignore contents so Presence Mode never becomes a chat/free-text channel.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await presence_manager.disconnect(room_id, user_id, websocket)
        if user_id not in presence_manager._connections.get(room_id, {}):
            _record_leave(room_id, user_id)
