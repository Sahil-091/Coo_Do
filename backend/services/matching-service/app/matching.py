"""Rules-based matching. There is no model inference or romantic signal."""
import uuid

from sqlalchemy import UUID, and_, column, exists, or_, select, values
from sqlalchemy.orm import Session

from app.schemas import InternalCandidate, MatchCandidateResponse
from db.models.matching import MatchBlock, MatchReport


def eligible_candidate_ids(
    db: Session, requester_id: uuid.UUID, candidate_ids: list[uuid.UUID]
) -> set[uuid.UUID]:
    """Exclude blocks and report history *inside the candidate SQL query*.

    Core-api supplies an already-consented candidate pool.  `VALUES` turns its
    ids into a SQL relation, and both directions of blocks/reports are applied
    with NOT EXISTS before any candidate can be ranked or returned.
    """
    if not candidate_ids:
        return set()
    candidate_pool = (
        values(column("candidate_id", UUID(as_uuid=True)), name="candidate_pool")
        .data([(candidate_id,) for candidate_id in candidate_ids])
        .cte("candidate_pool")
    )
    blocked = exists().where(
        or_(
            and_(
                MatchBlock.blocker_user_id == requester_id,
                MatchBlock.blocked_user_id == candidate_pool.c.candidate_id,
            ),
            and_(
                MatchBlock.blocker_user_id == candidate_pool.c.candidate_id,
                MatchBlock.blocked_user_id == requester_id,
            ),
        )
    )
    reported = exists().where(
        or_(
            and_(
                MatchReport.reporter_user_id == requester_id,
                MatchReport.target_user_id == candidate_pool.c.candidate_id,
            ),
            and_(
                MatchReport.reporter_user_id == candidate_pool.c.candidate_id,
                MatchReport.target_user_id == requester_id,
            ),
        )
    )
    statement = select(candidate_pool.c.candidate_id).where(~blocked, ~reported)
    return set(db.scalars(statement).all())


def rank_candidates(
    requester: InternalCandidate, candidates: list[InternalCandidate], eligible_ids: set[uuid.UUID]
) -> list[MatchCandidateResponse]:
    """Score only the approved signals; region/language are private tie-breakers."""
    requester_interests = set(requester.interests)
    requester_activities = set(requester.activity_types)
    ranked: list[tuple[int, str, MatchCandidateResponse]] = []

    for candidate in candidates:
        if candidate.user_id not in eligible_ids:
            continue
        shared_interests = sorted(requester_interests.intersection(candidate.interests))
        shared_activities = sorted(requester_activities.intersection(candidate.activity_types))
        same_course = bool(requester.course and requester.course == candidate.course)
        same_year = requester.year is not None and requester.year == candidate.year
        public_score = len(shared_interests) * 6 + len(shared_activities) * 4 + int(same_course) * 3 + int(same_year) * 2
        # Never use region/language as a sole basis or expose why they were
        # considered. They are only a small private tiebreaker for homesickness
        # and language-comfort use cases.
        private_tiebreak = int(bool(requester.region and requester.region == candidate.region))
        private_tiebreak += int(bool(requester.language and requester.language == candidate.language))
        if public_score == 0:
            continue

        reasons: list[str] = []
        if shared_interests:
            reasons.append("shared interests")
        if shared_activities:
            reasons.append("a shared activity style")
        if same_course:
            reasons.append("a course")
        if same_year:
            reasons.append("a year of study")
        response = MatchCandidateResponse(
            user_id=candidate.user_id,
            display_name=candidate.display_name,
            course=candidate.course,
            year=candidate.year,
            shared_interests=shared_interests,
            shared_activity_types=shared_activities,
            same_course=same_course,
            same_year=same_year,
            compatibility_reason="You share " + ", ".join(reasons) + ".",
        )
        ranked.append((public_score * 10 + private_tiebreak, str(candidate.user_id), response))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked]
