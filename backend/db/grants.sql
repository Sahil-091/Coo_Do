-- Least-privilege role separation for core-api and safety-service.
-- R&D doc Section 19: "safety_events... most access-restricted table in
-- the schema" and Section 21: schema separation so a compromise of one
-- service's credentials cannot expose the other's data.
--
-- Idempotent: safe to re-run. Run as a superuser (e.g. `postgres`),
-- AFTER `alembic upgrade head` has created the tables.
--
-- Usage:
--   psql -d campus_connect -f grants.sql

-- ---- Roles ----
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_core_api') THEN
    CREATE ROLE app_core_api LOGIN PASSWORD 'change_me_core_api';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_safety_service') THEN
    CREATE ROLE app_safety_service LOGIN PASSWORD 'change_me_safety_service';
  END IF;
  -- Narrower than app_safety_service: for the human-review workflow only
  -- (Section 10's "human escalation layer"). Gets SELECT + narrow UPDATE
  -- on safety_events, nothing else, and specifically cannot read
  -- flagged_text via this role's default grant below (kept out on
  -- purpose — reviewing the escalation_status/flag_level metadata does
  -- not require the raw text; expand only if a real reviewer workflow
  -- proves it's needed, per Section 11's data-minimization principle).
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_safety_reviewer') THEN
    CREATE ROLE app_safety_reviewer LOGIN PASSWORD 'change_me_safety_reviewer';
  END IF;
END
$$;

-- Dev-only passwords above — replace via secrets management before any
-- shared/staging/prod environment. Never commit real credentials.

-- ---- core_api: full access to its own tables, NOTHING on safety_events ----
GRANT SELECT, INSERT, UPDATE, DELETE ON
  users, profiles, checkins, tiny_actions, action_attempts,
  consent_records, privacy_settings, data_requests
TO app_core_api;

REVOKE ALL ON safety_events FROM app_core_api;

-- ---- safety_service: full access to safety_events ONLY ----
GRANT SELECT, INSERT, UPDATE ON safety_events TO app_safety_service;

REVOKE ALL ON
  users, profiles, checkins, tiny_actions, action_attempts,
  consent_records, privacy_settings, data_requests
FROM app_safety_service;

-- ---- safety_reviewer: metadata-only read + escalation-status update ----
GRANT SELECT (id, user_ref, flag_level, source, response_template_id,
              escalation_status, reviewer_ref, created_at, reviewed_at)
  ON safety_events TO app_safety_reviewer;
GRANT UPDATE (escalation_status, reviewer_ref, reviewed_at)
  ON safety_events TO app_safety_reviewer;
-- Deliberately no grant on the flagged_text column for this role.

REVOKE ALL ON
  users, profiles, checkins, tiny_actions, action_attempts,
  consent_records, privacy_settings, data_requests
FROM app_safety_reviewer;

-- ---- sequences: needed for INSERT to work when PKs default server-side ----
-- (Our PKs are client-generated UUIDs via SQLAlchemy defaults, so no
-- sequence grants are required today. If a future migration adds any
-- serial/identity column, its sequence will need an explicit GRANT here
-- too — Postgres does not do this automatically for non-owners.)
