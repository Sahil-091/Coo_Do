"""
Applies db/grants.sql using a superuser connection. Run AFTER
`alembic upgrade head` — grants.sql assumes the tables already exist.

Usage:
    DATABASE_URL=postgresql://postgres:pw@host/db python apply_grants.py

Separate from env.py's DATABASE_URL handling because this needs a
superuser connection (to CREATE ROLE / GRANT), whereas each service's own
DATABASE_URL is intentionally a least-privilege role that could never run
this script successfully — that's the point.
"""
import os

import psycopg2
from psycopg2.extensions import adapt

ROLE_PASSWORD_DEFAULTS = {
    "APP_CORE_API_DB_PASSWORD": "change_me_core_api",
    "APP_SAFETY_SERVICE_DB_PASSWORD": "change_me_safety_service",
    "APP_SAFETY_REVIEWER_DB_PASSWORD": "change_me_safety_reviewer",
    "APP_MATCHING_SERVICE_DB_PASSWORD": "change_me_matching_service",
    "APP_MODERATION_SERVICE_DB_PASSWORD": "change_me_moderation_service",
    "APP_MODERATION_REVIEWER_DB_PASSWORD": "change_me_moderation_reviewer",
}


def render_grants(sql: str) -> str:
    """Substitute SQL-quoted role passwords without putting secrets in SQL."""
    for environment_name, development_default in ROLE_PASSWORD_DEFAULTS.items():
        placeholder = f"__{environment_name}__"
        password = os.environ.get(environment_name, development_default)
        sql = sql.replace(placeholder, adapt(password).getquoted().decode())
    return sql


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    sql_path = os.path.join(os.path.dirname(__file__), "grants.sql")
    with open(sql_path) as f:
        sql = render_grants(f.read())

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
    finally:
        conn.close()

    print("grants.sql applied successfully")


if __name__ == "__main__":
    main()
