import uuid

from sqlalchemy.dialects import postgresql

from app.matching import eligible_candidate_ids, rank_candidates
from app.schemas import ActivityType, InternalCandidate


def _candidate(**overrides) -> InternalCandidate:
    data = {
        "user_id": uuid.uuid4(),
        "display_name": "Quiet Fox",
        "course": "Computer Science",
        "year": 2,
        "interests": ["chess", "sci-fi"],
        "activity_types": [ActivityType.STUDY],
        "region": "North",
        "language": "English",
    }
    data.update(overrides)
    return InternalCandidate(**data)


def test_ranking_uses_public_signals_and_never_exposes_private_tiebreakers():
    requester = _candidate()
    candidate = _candidate(
        display_name="Kind Otter",
        interests=["chess"],
        activity_types=[ActivityType.READING],
    )
    results = rank_candidates(requester, [candidate], {candidate.user_id})

    assert len(results) == 1
    assert results[0].shared_interests == ["chess"]
    assert results[0].compatibility_reason == "You share shared interests, a course, a year of study."
    assert "region" not in results[0].model_dump()
    assert "language" not in results[0].model_dump()


def test_candidate_exclusion_is_encoded_in_the_matching_sql_query():
    candidate_id = uuid.uuid4()

    class ScalarResult:
        def all(self):
            return []

    class RecordingSession:
        statement = None

        def scalars(self, statement):
            self.statement = statement
            return ScalarResult()

    session = RecordingSession()
    assert eligible_candidate_ids(session, uuid.uuid4(), [candidate_id]) == set()
    compiled = str(session.statement.compile(dialect=postgresql.dialect()))
    assert "NOT (EXISTS" in compiled
    assert "match_blocks" in compiled
    assert "match_reports" in compiled
