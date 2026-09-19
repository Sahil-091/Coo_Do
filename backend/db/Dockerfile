FROM python:3.12-slim
WORKDIR /migrate

COPY db/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY db ./db

# DATABASE_URL is provided at runtime by docker-compose and must be a
# SUPERUSER connection for this container specifically (it needs to
# CREATE ROLE / GRANT) — this is intentionally different from every
# other service's own least-privilege DATABASE_URL.
CMD ["sh", "-c", "alembic upgrade head && python db/apply_grants.py"]
