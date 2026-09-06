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
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    sql_path = os.path.join(os.path.dirname(__file__), "grants.sql")
    with open(sql_path) as f:
        sql = f.read()

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
