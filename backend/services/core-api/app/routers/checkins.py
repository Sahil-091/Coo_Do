import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.checkin_rules import route_checkin
from app.db import get_db
from app.schemas import (
    CheckInCreateRequest,
    CheckInResponse,
    CheckInSubmitResponse,
    RoutingResultResponse,
)
from app.security import verify_internal_secret
from db.models.core import CheckIn, User

router = APIRouter(
    prefix="/internal/users",
    tags=["checkins"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.post("/{user_id}/checkins", response_model=CheckInSubmitResponse, status_code=201)
def submit_checkin(
    user_id: uuid.UUID, payload: CheckInCreateRequest, db: Session = Depends(get_db)
) -> CheckInSubmitResponse:
    """
    Persists the raw check-in (feelings + stated need only — no free
    text, no score) and returns the deterministic routing result from
    checkin_rules.route_checkin. The routing decision itself is NOT
    persisted (see checkin_rules.py's module docstring) — it's a pure,
    stateless function of the inputs, so recomputing it is always
    consistent and there's nothing to keep in sync.
    """
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    checkin = CheckIn(
        user_id=user_id,
        feelings=[f.value for f in payload.feelings],
        stated_need=payload.stated_need.value,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    routing = route_checkin(
        feelings=payload.feelings, need=payload.stated_need, time_of_day=payload.time_of_day
    )

    return CheckInSubmitResponse(
        checkin=CheckInResponse(
            id=checkin.id,
            feelings=checkin.feelings,
            stated_need=checkin.stated_need,
            created_at=checkin.created_at,
        ),
        routing=RoutingResultResponse(path=routing.path, reason=routing.reason),
    )
