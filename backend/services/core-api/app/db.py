from collections.abc import Generator

from sqlalchemy.orm import Session

from db.base import SessionLocal

# Reuses the shared db.base engine/session factory rather than creating a
# second one — db.base already reads DATABASE_URL from the environment,
# and core-api's actual runtime DATABASE_URL (set via docker-compose /
# .env, using the app_core_api role's credentials — see db/grants.sql)
# is what SessionLocal ends up bound to. No need to duplicate that here.


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
