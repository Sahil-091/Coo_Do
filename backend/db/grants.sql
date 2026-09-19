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
    CREATE ROLE app_core_api LOGIN PASSWORD __APP_CORE_API_DB_PASSWORD__;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_safety_service') THEN
    CREATE ROLE app_safety_service LOGIN PASSWORD __APP_SAFETY_SERVICE_DB_PASSWORD__;
  END IF;
  -- Narrower than app_safety_service: for the human-review workflow only
  -- (Section 10's "human escalation layer"). Gets SELECT + narrow UPDATE
  -- on safety_events, nothing else, and specifically cannot read
  -- flagged_text via this role's default grant below (kept out on
  -- purpose — reviewing the escalation_status/flag_level metadata does
  -- not require the raw text; expand only if a real reviewer workflow
  -- proves it's needed, per Section 11's data-minimization principle).
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_safety_reviewer') THEN
    CREATE ROLE app_safety_reviewer LOGIN PASSWORD __APP_SAFETY_REVIEWER_DB_PASSWORD__;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_matching_service') THEN
    CREATE ROLE app_matching_service LOGIN PASSWORD __APP_MATCHING_SERVICE_DB_PASSWORD__;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_moderation_service') THEN
    CREATE ROLE app_moderation_service LOGIN PASSWORD __APP_MODERATION_SERVICE_DB_PASSWORD__;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_moderation_reviewer') THEN
    CREATE ROLE app_moderation_reviewer LOGIN PASSWORD __APP_MODERATION_REVIEWER_DB_PASSWORD__;
  END IF;
END
$$;

-- Also rotate the passwords of roles created by an earlier deployment. This
-- makes a secret rotation take effect when the migration/grants job reruns.
ALTER ROLE app_core_api PASSWORD __APP_CORE_API_DB_PASSWORD__;
ALTER ROLE app_safety_service PASSWORD __APP_SAFETY_SERVICE_DB_PASSWORD__;
ALTER ROLE app_safety_reviewer PASSWORD __APP_SAFETY_REVIEWER_DB_PASSWORD__;
ALTER ROLE app_matching_service PASSWORD __APP_MATCHING_SERVICE_DB_PASSWORD__;
ALTER ROLE app_moderation_service PASSWORD __APP_MODERATION_SERVICE_DB_PASSWORD__;
ALTER ROLE app_moderation_reviewer PASSWORD __APP_MODERATION_REVIEWER_DB_PASSWORD__;

-- Password literals are injected by apply_grants.py from environment-only
-- values. It uses the documented development defaults locally, but staging
-- and production must provide unique role passwords through secret storage.

-- ---- core_api: only the operations its routes actually use ----
-- Revoke first so re-running this file also removes an older broad grant.
REVOKE ALL ON
  users, profiles, checkins, tiny_actions, action_attempts, tiny_action_voice_events,
  consent_records, privacy_settings, data_requests, professional_resources, journal_entries, help_seeking_actions,
  activities, presence_rooms, activity_participants, activity_meetups, activity_rsvps, activity_alert_preferences, trusted_contacts, matches, match_blocks, match_reports
FROM app_core_api;

GRANT SELECT, INSERT, UPDATE ON
  users, profiles, consent_records, privacy_settings, professional_resources,
  activities, presence_rooms, activity_participants, activity_meetups, activity_rsvps, activity_alert_preferences, trusted_contacts
TO app_core_api;
GRANT DELETE ON trusted_contacts TO app_core_api;
-- Clearing a coarse-area opt-in deletes its only stored cell. Core-api never
-- receives DELETE on any unrelated user data as a consequence.
GRANT DELETE ON activity_alert_preferences TO app_core_api;
GRANT SELECT, INSERT ON checkins, action_attempts, tiny_action_voice_events, data_requests, help_seeking_actions
TO app_core_api;
GRANT SELECT ON tiny_actions TO app_core_api;
-- Journal deletion is deliberately the only Phase 8 DELETE privilege.
GRANT SELECT, INSERT, DELETE ON journal_entries TO app_core_api;

REVOKE ALL ON safety_events FROM app_core_api;

-- ---- safety_service: full access to safety_events ONLY ----
GRANT SELECT, INSERT, UPDATE ON safety_events TO app_safety_service;

REVOKE ALL ON
  users, profiles, checkins, tiny_actions, action_attempts, tiny_action_voice_events,
  consent_records, privacy_settings, data_requests, professional_resources, journal_entries, help_seeking_actions,
  activities, presence_rooms, activity_participants, activity_meetups, activity_rsvps, activity_alert_preferences, trusted_contacts, matches, match_blocks, match_reports
FROM app_safety_service;

-- ---- safety_reviewer: metadata-only read + escalation-status update ----
GRANT SELECT (id, user_ref, flag_level, source, response_template_id,
              classifier_model, classifier_prompt_version,
              escalation_status, reviewer_ref, created_at, reviewed_at)
  ON safety_events TO app_safety_reviewer;
GRANT UPDATE (escalation_status, reviewer_ref, reviewed_at)
  ON safety_events TO app_safety_reviewer;
-- Deliberately no grant on the flagged_text column for this role.

REVOKE ALL ON
  users, profiles, checkins, tiny_actions, action_attempts, tiny_action_voice_events,
  consent_records, privacy_settings, data_requests, professional_resources, journal_entries, help_seeking_actions,
  activities, presence_rooms, activity_participants, trusted_contacts, matches, match_blocks, match_reports
FROM app_safety_reviewer;

-- ---- matching_service: matching-owned state only ----
-- Profile data is deliberately fetched from core-api's narrow internal
-- candidate endpoint. This role has no direct SELECT grant on users/profiles.
REVOKE ALL ON users, profiles, checkins, tiny_actions, action_attempts,
  tiny_action_voice_events, consent_records, privacy_settings, data_requests,
  professional_resources, journal_entries, help_seeking_actions, activities, activity_meetups, activity_rsvps, activity_alert_preferences,
  presence_rooms, activity_participants, trusted_contacts, safety_events
FROM app_matching_service;
GRANT SELECT, INSERT, UPDATE ON matches, match_blocks, match_reports
TO app_matching_service;

-- ---- sequences: needed for INSERT to work when PKs default server-side ----
-- (Our PKs are client-generated UUIDs via SQLAlchemy defaults, so no
-- sequence grants are required today. If a future migration adds any
-- serial/identity column, its sequence will need an explicit GRANT here
-- too — Postgres does not do this automatically for non-owners.)

-- ---- moderation_service: anonymous-room data only ----
REVOKE ALL ON users, profiles, checkins, tiny_actions, action_attempts,
  tiny_action_voice_events, consent_records, privacy_settings, data_requests,
  professional_resources, journal_entries, help_seeking_actions, activities, activity_meetups, activity_rsvps, activity_alert_preferences,
  presence_rooms, activity_participants, trusted_contacts, matches, match_blocks,
  match_reports, safety_events
FROM app_moderation_service;
GRANT SELECT, INSERT, UPDATE ON community_rooms, community_guidelines_acceptances,
  community_posts, community_reports, moderation_events
TO app_moderation_service;

-- A reviewer has a distinct credential and database role. It can inspect the
-- held post and its queue metadata, then only change a queue outcome/post status.
REVOKE ALL ON users, profiles, checkins, tiny_actions, action_attempts,
  tiny_action_voice_events, consent_records, privacy_settings, data_requests,
  professional_resources, journal_entries, help_seeking_actions, activities, activity_meetups, activity_rsvps, activity_alert_preferences,
  presence_rooms, activity_participants, trusted_contacts, matches, match_blocks,
  match_reports, safety_events, community_rooms, community_guidelines_acceptances,
  community_reports
FROM app_moderation_reviewer;
GRANT SELECT ON community_posts, moderation_events TO app_moderation_reviewer;
GRANT UPDATE (status) ON community_posts TO app_moderation_reviewer;
GRANT UPDATE (review_status, reviewer_ref, reviewed_at) ON moderation_events TO app_moderation_reviewer;
