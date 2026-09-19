# Phase 12 launch gate — anonymous rooms and moderation

The application code and reviewer workflow are in place, but Phase 12 is **not
launch-ready** until this runbook has been completed in a staging environment.
Do not substitute unit tests or a local mock for these checks.

## Required evidence

1. A moderator account is in `MODERATION_REVIEWER_EMAILS`, has a distinct
   `MODERATION_REVIEWER_TOKEN`, and can open `/community/review`. A normal
   signed-in account must receive a 404 for that route.
2. Use at least seven disposable new accounts and rooms for the default burst
   of 20 posts. New accounts are deliberately limited to three posts an hour,
   so one test account cannot demonstrate queue throughput.
3. Save the JSON subjects file outside version control:

   ```json
   [{"user_id":"...","room_id":"..."}]
   ```

4. Run the burst against **staging only**:

   ```bash
   python scripts/load_test_moderation_queue.py \
     --base-url https://staging-moderation.example \
     --internal-secret "$INTERNAL_SHARED_SECRET" \
     --reviewer-token "$MODERATION_REVIEWER_TOKEN" \
     --subjects-file /secure/path/phase-12-subjects.json \
     --requests 20 --workers 5
   ```

5. A pass has `held_for_review == submitted`, no failures, and queue growth at
   least equal to held posts. Save the command output with the staging release
   record. Then have a staffed, authorized reviewer approve and remove sample
   posts in `/community/review`, confirming approved posts become visible and
   removed ones remain hidden.

6. Record the reviewer roster, timezone coverage, escalation ownership, and
   response-time target. The technical queue is not a staffed-review plan by
   itself.

Until all six are recorded, keep anonymous rooms behind the launch gate and
describe Phase 12 as implemented but pending live verification.
