"""Phase 11 non-dating, rules-based student matching service."""
import uuid

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core_client import fetch_candidate_pool
from app.db import get_db
from app.matching import eligible_candidate_ids, rank_candidates
from app.schemas import (
    BlockUserRequest,
    CandidatePool,
    CreateMatchRequest,
    MatchCandidateResponse,
    MatchResponse,
    ReportUserRequest,
    RespondToMatchRequest,
)
from app.security import verify_internal_secret
from db.models.matching import Match, MatchBlock, MatchReport, MatchStatus

app = FastAPI(title="matching-service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "matching-service"}


def _pair(user_id: uuid.UUID, target_user_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    if user_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="You cannot match with yourself.")
    return (user_id, target_user_id) if str(user_id) < str(target_user_id) else (target_user_id, user_id)


def _pool_or_http_error(user_id: uuid.UUID) -> CandidatePool:
    try:
        return CandidatePool.model_validate(fetch_candidate_pool(user_id))
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {403, 404}:
            raise HTTPException(status_code=error.response.status_code, detail="Matching is not available for this profile.") from None
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Matching is temporarily unavailable.") from None
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Matching is temporarily unavailable.") from None


@app.get("/internal/matches", response_model=list[MatchCandidateResponse], dependencies=[Depends(verify_internal_secret)])
def list_matches(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[MatchCandidateResponse]:
    pool = _pool_or_http_error(user_id)
    allowed_ids = eligible_candidate_ids(db, user_id, [candidate.user_id for candidate in pool.candidates])
    return rank_candidates(pool.requester, pool.candidates, allowed_ids)


@app.post("/internal/matches/requests", response_model=MatchResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_secret)])
def request_match(payload: CreateMatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    pool = _pool_or_http_error(payload.user_id)
    eligible_ids = eligible_candidate_ids(db, payload.user_id, [item.user_id for item in pool.candidates])
    ranked_ids = {
        candidate.user_id
        for candidate in rank_candidates(pool.requester, pool.candidates, eligible_ids)
    }
    if payload.target_user_id not in ranked_ids:
        # Keep excluded accounts indistinguishable from unavailable ones.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That match is unavailable.")
    user_one_id, user_two_id = _pair(payload.user_id, payload.target_user_id)
    existing = db.query(Match).filter(Match.user_one_id == user_one_id, Match.user_two_id == user_two_id).first()
    if existing is not None:
        return MatchResponse(id=existing.id, status=existing.status, requested_by_user_id=existing.requested_by_user_id, created_at=existing.created_at)
    match = Match(user_one_id=user_one_id, user_two_id=user_two_id, requested_by_user_id=payload.user_id)
    db.add(match)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        match = db.query(Match).filter(Match.user_one_id == user_one_id, Match.user_two_id == user_two_id).one()
    else:
        db.refresh(match)
    return MatchResponse(id=match.id, status=match.status, requested_by_user_id=match.requested_by_user_id, created_at=match.created_at)


@app.post("/internal/matches/{match_id}/respond", response_model=MatchResponse, dependencies=[Depends(verify_internal_secret)])
def respond_to_match(match_id: uuid.UUID, payload: RespondToMatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    match = db.get(Match, match_id)
    if match is None or payload.user_id not in {match.user_one_id, match.user_two_id}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
    if match.requested_by_user_id == payload.user_id or match.status != MatchStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request cannot be changed.")
    match.status = MatchStatus(payload.decision)
    db.commit()
    db.refresh(match)
    return MatchResponse(id=match.id, status=match.status, requested_by_user_id=match.requested_by_user_id, created_at=match.created_at)


@app.post("/internal/matches/block", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_internal_secret)])
def block_user(payload: BlockUserRequest, db: Session = Depends(get_db)) -> None:
    user_one_id, user_two_id = _pair(payload.user_id, payload.target_user_id)
    if db.query(MatchBlock).filter(MatchBlock.blocker_user_id == payload.user_id, MatchBlock.blocked_user_id == payload.target_user_id).first() is None:
        db.add(MatchBlock(blocker_user_id=payload.user_id, blocked_user_id=payload.target_user_id))
    db.query(Match).filter(
        Match.user_one_id == user_one_id, Match.user_two_id == user_two_id
    ).update({Match.status: MatchStatus.BLOCKED}, synchronize_session=False)
    db.commit()


@app.post("/internal/matches/report", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_internal_secret)])
def report_user(payload: ReportUserRequest, db: Session = Depends(get_db)) -> None:
    _pair(payload.user_id, payload.target_user_id)
    db.add(MatchReport(reporter_user_id=payload.user_id, target_user_id=payload.target_user_id, category=payload.category))
    db.commit()
