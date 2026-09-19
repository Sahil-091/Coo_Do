"""Phase 7: retrieval and versioned editing for human-curated support info.

No endpoint in this module calls an LLM.  These details can affect a student's
decision to seek care, so they are retrieved exactly as an authorized editor
has reviewed and published them.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ProfessionalResourceResponse, ProfessionalResourceUpsert
from app.security import verify_internal_secret
from db.models.core import ProfessionalResource

router = APIRouter(
    prefix="/internal/professional-resources",
    tags=["professional-resources"],
    dependencies=[Depends(verify_internal_secret)],
)


def _as_response(row: ProfessionalResource) -> ProfessionalResourceResponse:
    return ProfessionalResourceResponse(
        id=row.id,
        resource_key=row.resource_key,
        version=row.version,
        region=row.region,
        category=row.category,
        title=row.title,
        summary=row.summary,
        contact_label=row.contact_label,
        contact_value=row.contact_value,
        contact_uri=row.contact_uri,
        booking_steps=row.booking_steps or [],
        what_to_expect=row.what_to_expect,
        opening_lines=row.opening_lines or [],
        last_verified_at=row.last_verified_at,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _new_version(payload: ProfessionalResourceUpsert, version: int) -> ProfessionalResource:
    return ProfessionalResource(
        **payload.model_dump(),
        version=version,
        is_active=True,
    )


@router.get("", response_model=list[ProfessionalResourceResponse])
def list_resources(
    region: str = Query(default="India", min_length=2, max_length=80),
    include_inactive: bool = False,
    db: Session = Depends(get_db),
) -> list[ProfessionalResourceResponse]:
    query = db.query(ProfessionalResource).filter(ProfessionalResource.region == region)
    if not include_inactive:
        query = query.filter(ProfessionalResource.is_active.is_(True))
    rows = query.order_by(ProfessionalResource.category, ProfessionalResource.title).all()
    return [_as_response(row) for row in rows]


@router.post("", response_model=ProfessionalResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    payload: ProfessionalResourceUpsert, db: Session = Depends(get_db)
) -> ProfessionalResourceResponse:
    existing = (
        db.query(ProfessionalResource)
        .filter(
            ProfessionalResource.resource_key == payload.resource_key,
            ProfessionalResource.region == payload.region,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource key already exists.")
    row = _new_version(payload, version=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _as_response(row)


@router.put("/{resource_id}", response_model=ProfessionalResourceResponse)
def replace_resource(
    resource_id: uuid.UUID, payload: ProfessionalResourceUpsert, db: Session = Depends(get_db)
) -> ProfessionalResourceResponse:
    current = db.get(ProfessionalResource, resource_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")
    if not current.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only the current version can be replaced.")
    if (payload.resource_key, payload.region) != (current.resource_key, current.region):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Resource key and region cannot change.")

    latest_version = (
        db.query(func.max(ProfessionalResource.version))
        .filter(
            ProfessionalResource.resource_key == current.resource_key,
            ProfessionalResource.region == current.region,
        )
        .scalar()
        or current.version
    )
    current.is_active = False
    replacement = _new_version(payload, version=latest_version + 1)
    db.add(replacement)
    db.commit()
    db.refresh(replacement)
    return _as_response(replacement)
